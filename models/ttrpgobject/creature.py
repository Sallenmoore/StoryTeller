import random

import markdown
from autonomous.model.autoattr import BoolAttr, IntAttr, StringAttr

from autonomous import log
from models.base.actor import Actor


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
        return super().generate(prompt=prompt)

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
            "hit points": self.hitpoints,
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

    # def foundry_export(self):
    #     source_data = self.page_data()
    #     """
    #     Transforms a generic 'mech' (or similar NPC) JSON object into the specific
    #     Systems Without Number (SWN) "character" Actor document schema.
    #     """
    #     # 1. Define the target schema structure with required defaults
    #     target_schema = {
    #         "name": "Character",
    #         "type": "character",
    #         "img": "icons/svg/mystery-man.svg",
    #         "system": {
    #             "health": {"value": 10, "max": 10},
    #             "biography": "",
    #             "species": "",
    #             "access": {"value": 1, "max": 1},
    #             "traumaTarget": 6,
    #             "baseAc": 10,
    #             "meleeAc": 10,
    #             "ab": 1,
    #             "meleeAb": 1,
    #             "systemStrain": {"value": 0, "permanent": 0},
    #             "pools": {},
    #             "effortCommitments": {},
    #             "speed": 10,
    #             "cyberdecks": [],
    #             "health_max_modified": 0,
    #             "stats": {
    #                 "str": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
    #                 "dex": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
    #                 "con": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
    #                 "int": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
    #                 "wis": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
    #                 "cha": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
    #             },
    #             "hitDie": "d6",
    #             "level": {"value": 1, "exp": 0, "expToLevel": 3},
    #             "goals": "",
    #             "class": "",
    #             "homeworld": "",
    #             "background": "",
    #             "employer": "",
    #             "languages": [],
    #             "credits": {"debt": 0, "balance": 0, "owed": 0},
    #             "unspentSkillPoints": 0,
    #             "unspentPsySkillPoints": 0,
    #             "extra": {"value": 0, "max": 10},
    #             "tweak": {
    #                 "advInit": False,
    #                 "showResourceList": False,
    #                 "showCyberware": True,
    #                 "showPsychic": True,
    #                 "showArts": False,
    #                 "showSpells": False,
    #                 "showAdept": False,
    #                 "showMutation": False,
    #                 "showPoolsInHeader": False,
    #                 "showPoolsInPowers": True,
    #                 "showPoolsInCombat": True,
    #                 "resourceList": [],
    #                 "debtDisplay": "Debt",
    #                 "owedDisplay": "Owed",
    #                 "balanceDisplay": "Balance",
    #                 "initiative": {},
    #             },
    #         },
    #         "prototypeToken": {
    #             "name": "Character",
    #             "displayName": 0,
    #             "actorLink": False,
    #             "width": 1,
    #             "height": 1,
    #             "texture": {"src": "icons/svg/mystery-man.svg"},
    #             "bar1": {"attribute": "health"},
    #             "bar2": {"attribute": "power"},
    #         },
    #         "items": [],
    #         "effects": [],
    #         "flags": {},
    #         "ownership": {"default": 0},
    #         "_stats": {},
    #     }

    #     # Helper function to safely get attribute base score
    #     def get_attr_score(attr_key, default=9):
    #         # Source uses 'dexerity', target uses 'dex'
    #         key_map = {"dexerity": "dex"}
    #         final_key = key_map.get(attr_key, attr_key)

    #         # We assume the source attribute scores are the Base scores
    #         return int(
    #             source_data.get("attributes", {}).get(
    #                 final_key, source_data.get("attributes", {}).get(attr_key, default)
    #             )
    #         )

    #     # 2. Map Core Fields (Name, Image, Health, AC, Speed)
    #     char_name = source_data.get("name", "Unknown Character").strip()
    #     target_schema["name"] = char_name
    #     target_schema["prototypeToken"]["name"] = char_name

    #     if url := source_data.get("image", "").strip():
    #         target_schema["img"] = f"https://storyteller.stevenamoore.dev{url}"

    #     # Health (Hit Points)
    #     hp = int(source_data.get("hit points", 10))
    #     target_schema["system"]["health"]["value"] = hp
    #     target_schema["system"]["health"]["max"] = hp

    #     # AC
    #     target_schema["system"]["baseAc"] = int(source_data.get("ac", 10))
    #     target_schema["system"]["meleeAc"] = int(source_data.get("ac", 10))

    #     # Speed
    #     target_schema["system"]["speed"] = int(source_data.get("speed", 10))

    #     # Archetype -> Class and Species
    #     target_schema["system"]["class"] = source_data.get("archetype", "").strip()
    #     target_schema["system"]["species"] = source_data.get("species", "").strip()

    #     # Level
    #     target_schema["system"]["level"]["value"] = int(source_data.get("level", 1))

    #     # 3. Map Attributes (Stats)
    #     for stat_key in target_schema["system"]["stats"].keys():
    #         score = get_attr_score(stat_key)
    #         target_schema["system"]["stats"][stat_key]["base"] = score

    #     # 4. Map Narrative Fields (Biography and Goals)
    #     skills_list = [
    #         f"<li><strong>{k}:</strong> {v}</li>"
    #         for k, v in source_data.get("skills", {}).items()
    #         if v
    #     ]

    #     # Combine description fields into biography
    #     combined_biography = f"""
    #         <h2>Physical Description & Archetype</h2>
    #         <p><strong>Archetype:</strong> {source_data.get("archetype", "N/A")}</p>
    #         <p><strong>Species:</strong> {source_data.get("species", "N/A")}</p>
    #         <p>{source_data.get("desc", "No physical description provided.")}</p>

    #         <h2>History</h2>
    #         {source_data.get("history", "")}

    #         <h2>Skills (Reference Only)</h2>
    #         <ul>{"".join(skills_list) if skills_list else "<li>No non-default skill values provided.</li>"}</ul>
    #     """
    #     target_schema["system"]["biography"] = combined_biography.strip()
    #     target_schema["system"]["goals"] = source_data.get("goal", "").strip()

    #     return target_schema

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
