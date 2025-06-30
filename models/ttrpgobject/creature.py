import random

import markdown

from autonomous import log
from autonomous.model.autoattr import IntAttr, ListAttr, StringAttr
from models.base.actor import Actor


class Creature(Actor):
    type = StringAttr(default="")
    size = StringAttr(
        default="medium", choices=["tiny", "small", "medium", "large", "huge"]
    )
    group = IntAttr(default=False)

    parent_list = ["Location", "District", "Vehicle"]
    _funcobj = {
        "name": "generate_creature",
        "description": "completes Creature data object",
        "parameters": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "The general category of creature, such as humanoid, monster, alien, etc.",
                },
                "size": {
                    "type": "string",
                    "description": "huge, large, medium, small, or tiny",
                },
                "group": {
                    "type": "integer",
                    "description": "The average number of creatures of this kind that usually stay together, or 0 for a unique creature (i.e. BBEG)",
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
{self.backstory}

---
"""

    @property
    def image_prompt(self):
        return f"""A full-length color portrait of a {self.genre} {self.type or "creature"} with the following description:
        {("- TYPE: " if self.group else "- NAME: ") + self.name}
        {"- DESCRIPTION: " + self.description if self.description else ""}
        {"- SIZE: " + self.size if self.size else ""}
        """

    @property
    def unique(self):
        return bool(self.group)

    ################### CRUD Methods #####################
    def generate(self):
        prompt = f"""Create a {random.choice(["dangerous", "evil", "misunderstood", "manipulative", "mindless"])} {self.genre} {self.type} antagonist type with a {random.choice(("unexpected", "mysterious", "sinister", "selfish"))} goal they are working toward.
        """
        return super().generate(prompt=prompt)

    ################### Instance Methods #####################

    def page_data(self):
        return {
            "pk": str(self.pk),
            "image_pk": str(self.image.pk) if self.image else None,
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
            "abilities": [str(a) for a in self.abilities],
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
