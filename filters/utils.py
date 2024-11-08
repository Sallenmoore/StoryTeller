import random

from dmtoolkit import dmtools

from autonomous import log

def roll_dice(roll_str):
    result = dmtools.dice_roll(roll_str)
    if isinstance(result, list):
        return sum(result)
    return result


def filter_shuffle(seq, max=0):
    max = int(max)
    try:
        result = list(seq)
        random.shuffle(result)
        return result[:max] if max > 0 else result
    except Exception as e:
        log(e)
        return seq
