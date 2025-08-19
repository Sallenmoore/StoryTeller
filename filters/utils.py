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

# display the appropriate lifetime calue based on object type
def dsp_lifetime(obj_type,d='start'):
  lifetime = {}

  if obj_type in ['Character', 'Creature']:
    lifetime['start'] = 'Born'
    lifetime['stop'] = 'Died'
  elif obj_type in ['Item', 'Vehicle']:
    lifetime['start'] = 'Created'
    lifetime['stop'] = 'Destroyed'
  elif obj_type in ['Faction']:
    lifetime['start'] = 'Assembled'
    lifetime['stop'] = 'Disbanded'
  else:
    lifetime['start'] = 'Began'
    lifetime['stop'] = 'Ended'

  return  lifetime[d]