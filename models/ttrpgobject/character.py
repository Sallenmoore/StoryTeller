import random

import markdown

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    BoolAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from models.base.actor import Actor


class Character(Actor):
    dnd_beyond_id = StringAttr(default="")
    is_player = BoolAttr(default=False)
    age = IntAttr(default=0)
    gender = StringAttr(default="")
    occupation = StringAttr(default="")
    abilities = ListAttr(StringAttr(default=""))
    race = StringAttr(default="")
    wealth = ListAttr(StringAttr(default=""))
    autogm_summary = ListAttr(ReferenceAttr(choices=["AutoGMScene"]))

    parent_list = ["City", "Location", "District", "Faction"]
    _genders = ["male", "female", "non-binary"]
    _traits_list = [
        "secretly evil",
        "shy and gentle",
        "outgoing and imaginative",
        "unfriendly, but not unkind",
        "cruel and sadistic",
        "power-hungry and ambitious",
        "kind and helpful",
        "proud and self-absorbed",
        "silly, a prankster",
        "overly serious",
        "incredibly greedy",
        "extremely generous",
        "hardworking",
        "cowardly and insecure",
        "practical to a fault",
        "dangerously curious",
        "cautious and occasionally paranoid",
        "reckless, but heroic",
    ]
    _funcobj = {
        "name": "generate_npc",
        "description": "creates, completes, and expands on the attributes and story of an existing NPC",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A unique and unusual first, middle, and last name",
                },
                "gender": {
                    "type": "string",
                    "description": "The NPC's preferred gender",
                },
                "age": {
                    "type": "integer",
                    "description": "The NPC's physical age in years",
                },
                "race": {
                    "type": "string",
                    "description": "The NPC's species",
                },
                "traits": {
                    "type": "string",
                    "description": "A description of the NPC's personality in less than 10 words",
                },
                "desc": {
                    "type": "string",
                    "description": "A detailed enough physical description to generate an AI image of the NPC",
                },
                "backstory": {
                    "type": "string",
                    "description": "The NPC's detailed backstory that includes only publicly known information about the NPC",
                },
                "goal": {
                    "type": "string",
                    "description": "The NPC's goals and closely guarded secrets",
                },
                "abilities": {
                    "type": "array",
                    "description": "Detailed descriptions in MARKDOWN starting at heading level 3 of at least 3 combat abilities and 3 special abilities of the character. Include the name of the ability, a brief description of what it does, and the dice roll mechanics involved in using the ability.",
                    "items": {"type": "string"},
                },
                "occupation": {
                    "type": "string",
                    "description": "The NPC's profession or daily occupation",
                },
                "hitpoints": {
                    "type": "integer",
                    "description": "NPC's maximum hit points",
                },
                "strength": {
                    "type": "integer",
                    "description": "The amount of Strength the NPC has from 1-20",
                },
                "dexterity": {
                    "type": "integer",
                    "description": "The amount of Dexterity the NPC has from 1-20",
                },
                "constitution": {
                    "type": "integer",
                    "description": "The amount of Constitution the NPC has from 1-20",
                },
                "intelligence": {
                    "type": "integer",
                    "description": "The amount of Intelligence the NPC has from 1-20",
                },
                "wisdom": {
                    "type": "integer",
                    "description": "The amount of Wisdom the NPC has from 1-20",
                },
                "charisma": {
                    "type": "integer",
                    "description": "The amount of Charisma the NPC has from 1-20",
                },
            },
        },
    }

    ################# Instance Properities #################

    @property
    def child_key(self):
        return "players" if self.is_player else "characters"

    @property
    def gm(self):
        return self.world.gm

    @property
    def history_primer(self):
        return "Incorporate the below LIFE EVENTS into the BACKSTORY to generate a chronological summary of the character's history in MARKDOWN format with paragraph breaks after no more than 4 sentences."

    @property
    def history_prompt(self):
        return f"""
BORN
---
{self.start_date.datestr() if self.start_date else "Unknown"}

BACKSTORY
---
{self.backstory_summary}

LIFE EVENTS
---
"""

    @property
    def image_tags(self):
        age_tag = f"{self.age//10}0s"
        return super().image_tags + [self.gender, age_tag, self.race]

    @property
    def image_prompt(self):
        if not self.age:
            self.age = random.randint(15, 50)
            self.save()
        prompt = f"""
A full-body color portrait of a fictional {self.gender} {self.race} {self.genre} character aged {self.age} who is a {self.occupation} and described as: {self.description}

PRODUCE ONLY A SINGLE REPRESENTATION. DO NOT GENERATE VARAITIONS.
"""
        return prompt

    ################# Instance Methods #################

    def generate(self):
        age = self.age if self.age else random.randint(15, 45)
        gender = self.gender or random.choices(self._genders, weights=[4, 5, 1], k=1)[0]

        prompt = f"Generate a {self.race} {gender} NPC aged {age} years that is a {self.occupation} who is described as: {self.traits}. Create, or if already present expand on, the NPC's detailed backstory. Also give the NPC a unique, but {random.choice(('mysterious', 'mundane', 'sinister', 'absurd', 'deadly'))} secret to protect."

        obj = super().generate(prompt=prompt)
        self.hitpoints = random.randint(5, 100)
        if isinstance(self.abilities[0], str):
            self.abilities = [markdown.markdown(a) for a in self.abilities]
        elif isinstance(self.abilities[0], dict):
            self.abilities = [
                markdown.markdown("<br>".join(a.items())) for a in self.abilities
            ]
        self.age = age
        self.gender = gender
        self.save()
        return obj

    ############################# AutoGM #############################
    ## MARK: AUTOGM

    def start_gm_session(self, year):
        self.autogm_summary += [
            self.gm.start(year=year, player=self, scenario=self.autogm_summary)
        ]
        if isinstance(self.autogm_summary.get("player"), str):
            self.autogm_summary["player"] = self.get(self.autogm_summary["player"])
        self.save()

    def run_gm_session(self, message=""):
        self.autogm_summary += [self.world.gm.run(player=self, message=message)]
        self.save()

    def end_gm_session(self, message=""):
        self.autogm_summary += [self.world.gm.end(message=message)]
        self.save()

    ############################# Object Data #############################
    ## MARK: Object Data
    def page_data(self):
        return {
            "pk": str(self.pk),
            "name": self.name,
            "desc": self.desc,
            "backstory": self.backstory,
            "history": self.history,
            "gender": self.gender,
            "age": self.age,
            "occupation": self.occupation,
            "race": self.race,
            "hitpoints": self.hitpoints,
            "attributes": {
                "strength": self.strength,
                "dexerity": self.dexterity,
                "constitution": self.constitution,
                "wisdom": self.wisdom,
                "intelligence": self.intelligence,
                "charisma": self.charisma,
            },
            "abilities": self.abilities,
            "wealth": [w for w in self.wealth],
            "items": [{"name": r.name, "pk": str(r.pk)} for r in self.items],
        }

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_is_player()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ############### Verification Methods ##############
    def pre_save_is_player(self):
        # log(self.is_player)
        if self.is_player == "False":
            self.is_player = False
        else:
            self.is_player = bool(self.is_player)
        # log(self.is_player)
