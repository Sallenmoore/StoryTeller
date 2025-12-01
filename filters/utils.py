import random

from dmtoolkit import dmtools
from flask import get_template_attribute

from autonomous import log


def get_icon(obj, size="2rem"):
    try:
        icon_func = obj.title if hasattr(obj, "title") else obj.model_name()
        icon_func = icon_func.lower().replace(" ", "").replace("-", "")
        return get_template_attribute("shared/_icons.html", icon_func)(size)
    except Exception as e:
        log(e, obj, "No icon found for object")
    return get_template_attribute("shared/_icons.html", "default")(size)


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
