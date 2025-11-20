import random

from autonomous.model.autoattr import StringAttr
from autonomous.model.automodel import AutoModel

from autonomous import log


class Ability(AutoModel):
    name = StringAttr(default="")
    description = StringAttr(default="")
    action = StringAttr(
        choices=["main action", "bonus action", "reaction", "free action", "passive"]
    )
    effects = StringAttr(default="")
    duration = StringAttr(default="")
    dice_roll = StringAttr(default="")

    _funcobj = {
        "name": "generate_ability",
        "description": "Generates a new Ability for a TTRPG Character.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Unique name for the Ability.",
                },
                "action": {
                    "type": "string",
                    "enum": [
                        "main action",
                        "bonus action",
                        "reaction",
                        "free action",
                        "passive",
                    ],
                    "description": "type of action required.",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the ability and how the Character aquired the ability in MARKDOWN.",
                },
                "effects": {
                    "type": "string",
                    "description": "Description of the ability's effects.",
                },
                "duration": {
                    "type": "string",
                    "description": "The duration of the ability's effects.",
                },
                "dice_roll": {
                    "type": "string",
                    "description": "The dice roll mechanics for determining the success or failure of the ability.",
                },
            },
        },
    }

    def __str__(self):
        return f"{self.name} [{self.action}]: {self.description}; EFFECTS: {self.effects}; DURATION: {self.duration}; DICE ROLL: {self.dice_roll}"
