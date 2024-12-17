import random

import markdown

from autonomous import log
from autonomous.model.autoattr import IntAttr, ListAttr, ReferenceAttr, StringAttr
from models.base.place import Place


class Vehicle(Place):
    type = StringAttr(default="")
    size = StringAttr(
        default="medium", choices=["tiny", "small", "medium", "large", "huge"]
    )
    hitpoints = IntAttr(default=lambda: random.randint(10 - 250))
    abilities = ListAttr(ReferenceAttr(choices=["Ability"]))
    group = IntAttr(default=False)

    parent_list = ["Location", "District", "City", "Region"]
    _funcobj = {
        "name": "generate_vehicle",
        "description": "completes Vehicle data object",
        "parameters": {
            "type": "object",
            "properties": {
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
                    "description": "The average number of vehicles of this kind that usually travel together, or 0 for a unique vehicle (i.e. BBEG)",
                },
            },
        },
    }

    ################### Property Methods #####################

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
            "goal": self.goal,
            "type": self.type,
            "size": self.size,
            "hit points": self.hitpoints,
            "abilities": self.abilities,
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
