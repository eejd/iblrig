#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Niccolò Bonacchi
# @Date:   2018-02-02 12:31:13
from pybpodapi.protocol import Bpod, StateMachine
import logging

from session_params import SessionParamHandler
import task_settings
import user_settings

log = logging.getLogger('iblrig')
log.setLevel(logging.INFO)

global sph
sph = SessionParamHandler(task_settings, user_settings)


# =============================================================================
# CONNECT TO BPOD
# =============================================================================
bpod = Bpod()
log.info('Listening...')
# =============================================================================
#     Start state machine definition
# =============================================================================
sma = StateMachine(bpod)

sma.add_state(
    state_name='trial_start',
    state_timer=0,
    state_change_conditions={'Tup': 'listen'},
    output_actions=[])

sma.add_state(
    state_name='listen',
    state_change_conditions={},
    output_actions=[])

# Send state machine description to Bpod device
bpod.send_state_machine(sma)
# Run state machine
bpod.run_state_machine(sma)  # Locks until state machine 'exit' is reached

data = bpod.session.current_trial.export()
X
bpod.close()

if __name__ == '__main__':
    print('main')
