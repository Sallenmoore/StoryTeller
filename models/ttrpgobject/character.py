import random

import markdown

from autonomous import log
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from models.base.actor import Actor
from models.stories.quest import Scene


class Character(Actor):
    dnd_beyond_id = StringAttr(default="")
    occupation = StringAttr(default="")
    wealth = ListAttr(StringAttr(default=""))
    rumors = ListAttr(StringAttr(default=""))
    quests = ListAttr(ReferenceAttr(choices=["Quest"]))

    parent_list = ["Location", "District", "Faction", "City", "Vehicle", "Shop"]

    _template = [
        [
            "Criminal, thug, thief, swindler",
            "Menial, cleaner, retail worker, servant",
            "Unskilled heavy labor, porter, construction",
            "Skilled trade, electrician, mechanic, pilot",
            "Idea worker, programmer, writer",
            "Merchant, business owner, trader, banker",
            "Official, bureaucrat, courtier, clerk",
            "Military, soldier, enforcer, law officer",
        ],
        [
            "The local underclass",
            "Common laborer",
            "Aspiring bourgeoise or upper class",
            "The elite of this society",
            "Minority or foreigner",
            "Offworlders or exotic",
        ],
        [
            "They have significant debt or money woes",
            "A loved one is in trouble",
            "Romantic failure with a desired person",
            "Drug or behavioral addiction",
            "Their superior dislikes or resents them",
            "They have a persistent sickness",
            "They hate their job or life situation",
            "Someone dangerous is targeting them",
            "They're pursuing a disastrous purpose",
            "They have no problems worth mentioning",
        ],
        [
            "Unusually young or old for their role",
            "Young adult",
            "Mature prime",
            "Middle-aged or elderly",
        ],
        [
            "They want a particular romantic partner",
            "They want money for them or a loved one",
            "They want a promotion in their job",
            "They want answers about a past trauma",
            "They want revenge on an enemy",
            "They want to help a beleaguered friend",
            "They want an entirely different job",
            "They want protection from an enemy",
            "They want to leave their current life",
            "They want fame and glory",
            "They want power over those around them",
            "They have everything they want from life",
        ],
    ]

    _funcobj = {
        "name": "generate_npc",
        "description": "creates, completes, and expands on the attributes and story of an existing NPC",
        "parameters": {
            "type": "object",
            "properties": {
                "occupation": {
                    "type": "string",
                    "description": "The NPC's profession or daily occupation",
                },
                "rumors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of 3 rumors the NPC knows about an existing storyline or world event",
                },
            },
        },
    }

    ################# Instance Properities #################

    @property
    def child_key(self):
        return "players" if self.is_player else "characters"

    @property
    def history_primer(self):
        return "Incorporate the below LIFE EVENTS into the BACKSTORY to generate a chronological summary of the character's history in MARKDOWN format with paragraph breaks after no more than 4 sentences."

    @property
    def history_prompt(self):
        if self.age and self.backstory_summary:
            return f"""
AGE
---
{self.age}

BACKSTORY
---
{self.backstory}

"""

    @property
    def image_tags(self):
        age_tag = f"{self.age // 10}0s"
        return super().image_tags + [self.gender, age_tag, self.species]

    @property
    def image_prompt(self):
        if not self.age:
            self.age = random.randint(15, 50)
            self.save()
        prompt = f"""
A full-body color portrait of a fictional {self.gender} {self.species} {self.genre} character aged {self.age or 32} who is a {self.occupation}, looks like {self.lookalike}, and is described as: {self.description}

PRODUCE ONLY A SINGLE REPRESENTATION. DO NOT GENERATE VARIATIONS.
"""
        return prompt

    ################# Instance Methods #################

    def generate(self):
        age = self.age if self.age else random.randint(21, 55)
        gender = (
            self.gender or random.choices(self._genders, weights=[10, 10, 1], k=1)[0]
        )

        prompt = f"Generate a {gender} {self.species} {self.archetype} NPC aged {age} years that is a {self.occupation} who is described as: {self.traits}. Create, or if already present expand on, the NPC's detailed backstory. Also give the NPC a unique, but {random.choice(('mysterious', 'mundane', 'sinister', 'absurd', 'deadly', 'awesome'))} secret to protect that is at least tangentially related to an existing world event."

        result = super().generate(prompt=prompt)

        return result

    ############################# Object Data #############################
    ## MARK: Object Data
    def page_data(self):
        return {
            "pk": str(self.pk),
            "image_pk": str(self.image.pk) if self.image else None,
            "name": self.name,
            "desc": self.desc,
            "backstory": self.backstory,
            "history": self.history,
            "gender": self.gender,
            "age": self.age,
            "occupation": self.occupation,
            "species": self.species,
            "hitpoints": self.hitpoints,
            "attributes": {
                "strength": self.strength,
                "dexerity": self.dexterity,
                "constitution": self.constitution,
                "wisdom": self.wisdom,
                "intelligence": self.intelligence,
                "charisma": self.charisma,
            },
            "abilities": [str(a) for a in self.abilities],
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
        document.pre_save_description()

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

    def pre_save_description(self):
        if not self.backstory:
            for t in self._template:
                self.backstory += f"""
<p>{random.choice(t)}</p>
"""
