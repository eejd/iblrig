#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author: Niccolò Bonacchi; Eric DeWitt
# @Date: Friday, February 8th 2019, 11:39:30 am
import numpy as np

import iblrig.misc as misc


def get_block_len(factor, min_, max_):
    return int(misc.texp(factor=factor, min_=min_, max_=max_))


def update_block_params(tph):
    tph.reward_block_trial_num += 1
    if tph.reward_block_trial_num > tph.reward_block_len:
        tph.reward_block_num += 1
        tph.reward_block_trial_num = 1
        tph.reward_block_len = get_block_len(
            factor=tph.reward_block_len_factor, min_=tph.reward_block_len_min,
            max_=tph.reward_block_len_max)

    return tph


def update_reward_multiplier(tph):
    if tph.reward_block_trial_num != 1:
        return tph.reward_block_multiplier

    if tph.reward_block_num == 1 and tph.reward_block_init_1:
        return tph.reward_block_multiplier
    else:
        return tph.reward_block_multiplier_set[tph.contrast_set.index(tph.contrast)]


def init_block_len(tph):
    if tph.reward_block_init_5050:
        return 90
    else:
        return self.get_block_len(
            factor=tph.reward_block_len_factor, min_=tph.reward_block_len_min,
            max_=tph.reward_block_len_max)


def init_reward_amount(sph, tph):
    if tph.reward_block_init_1:
        return sph.REWARD_BLOCK_INIT_MULTIPLIER
    else:
        return tph.reward_block_multiplier_set[tph.contrast_set.index(tph.contrast)]


# this could be moved to a different function, depends on blocks?
def get_reward_amount_with_rpe(tph):
    alt_reward_multiplier_values = set(tph.reward_block_multiplier_set).difference(set(tph.reward_amount))
    if np.random.rand() < tph.reward_rpe_probability:
        return tph.reward_amount * np.random.choice(alt_reward_multiplier_values)
    else:
        return tph.reward_amount * tph.reward_block_multiplier

