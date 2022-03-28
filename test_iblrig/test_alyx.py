import unittest
import subprocess
import shutil

from pathlib import Path
import iblrig.ibllib_calls as calls


class TestIbllibCalls(unittest.TestCase):
    def setUp(self):
        self.project_name = "ibl_mainenlab"
        self.one_test = True

    def test_call_one_get_project_data(self):
        calls.call_one_get_project_data(self.project_name, one_test=self.one_test)
        self.assertTrue(Path().home().joinpath("TempAlyxProjectData").exists())
        self.assertTrue(Path().home().joinpath("TempAlyxProjectData", f"{self.project_name}_subjects.json").exists())

    def test_call_one_sync_params(self):
        resp = calls.call_one_sync_params(one_test=self.one_test)
        self.assertTrue(isinstance(resp, subprocess.CompletedProcess))
        self.assertTrue(resp.returncode == 0)

    def tearDown(self):
        shutil.rmtree(calls.ROOT_FOLDER, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(exit=False)
