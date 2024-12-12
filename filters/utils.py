import random

from dmtoolkit import dmtools

from autonomous import log


def roll_dice(roll_str):
    result = dmtools.dice_roll(roll_str)
    if isinstance(result, list):
        return sum(result)
    return result


def bonus(value):
    if value:
        idx = value.find("+")
        if idx == -1:
            idx = value.find("-")
        if idx != -1:
            return value[idx:]
    return "+0"
