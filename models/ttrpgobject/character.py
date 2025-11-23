import random

import markdown
from autonomous.model.autoattr import (
    BoolAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)

from autonomous import log
from models.base.actor import Actor


class Character(Actor):
    dnd_beyond_id = StringAttr(default="")
    is_player = BoolAttr(default=False)
    occupation = StringAttr(default="")
    wealth = ListAttr(StringAttr(default=""))
    quests = ListAttr(ReferenceAttr(choices=["Quest"]))
    parent_lineage = ListAttr(ReferenceAttr(choices=["Character"]))
    sibling_lineage = ListAttr(ReferenceAttr(choices=["Character"]))
    children_lineage = ListAttr(ReferenceAttr(choices=["Character"]))

    start_date_label = "Born"
    end_date_label = "Died"

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
            "Outsider or exotic",
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
                    "description": "The NPC's profession or daily occupation.",
                },
                "wealth": {
                    "type": "array",
                    "description": "A list of items the NPC possesses, with descriptions for each. There should be at least one mundane item and one valuable item at minimum.",
                    "items": {"type": "string"},
                },
            },
        },
    }

    ################# Instance Properities #################

    @property
    def child_key(self):
        return "players" if self.is_player else "characters"

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
A full-body color portrait of a {self.gender} {self.genre} {self.species} aged {self.age} {f"who is a {self.occupation}" if self.occupation and self.occupation != "General" else ""}, looks a faintly similar to {self.lookalike} (changed enough to not be identical), and described as: {self.description}

PRODUCE ONLY A SINGLE REPRESENTATION. DO NOT GENERATE VARIATIONS.
"""
        return prompt

    @property
    def lineage(self):
        return [*self.parent_lineage, *self.sibling_lineage, *self.children_lineage]

    ################# Instance Methods #################

    def generate(self):
        age = self.age if self.age else random.randint(21, 55)
        gender = (
            self.gender or random.choices(self._genders, weights=[10, 10, 1], k=1)[0]
        )
        occupation = self.occupation or random.choice(
            [
                "merchant",
                "soldier",
                "scholar",
                "noble",
                "spy",
                "artisan",
                "healer",
                "farmer",
                "laborer",
                "sailor",
                "thief",
                "priest",
                "entertainer",
                "alchemist",
                "explorer",
            ]
        )

        prompt = f"""Generate a {gender} {self.species} {self.archetype} NPC aged {age} years that is a {occupation}. Use the following thematic motif: {self.traits}.
"""

        result = super().generate(prompt=prompt)

        return result

    ############################# Object Data #############################
    ## MARK: Object Data
    def page_data(self):
        if not self.history:
            self.resummarize()
        return {
            "pk": str(self.pk),
            "image": str(self.image.url()) if self.image else None,
            "name": self.name,
            "desc": self.desc,
            "backstory": self.backstory,
            "history": self.history,
            "gender": self.gender,
            "speed": self.speed,
            "speed_units": self.speed_units,
            "age": self.age,
            "occupation": self.occupation,
            "archetype": self.archetype,
            "species": self.species,
            "hitpoints": self.hitpoints,
            "ac": self.ac,
            "is_player": self.is_player,
            "attributes": {
                "strength": self.strength,
                "dexerity": self.dexterity,
                "constitution": self.constitution,
                "wisdom": self.wisdom,
                "intelligence": self.intelligence,
                "charisma": self.charisma,
            },
            "skills": self.skills,
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
