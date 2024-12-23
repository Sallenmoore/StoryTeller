import copy

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
from models.ttrpgobject.ability import Ability
from models.ttrpgobject.ttrpgobject import TTRPGObject


class Actor(TTRPGObject):
    meta = {"abstract": True, "allow_inheritance": True, "strict": False}
    goal = StringAttr(default="Unknown")
    is_player = BoolAttr(default=False)
    gender = StringAttr(default="Unknown")
    age = IntAttr(default=0)
    species = StringAttr(default="Unknown")
    abilities = ListAttr(ReferenceAttr(choices=["Ability"]))
    hitpoints = IntAttr(default=30)
    status = StringAttr(default="healthy")
    ac = IntAttr(default=10)
    current_hitpoints = IntAttr(default=10)
    strength = IntAttr(default=10)
    dexterity = IntAttr(default=10)
    constitution = IntAttr(default=10)
    wisdom = IntAttr(default=10)
    intelligence = IntAttr(default=10)
    charisma = IntAttr(default=10)
    archetype = StringAttr(default="Unknown")
    voice_description = StringAttr(default="")

    _genders = ["male", "female", "non-binary"]

    _funcobj = {
        "name": {
            "type": "string",
            "description": "A unique and unusual first, middle, and last name",
        },
        "gender": {
            "type": "string",
            "description": "preferred gender",
        },
        "age": {
            "type": "integer",
            "description": "physical age in years",
        },
        "voice_description": {
            "type": "string",
            "description": "where applicable, description of the voice including pitch, placement (i.e. throaty to nasally), tempo, volume, tone, and accent",
        },
        "species": {
            "type": "string",
            "description": "species, such as human, orc, monster, etc.",
        },
        "traits": {
            "type": "string",
            "description": "A tag line or motif that describes the character",
        },
        "desc": {
            "type": "string",
            "description": "A detailed physical description optimized for AI image generation of the NPC",
        },
        "backstory": {
            "type": "string",
            "description": "detailed backstory that includes only publicly known information about the NPC, being careful not to reveal sensitive information or secrets",
        },
        "goal": {
            "type": "string",
            "description": "goals and closely guarded secrets",
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
        },
        "archetype": {
            "type": "string",
            "description": "archetype or role in the world, such as Rogue, Wizard, Soldier, etc.",
        },
        "hitpoints": {
            "type": "integer",
            "description": "maximum hit points",
        },
        "strength": {
            "type": "integer",
            "description": "The amount of Strength from 1-20",
        },
        "dexterity": {
            "type": "integer",
            "description": "The amount of Dexterity from 1-20",
        },
        "constitution": {
            "type": "integer",
            "description": "The amount of Constitution from 1-20",
        },
        "intelligence": {
            "type": "integer",
            "description": "The amount of Intelligence from 1-20",
        },
        "wisdom": {
            "type": "integer",
            "description": "The amount of Wisdom from 1-20",
        },
        "charisma": {
            "type": "integer",
            "description": "The amount of Charisma from 1-20",
        },
    }

    @property
    def map(self):
        return self.parent.map if self.parent else None

    @property
    def race(self):
        return self.species

    @race.setter
    def race(self, value):
        self.species = value

    def generate(self, prompt=""):
        self._funcobj["parameters"]["properties"] |= Actor._funcobj
        super().generate(prompt)

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    @classmethod
    def auto_post_init(cls, sender, document, **kwargs):
        super().auto_post_init(sender, document, **kwargs)
        document.pre_save_ac()

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_ac()
        document.pre_save_ability()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ############### Verification Methods ##############

    def pre_save_ac(self):
        self.ac = max(
            10,
            ((int(self.dexterity) - 10) // 2) + ((int(self.strength) - 10) // 2) + 10,
        )

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
