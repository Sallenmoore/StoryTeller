import random
import re

import markdown
from autonomous.model.autoattr import IntAttr, ListAttr, ReferenceAttr, StringAttr

from autonomous import log
from models.base.place import Place
from models.ttrpgobject.ability import Ability


class Vehicle(Place):
    size = StringAttr(
        default="medium", choices=["tiny", "small", "medium", "large", "huge"]
    )
    type = StringAttr(
        default="ground vehicle",
        choices=["ground vehicle", "aircraft", "watercraft", "spacecraft"],
    )
    make = StringAttr(default="")
    speed = StringAttr(default="50 feet per round")
    hitpoints = IntAttr(default=lambda: random.randint(10, 250))
    armor = IntAttr(default=lambda: random.randint(1, 20))
    ac = IntAttr(default=lambda: random.randint(1, 20))
    abilities = ListAttr(ReferenceAttr(choices=["Ability"]))
    capacity = IntAttr(default=1)

    start_date_label = "Built"
    end_date_label = "Destroyed"

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
                "status": {
                    "type": "string",
                    "description": "current, immediate situation the vehicle is in, such as partially operational, damaged engine, marked as stolen, etc.",
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
                    "description": "The general category of vehicle. Must be one of the following: ground vehicle, aircraft, watercraft, spacecraft.",
                },
                "make": {
                    "type": "string",
                    "description": "The general type of vehicle, such as a car, truck, motorcycle, transport, assault, fighter, etc. This should be more specific than the type field.",
                },
                "size": {
                    "type": "string",
                    "description": "huge, large, medium, small, or tiny",
                },
                "hitpoints": {
                    "type": "integer",
                    "description": "The maximum number of hit points the vehicle has.",
                },
                "armor": {
                    "type": "integer",
                    "description": "The armor level of the vehicle. No Armor == 0, Highest Armor == 20.",
                },
                "speed": {
                    "type": "string",
                    "description": "The speed of the vehicle, typically measured in feet per round.",
                },
                "capacity": {
                    "type": "integer",
                    "description": "The maximum number of crew that can be aboard the vehicle.",
                },
                "sensory_details": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of sensory details, such as sight, sound, smell, and touch, that a GM can use to bring the vehicle to life",
                },
                "recent_events": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A concise list of significant events that have recently occurred in this vehicle, even if they aren't ongoing situations. Only include publicly known information.",
                },
                "abilities": {
                    "type": "array",
                    "description": "Generate at least 2 offensive combat, 2 defensive combat AND 2 roleplay special ability objects for the array. Each object in the array should have attributes for the ability name, type of action, detailed description in MARKDOWN, effects, duration, and the dice roll mechanics involved in using the ability.",
                    "items": {
                        "type": "object",
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
    def image_prompt(self):
        return f"""A full color image of a {self.genre} {self.make} {self.type} with the following description:
"- NAME: {self.name}
{"- DESCRIPTION: " + self.description if self.description else ""}
{"- SIZE: " + self.size if self.size else ""}
"""

    ################### CRUD Methods #####################
    def generate(self):
        prompt = f"""Create a {random.choice(["highly advanced", "dilapidated", "warclad", "commercial", "opulent"])} {self.genre} {self.type} that has a {random.choice(("unexpected", "mysterious", "sinister", "incredible"))} history.
        """
        return super().generate(prompt=prompt)

    ################### Instance Methods #####################

    ################### Serialization Methods #####################

    def page_data(self):
        if not self.history:
            self.resummarize()
        return {
            "pk": str(self.pk),
            "name": self.name,
            "desc": self.description,
            "image": str(self.image.url()) if self.image else "",
            "backstory": self.backstory,
            "history": self.history,
            "ac": self.ac,
            "armor": self.armor,
            "speed": self.speed,
            "type": self.type,
            "size": self.size,
            "hitpoints": self.hitpoints,
            "capacity": self.capacity,
        }

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################
    @classmethod
    def auto_post_init(cls, sender, document, **kwargs):
        # log("Auto Pre Save World")
        super().auto_post_init(sender, document, **kwargs)

        ############### MIGRATION ##################
        if document.type not in [
            "ground vehicle",
            "aircraft",
            "watercraft",
            "spacecraft",
        ]:
            document.make = document.type
            document.type = "ground vehicle"

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
        for idx, ability in enumerate(self.abilities):
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
