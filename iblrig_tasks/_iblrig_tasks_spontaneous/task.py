"""
The spontaneous protocol is used to record spontaneous activity in the mouse brain.
The task does nothing, only creates the architecture for the data streams to be recorded.
"""

import logging

from iblrig.base_tasks import SpontaneousSession
import iblrig.test

log = logging.getLogger("iblrig")


class Session(SpontaneousSession):
    protocol_name = "_iblrig_tasks_spontaneous"


if __name__ == "__main__":  # pragma: no cover
    # python .\iblrig_tasks\_iblrig_tasks_spontaneous\task.py --subject mysubject
    kwargs = iblrig.misc.get_task_runner_argument_parser()
    sess = Session(**kwargs)
    sess.run()