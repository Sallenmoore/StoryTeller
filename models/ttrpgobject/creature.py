import random

import markdown

from autonomous import log
from autonomous.model.autoattr import BoolAttr, ListAttr, StringAttr
from models.base.actor import Actor


class Creature(Actor):
    type = StringAttr(default="")
    size = StringAttr(
        default="medium", choices=["tiny", "small", "medium", "large", "huge"]
    )
    abilities = ListAttr(StringAttr())
    bbeg = BoolAttr(default=False)

    parent_list = ["Location", "District"]
    _funcobj = {
        "name": "generate_creature",
        "description": "completes Creature data object",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A descriptive, unique, and evocative name",
                },
                "type": {
                    "type": "string",
                    "description": "The general category of creature, such as humanoid, monster, alien, etc.",
                },
                "traits": {
                    "type": "string",
                    "description": "A description of the creature's motivation in less than 10 words",
                },
                "size": {
                    "type": "string",
                    "description": "huge, large, medium, small, or tiny",
                },
                "desc": {
                    "type": "string",
                    "description": "A detailed enough physical description to generate an AI image of this type of creature",
                },
                "backstory": {
                    "type": "string",
                    "description": "A detailed history of the creature type that includes only publicly known information about the creature.",
                },
                "goal": {
                    "type": "string",
                    "description": "This kind of creature's usual goals and secrets",
                },
                "hitpoints": {
                    "type": "integer",
                    "description": "Creature's maximum hit points",
                },
                "abilities": {
                    "type": "array",
                    "description": "Detailed descriptions in MARKDOWN starting at heading level 3 of at least 5 of this type of creature's combat and special abilities. Include the name of the ability, a brief description of what it does, and the dice roll mechanics to use the ability.",
                    "items": {"type": "string"},
                },
                "strength": {
                    "type": "integer",
                    "description": "The amount of Strength the creature has from 1-20",
                },
                "dexterity": {
                    "type": "integer",
                    "description": "The amount of Dexterity the creature has from 1-20",
                },
                "constitution": {
                    "type": "integer",
                    "description": "The amount of Constitution the creature has from 1-20",
                },
                "intelligence": {
                    "type": "integer",
                    "description": "The amount of Intelligence the creature has from 1-20",
                },
                "wisdom": {
                    "type": "integer",
                    "description": "The amount of Wisdom the creature has from 1-20",
                },
                "charisma": {
                    "type": "integer",
                    "description": "The amount of Charisma the creature has from 1-20",
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

{"EVENTS INVOLVING THIS CREATURE TYPE" if not self.bbeg else "LIFE EVENTS"}
---
"""

    @property
    def image_prompt(self):
        return f"""A full-length color portrait of a {self.genre} {self.type or 'creature'} with the following description:
        {("- TYPE: " if self.group else "- NAME: ") + self.name}
        {"- DESCRIPTION: " + self.description if self.description else ""}
        {"- SIZE: " + self.size if self.size else ""}
        {"- GOAL: " + self.goal if self.goal else ""}
        """

    @property
    def unique(self):
        return bool(self.bbeg)

    ################### CRUD Methods #####################
    def generate(self):
        group = "type of enemy whose species" if self.bbeg else "foe who"
        prompt = f"""Create a {random.choice(['dangerous', 'evil', 'misunderstood', 'manipulative', 'mindless'])} {self.genre} {self.type} {group} has a {random.choice(('boring', 'mysterious', 'sinister', 'complicated'))} goal they are working toward.
        """
        obj = super().generate(prompt=prompt)
        if isinstance(self.abilities[0], str):
            self.abilities = [markdown.markdown(a) for a in self.abilities]
        elif isinstance(self.abilities[0], dict):
            self.abilities = [
                markdown.markdown("<br>".join(a.items())) for a in self.abilities
            ]
        self.save()
        return obj

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
            "attributes": {
                "strength": self.strength,
                "dexerity": self.dexterity,
                "constitution": self.constitution,
                "wisdom": self.wisdom,
                "intelligence": self.intelligence,
                "charisma": self.charisma,
            },
            "abilities": self.abilities,
            "items": [{"name": r.name, "pk": str(r.pk)} for r in self.items],
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
            log(f"Invalid size for creature: {self.size}", _print=True)
            self.size = "medium"
