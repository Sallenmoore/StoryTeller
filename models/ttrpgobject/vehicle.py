import random

import markdown

from autonomous import log
from autonomous.model.autoattr import IntAttr, ListAttr, ReferenceAttr, StringAttr
from models.base.place import Place
from models.ttrpgobject.ability import Ability


class Vehicle(Place):
    type = StringAttr(default="")
    size = StringAttr(
        default="medium", choices=["tiny", "small", "medium", "large", "huge"]
    )
    hitpoints = IntAttr(default=lambda: random.randint(10, 250))
    abilities = ListAttr(ReferenceAttr(choices=["Ability"]))
    group = IntAttr(default=False)

    parent_list = ["Location", "District", "City", "Region"]
    _funcobj = {
        "name": "generate_vehicle",
        "description": "completes Vehicle data object",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "An intriguing, suggestive, and unique name",
                },
                "backstory": {
                    "type": "string",
                    "description": "A description of the history of the vehicle. Only include what would be publicly known information.",
                },
                "desc": {
                    "type": "string",
                    "description": "A short physical description that will be used to generate an evocative image of the vehicle",
                },
                "type": {
                    "type": "string",
                    "description": "The general category of vehicle, such as automobile, wagon, starship, etc.",
                },
                "size": {
                    "type": "string",
                    "description": "huge, large, medium, small, or tiny",
                },
                "group": {
                    "type": "integer",
                    "description": "The average number of vehicles of this kind that usually travel together, or 0 for a unique vehicle (i.e. BBEV)",
                },
                "abilities": {
                    "type": "array",
                    "description": "Generate at least 2 offensive combat, 2 defensive combat AND 2 roleplay special ability objects for the array. Each object in the array should have attributes for the ability name, type of action, detailed description in MARKDOWN, effects, duration, and the dice roll mechanics involved in using the ability.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "name",
                            "action",
                            "description",
                            "effects",
                            "duration",
                            "dice_roll",
                        ],
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
                                "description": "Detailed description of the ability and how the Vehicle implements the ability in MARKDOWN.",
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
                },
            },
        },
    }

    ################### Property Methods #####################
    @property
    def crew(self):
        return [
            c for c in self.associations if c.model_name() in ["Character", "Creature"]
        ]

    @property
    def image_tags(self):
        return super().image_tags + [self.type, self.size]

    @property
    def history_prompt(self):
        return f"""
BACKSTORY
---
{self.backstory_summary}

{"EVENTS INVOLVING THIS VEHICLE TYPE" if not self.group else "TIMELINE OF EVENTS"}
---
"""

    @property
    def image_prompt(self):
        return f"""A full color image of a {self.genre} {self.type or 'vehicle'} with the following description:
{("- TYPE: " if self.group else "- NAME: ") + self.name}
{"- DESCRIPTION: " + self.description if self.description else ""}
{"- SIZE: " + self.size if self.size else ""}
"""

    @property
    def unique(self):
        return bool(self.group)

    ################### CRUD Methods #####################
    def generate(self):
        group = "type of vehicle that" if self.group else "unique vehicle whose owner "
        prompt = f"""Create a {random.choice(['highly advanced', 'dilapidated', 'warclad', 'commercial', 'opulent'])} {self.genre} {self.type} {group} has a {random.choice(('unexpected', 'mysterious', 'sinister', 'incredible'))} history.
        """
        return super().generate(prompt=prompt)

    ################### Instance Methods #####################

    def page_data(self):
        return {
            "pk": str(self.pk),
            "name": self.name,
            "desc": self.description,
            "backstory": self.backstory,
            "history": self.history,
            "type": self.type,
            "size": self.size,
            "hit points": self.hitpoints,
            "abilities": [str(a) for a in self.abilities],
            "group": self.group,
            "crew": [c.path for c in self.crew],
        }

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_size()
        document.pre_save_ability()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################
    def pre_save_size(self):
        if isinstance(self.size, str) and self.size.lower() in [
            "tiny",
            "small",
            "medium",
            "large",
            "huge",
        ]:
            self.size = self.size.lower()
        else:
            log(f"Invalid size for vehicle: {self.size}", _print=True)
            self.size = "medium"

    def pre_save_ability(self):
        log(self.abilities, _print=True)
        for idx, ability in enumerate(self.abilities):
            log(ability)
            if isinstance(ability, str):
                a = Ability(description=ability)
                a.save()
                self.abilities[idx] = a
            elif isinstance(ability, dict):
                a = Ability(**ability)
                a.save()
                self.abilities[idx] = a
            else:
                ability.description = (
                    markdown.markdown(ability.description.replace("```markdown", ""))
                    .replace("h1>", "h3>")
                    .replace("h2>", "h3>")
                )

        self.abilities = [a for a in self.abilities if a.name]

        log(self.abilities, _print=True)
