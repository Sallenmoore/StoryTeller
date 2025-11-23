import random

import markdown
from autonomous.model.autoattr import BoolAttr, IntAttr, StringAttr

from autonomous import log
from models.base.actor import Actor
from models.ttrpgobject.ability import Ability


class Creature(Actor):
    type = StringAttr(default="")
    size = StringAttr(
        default="medium", choices=["tiny", "small", "medium", "large", "huge"]
    )
    legendary = BoolAttr(default=False)

    start_date_label = "Born"
    end_date_label = "Died"

    parent_list = ["Location", "District", "Vehicle", "Faction", "City"]
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
            },
        },
    }

    ################### Property Methods #####################

    @property
    def image_tags(self):
        return super().image_tags + [self.type, self.size]

    @property
    def image_prompt(self):
        return f"""A full-length color portrait of a {self.genre} {self.type or "creature"} with the following description:
        {("- TYPE: " if not self.legendary else "- NAME: ") + self.name}
        {"- DESCRIPTION: " + self.description if self.description else ""}
        {"- SIZE: " + self.size if self.size else ""}
        """

    @property
    def unique(self):
        return self.legendary

    ################### CRUD Methods #####################
    def generate(self):
        if self.legendary:
            prompt = f"""Generate detailed data for a unique named {self.type or "creature"} suitable for a {self.genre} TTRPG. Focus on their individual characteristics, abilities, backstory, and general disposition, suitable for a group of adventurers to encounter.
        """
        else:
            prompt = f"""Generate detailed data for a common {self.type or "creature"} type suitable for a {self.genre} TTRPG. Focus on their typical characteristics, abilities, and general disposition, suitable for a group of adventurers to encounter. Do not generate a unique named character or individual. This is a classification of creature, not a specific creature.
            """
        super().generate(prompt=prompt)

    ################### Instance Methods #####################

    def page_data(self):
        if not self.history:
            self.resummarize()
        return {
            "pk": str(self.pk),
            "image": str(self.image.url()) if self.image else None,
            "name": self.name,
            "desc": self.description,
            "backstory": self.backstory,
            "speed": self.speed,
            "speed_units": self.speed_units,
            "level": self.level,
            "history": self.history,
            "species": self.species,
            "goal": self.goal,
            "type": self.type,
            "size": self.size,
            "hitpoints": self.hitpoints,
            "ac": self.ac,
            "archetype": self.archetype,
            "skills": self.skills,
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
        document.pre_save_legendary()

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

    def pre_save_legendary(self):
        if isinstance(self.legendary, str):
            if self.legendary.lower() in ["true", "1", "yes"]:
                self.legendary = True
            else:
                self.legendary = False
