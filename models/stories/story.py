import random

from autonomous import log
from autonomous.model.autoattr import DictAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.base.ttrpgbase import TTRPGBase


class Story(AutoModel):
    name = StringAttr(default="")
    type = StringAttr(default="Local", choices=["Local", "Global", "Epic"])
    situation = StringAttr(default="")
    current_status = StringAttr(default="")
    backstory = StringAttr(default="")
    tasks = ListAttr(StringAttr(default=""))
    rumors = ListAttr(StringAttr(default=""))
    information = ListAttr(StringAttr(default=""))
    bbeg = ReferenceAttr(choices=["Character"])
    encounters = ListAttr(ReferenceAttr(choices=["Encounter"]))
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    episodes = ListAttr(ReferenceAttr(choices=["Episode"]))

    def __str__(self):
        return f"{self.situation}"

    funcobj = {
        "name": "generate_story",
        "description": "creates a compelling narrative consistent with the described world for the players to engage with, explore, and advance in creative and unexpected ways.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A name for the storyline.",
                },
                "situation": {
                    "type": "string",
                    "description": "A description of the overall situation and its effects on the TTRPG world. This should be a specific, concrete situation that the players can engage with and explore.",
                },
                "current_status": {
                    "type": "string",
                    "description": "A detailed description of the current status of the situation, including things unknown to the player characters.",
                },
                "backstory": {
                    "type": "string",
                    "description": "A detailed description of the backstory leading up to the current situation.",
                },
                "tasks": {
                    "type": "array",
                    "description": "A list of tasks that the player characters must complete to advance the story. These tasks should be relevant to the situation and provide a scenario for the player characters to engage with the story.",
                    "items": {"type": "string"},
                },
                "rumors": {
                    "type": "array",
                    "description": "A list of rumors that will draw the players in and help the player characters learn about the situation, in the order they should be revealed. Rumors are not always true, but they should be relevant to the situation and provide useful information to the player characters.",
                    "items": {"type": "string"},
                },
                "information": {
                    "type": "array",
                    "description": " A list of information that the player characters can discover about the situation, in the order they should be revealed. This information should be relevant to the situation and provide useful context for the player characters.",
                    "items": {"type": "string"},
                },
            },
        },
    }
