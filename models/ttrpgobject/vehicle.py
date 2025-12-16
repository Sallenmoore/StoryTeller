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
    category = StringAttr(
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
    dungeon = ReferenceAttr(choices=["Dungeon"])

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
                "category": {
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
        return super().image_tags + [self.category, self.size]

    @property
    def image_prompt(self):
        return f"""A full color image of a {self.genre} {self.make} {self.category} with the following description:
"- NAME: {self.name}
{"- DESCRIPTION: " + self.description if self.description else ""}
{"- SIZE: " + self.size if self.size else ""}
"""

    ################### CRUD Methods #####################
    def generate(self):
        prompt = f"""
{f"CATEGORY: {self.category}" if self.category else ""}
{f"MAKE: {self.make}" if self.make else ""}
{f"SIZE: {self.size}" if self.size else ""}
{f"SPEED: {self.speed}" if self.speed else ""}
{f"CREW CAPACITY: {self.capacity}" if self.capacity else ""}
{f"HITPOINTS: {self.hitpoints}" if self.hitpoints else ""}
{f"ARMOR: {self.armor}" if self.armor else ""}
{f"AC: {self.ac}" if self.ac else ""}
{f"ABILITIES: {self.abilities}" if self.abilities else ""}
"""
        super().generate(prompt=prompt)

        if not self.abilities:
            for _ in range(random.randint(1, 6)):
                ability = Ability(world=self.world)
                ability.save()
                self.abilities.append(ability)
                self.save()
                ability.generate(self)

    ################### Instance Methods #####################

    ################### Serialization Methods #####################

    def page_data(self):
        if not self.history:
            self.generate_history()
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
            "category": self.category,
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
        if document.category not in [
            "ground vehicle",
            "aircraft",
            "watercraft",
            "spacecraft",
        ]:
            document.make = document.category
            document.category = "ground vehicle"

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_size()
        # document.pre_save_ability()

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

    # def pre_save_ability(self):
    #     for idx, ability in enumerate(self.abilities):
    #         if isinstance(ability, str):
    #             a = Ability(description=ability)
    #             a.save()
    #             self.abilities[idx] = a
    #         elif isinstance(ability, dict):
    #             a = Ability(**ability)
    #             a.save()
    #             self.abilities[idx] = a
    #         else:
    #             ability.description = (
    #                 markdown.markdown(ability.description.replace("```markdown", ""))
    #                 .replace("h1>", "h3>")
    #                 .replace("h2>", "h3>")
    #             )

    #     self.abilities = [a for a in self.abilities if a.name]
