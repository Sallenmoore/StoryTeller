import random

import markdown
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)

from autonomous import log
from models.base.actor import Actor


class Character(Actor):
    dnd_beyond_id = StringAttr(default="")
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
                    "description": "The NPC's profession or daily occupation.",
                }
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
A full-body color portrait of a {self.gender} {self.genre} {self.species} aged {self.age} {f"who is a {self.occupation}" if self.occupation and self.occupation != "General"}, looks like {self.lookalike}, and is described as: {self.description}

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
Create, or if already present expand on, the NPC's detailed backstory.
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

    def foundry_export(self):
        source_data = self.page_data()
        """
        Transforms a generic 'mech' or 'human' JSON object into the specific
        Systems Without Number (SWN) "character" Actor document schema.
        """
        # 1. Define the target schema structure with required defaults
        target_schema = {
            "name": "Character",
            "type": "character",
            "img": "icons/svg/mystery-man.svg",
            "system": {
                "health": {"value": 10, "max": 10},
                "biography": "",
                "species": "",
                "access": {"value": 1, "max": 1},
                "traumaTarget": 6,
                "baseAc": 10,
                "meleeAc": 10,
                "ab": 1,
                "meleeAb": 1,
                "systemStrain": {"value": 0, "permanent": 0},
                "pools": {},
                "effortCommitments": {},
                "speed": 10,
                "cyberdecks": [],
                "health_max_modified": 0,
                "stats": {
                    "str": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "dex": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "con": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "int": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "wis": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "cha": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                },
                "hitDie": "d6",
                "level": {"value": 1, "exp": 0, "expToLevel": 3},
                "goals": "",
                "class": "",
                "homeworld": "",
                "background": "",
                "employer": "",
                "languages": [],
                "credits": {"debt": 0, "balance": 0, "owed": 0},
                "unspentSkillPoints": 0,
                "unspentPsySkillPoints": 0,
                "extra": {"value": 0, "max": 10},
                "tweak": {
                    "advInit": False,
                    "showResourceList": False,
                    "showCyberware": True,
                    "showPsychic": True,
                    "showArts": False,
                    "showSpells": False,
                    "showAdept": False,
                    "showMutation": False,
                    "showPoolsInHeader": False,
                    "showPoolsInPowers": True,
                    "showPoolsInCombat": True,
                    "resourceList": [],
                    "debtDisplay": "Debt",
                    "owedDisplay": "Owed",
                    "balanceDisplay": "Balance",
                    "initiative": {},
                },
            },
            "prototypeToken": {
                "name": "Character",
                "displayName": 0,
                "actorLink": False,
                "width": 1,
                "height": 1,
                "texture": {"src": "icons/svg/mystery-man.svg"},
                "bar1": {"attribute": "health"},
                "bar2": {"attribute": "power"},
            },
            "items": [],
            "effects": [],
            "flags": {},
            "ownership": {"default": 0},
            "_stats": {},
        }

        # Helper function to safely get attribute base score
        def get_attr_score(attr_key, default=9):
            # Source uses 'dexerity', target uses 'dex'
            key_map = {"dexerity": "dex"}
            final_key = key_map.get(attr_key, attr_key)

            # We assume the source attribute scores are the Base scores
            return int(
                source_data.get("attributes", {}).get(
                    final_key, source_data.get("attributes", {}).get(attr_key, default)
                )
            )

        # 2. Map Core Fields (Name, Image, Health, AC, Speed)
        char_name = source_data.get("name", "Unknown Character").strip()
        target_schema["name"] = char_name
        target_schema["prototypeToken"]["name"] = char_name

        if url := source_data.get("image", "").strip():
            target_schema["img"] = f"https://storyteller.stevenamoore.dev{url}"

        # Health (Hit Points)
        hp = int(source_data.get("hitpoints", 10))
        target_schema["system"]["health"]["value"] = hp
        target_schema["system"]["health"]["max"] = hp

        # AC
        target_schema["system"]["baseAc"] = int(source_data.get("ac", 10))
        target_schema["system"]["meleeAc"] = int(source_data.get("ac", 10))

        # Speed
        target_schema["system"]["speed"] = int(source_data.get("speed", 10))

        # Occupation -> Class and Species
        target_schema["system"]["class"] = source_data.get("occupation", "").strip()
        target_schema["system"]["species"] = source_data.get("species", "").strip()

        # Level (default to 1 since source JSON doesn't provide it)
        target_schema["system"]["level"]["value"] = int(source_data.get("level", 1))

        # 3. Map Attributes (Stats)
        for stat_key in target_schema["system"]["stats"].keys():
            score = get_attr_score(stat_key)
            target_schema["system"]["stats"][stat_key]["base"] = score

        # 4. Map Narrative Fields (Biography and Goals)
        skills_list = [
            f"<li><strong>{k}:</strong> {v}</li>"
            for k, v in source_data.get("skills", {}).items()
            if v
        ]

        # Combine description fields into biography
        combined_biography = f"""
            <h2>Character Details</h2>
            <p><strong>Species:</strong> {source_data.get("species", "N/A")}</p>
            <p><strong>Class/Occupation:</strong> {source_data.get("occupation", "N/A")}</p>
            <p><strong>Gender:</strong> {source_data.get("gender", "Unknown")}</p>
            <p><strong>Age:</strong> {source_data.get("age", "Unknown")}</p>
            <hr/>

            <h2>Physical Description</h2>
            <p>{source_data.get("desc", "No physical description provided.")}</p>

            <h2>Backstory Snippets</h2>
            {source_data.get("backstory", "")}

            <h2>Detailed History</h2>
            {source_data.get("history", "")}

            <h2>Skills (Reference Only)</h2>
            <ul>{"".join(skills_list) if skills_list else "<li>No non-default skill values provided.</li>"}</ul>
        """
        target_schema["system"]["biography"] = combined_biography.strip()
        target_schema["system"]["goals"] = source_data.get("goal", "").strip()

        return target_schema

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
