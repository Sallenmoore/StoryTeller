import random

from autonomous import log
from autonomous.model.autoattr import StringAttr
from autonomous.model.automodel import AutoModel


class Ability(AutoModel):
    name = StringAttr(default="")
    description = StringAttr(default="")
    action = StringAttr(
        choices=["main action", "bonus action", "reaction", "free action", "passive"]
    )
    effects = StringAttr(default="")
    duration = StringAttr(default="")
    dice_roll = StringAttr(default="")

    def __str__(self):
        return f"{self.name} [{self.action}]: {self.description}; EFFECTS: {self.effects}; DURATION: {self.duration}; DICE ROLL: {self.dice_roll}"
