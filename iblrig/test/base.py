import copy
import datetime
import inspect
import json
import logging
import random
import string
import tempfile
import unittest
from pathlib import Path

import ibllib.pipes.dynamic_pipeline
import iblrig
from ibllib.io.extractors.base import protocol2extractor
from ibllib.tests import TEST_DB  # noqa
from one.api import ONE

PATH_FIXTURES = Path(__file__).parent.joinpath('fixtures')

TASK_KWARGS = {
    'file_iblrig_settings': 'iblrig_settings_template.yaml',
    'file_hardware_settings': 'hardware_settings_template.yaml',
    'subject': 'iblrig_test_subject',
    'subject_weight_grams': 42,
    'interactive': False,
    'projects': ['ibl_neuropixel_brainwide_01', 'ibl_mainenlab'],
    'procedures': ['Behavior training/tasks', 'Imaging'],
    'hardware_settings': dict(RIG_NAME='_iblrig_cortexlab_behavior_3', MAIN_SYNC=True),
    'iblrig_settings': dict(ALYX_LAB='cortexlab'),
}


class TaskArgsMixin:
    task_kwargs = {}
    _tmp = None

    @staticmethod
    def create_task_kwargs(tmpdir=True):
        """
        Copy task keyword arguments and create a temporary directory.

        Parameters
        ----------
        tmpdir : bool, tempfile.TemporaryDirectory, pathlib.Path
            An optional temporary directory to add to kwargs as iblrig settings local data path.
            If False, the default location is used. If True, a new tempdir is created and added to
            teardown routine.

        """
        task_kwargs = copy.deepcopy(TASK_KWARGS)
        if tmpdir is True:
            tmpdir = tempfile.TemporaryDirectory()
        if tmpdir:
            p = Path(tmpdir.name if isinstance(tmpdir, tempfile.TemporaryDirectory) else tmpdir)
            task_kwargs['iblrig_settings'].update(iblrig_remote_data_path=None, iblrig_local_data_path=p)
        return task_kwargs, tmpdir

    def get_task_kwargs(self, tmpdir=True):
        """
        Copy task keyword arguments and create a temporary directory.

        Parameters
        ----------
        tmpdir : bool, tempfile.TemporaryDirectory, pathlib.Path
            An optional temporary directory to add to kwargs as iblrig settings local data path.
            If False, the default location is used. If True, a new tempdir is created and added to
            teardown routine.

        """
        self.task_kwargs, tmp = self.create_task_kwargs(tmpdir)
        if tmp:
            self.tmp = Path(tmp.name if isinstance(tmp, tempfile.TemporaryDirectory) else tmp)
            if isinstance(tmp, tempfile.TemporaryDirectory):
                self.addCleanup(tmp.cleanup)
        self.addCleanup(self.cleanup_handlers)

    @staticmethod
    def cleanup_handlers():
        """Close log file handlers before cleaning up temp dir.

        The tasks open log files within the temp session dir. Here we ensure files are closed
        before removing file tree.
        """
        for name in ('iblrig', 'pybpodapi'):
            for fh in filter(lambda h: h.name == f'{name}_file', logging.getLogger(name).handlers):
                fh.close()
                logging.getLogger(name).removeHandler(fh)


class BaseTestCases:
    """
    We wrap the base class in a blank class to avoid it being called or discovered by unittest
    """

    class CommonTestTask(unittest.TestCase, TaskArgsMixin):
        task = None

        def read_and_assert_json_settings(self, json_file):
            with open(json_file) as fp:
                settings = json.load(fp)
            # test a subset of keys useful for extraction
            self.assertIn('ALYX_USER', settings)
            self.assertEqual(settings['IBLRIG_VERSION'], iblrig.__version__)
            self.assertIn('PYBPOD_PROTOCOL', settings)
            self.assertIn('RIG_NAME', settings)
            self.assertIn('SESSION_END_TIME', settings)
            self.assertIn('SESSION_NUMBER', settings)
            dt = datetime.datetime.now() - datetime.datetime.fromisoformat(settings['SESSION_START_TIME'])
            self.assertLess(dt.seconds, 600)  # leaves some time for debugging
            self.assertIn('SUBJECT_WEIGHT', settings)
            return settings

    class CommonTestInstantiateTask(CommonTestTask):
        def test_json_settings(self):
            json_file = self.task.save_task_parameters_to_json_file()
            self.read_and_assert_json_settings(json_file)

        def test_graphviz(self) -> None:
            if hasattr(self.task, 'get_graphviz_task'):
                self.task.mock()
                pdf_out = Path(inspect.getfile(self.task.__class__)).parent.joinpath('state_machine_graph')
                self.task.get_graphviz_task(output_file=pdf_out, view=False)

        def test_acquisition_description(self) -> None:
            # This makes sure that the task has a defined set of extractors
            description_task = self.task.experiment_description['tasks'][0][self.task.protocol_name]
            # there are 2 ways to define extractors, either in the `extractor_tasks` property, in which
            # case this is hard-coded in the task parameters, or at extraction runtime using ibllib.io.extractors.base
            # here we check that either of these methods is used and yields a valid extractor
            if self.task.extractor_tasks is not None:
                self.assertEqual(description_task['extractors'], self.task.extractor_tasks)
            else:
                protocol2extractor(self.task.protocol_name)

        def test_pipeline(self) -> None:
            self.task.create_session()
            ibllib.pipes.dynamic_pipeline.make_pipeline(self.task.paths.SESSION_FOLDER)


class IntegrationFullRuns(BaseTestCases.CommonTestTask):
    """
    This provides a base class that creates a subject on the test database for testing
    the full registration / run / register results cycle
    """

    create_subject = True
    _tmp = None  # a temporary directory
    one = None

    @classmethod
    def setUpClass(cls) -> None:
        """
        Instantiates ONE test, creates a random subject to be deleted once all of the operations
        have completed
        :return:
        """
        cls.one = ONE(**TEST_DB, mode='remote')
        cls.task_kwargs, cls._tmp = TaskArgsMixin.create_task_kwargs()
        cls.task_kwargs.update({'subject': 'iblrig_unit_test_' + ''.join(random.choices(string.ascii_letters, k=8))})
        if cls.create_subject:
            cls.one.alyx.rest('subjects', 'create', data=dict(nickname=cls.task_kwargs['subject'], lab='cortexlab'))

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.create_subject and cls.one:
            cls.one.alyx.rest('subjects', 'delete', id=cls.task_kwargs['subject'])
        cls.cleanup_handlers()
        if cls._tmp:
            cls._tmp.cleanup()
