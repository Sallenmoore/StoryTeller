import random

import markdown

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    BoolAttr,
    DictAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from models.abstracts.actor import Actor


class Character(Actor):
    dnd_beyond_id = StringAttr(default="")
    is_player = BoolAttr(default=False)
    gender = StringAttr(default="")
    occupation = StringAttr(default="")
    children_relation = ListAttr(ReferenceAttr(choices=["Character"]))
    parents_relation = ListAttr(ReferenceAttr(choices=["Character"]))
    partners_relation = ListAttr(ReferenceAttr(choices=["Character"]))
    siblings_relation = ListAttr(ReferenceAttr(choices=["Character"]))
    ancestor_relation = ListAttr(ReferenceAttr(choices=["Character"]))
    descendant_relation = ListAttr(ReferenceAttr(choices=["Character"]))
    abilities = ListAttr(StringAttr(default=""))
    race = StringAttr(default="")
    wealth = ListAttr(StringAttr(default=""))
    chats = DictAttr()
    autogm_summary = DictAttr()

    _no_copy = Actor._no_copy | {"chats": {}}
    parent_list = ["City", "Location", "POI", "Encounter", "Faction"]
    _possible_events = [
        "Birth",
        *Actor._possible_events,
        "Disappeared",
        "Death",
    ]
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
                "notes": {
                    "type": "array",
                    "description": "Create at least 3 separate descriptions of potential side quests involving the NPC. For each include the name of the quest, a brief description of the quest, and the rewards for completing the quest.",
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
    def chat_summary(self):
        return self.chats["summary"]

    @property
    def end_date_str(self):
        return "Died" if self.end_date.get("year") else "Unknown"

    @property
    def gm(self):
        return self.world.gm

    @property
    def start_date_str(self):
        return "Born" if self.start_date.get("year") else "Unknown"

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
            self.age = random.randint(15, 45)
            self.save()
        prompt = f"""
A full-body color portrait of a fictional {self.gender} {self.race} {self.genre} character aged {self.age} who is a {self.occupation} and described as: {self.description}

PRODUCE ONLY A SINGLE REPRESENTATION. DO NOT GENERATE VARAITIONS.
"""
        return prompt

    @property
    def lineage(self):
        return {
            "child": self.children_relation,
            "parent": self.parents_relation,
            "partner": self.partners_relation,
            "sibling": self.siblings_relation,
            "ancestor": self.ancestor_relation,
            "descendant": self.descendant_relation,
        }

    ################# Instance Methods #################

    def generate(self):
        age = self.age if self.age else random.randint(15, 45)
        gender = self.gender or random.choices(self._genders, weights=[4, 5, 1], k=1)[0]

        prompt = f"Generate a {self.race} {gender} NPC aged {age} years that is a {self.occupation} who is described as: {self.traits}. Write, or if already present expand on, the NPC's detailed backstory that only includes publicly known information. Also give the NPC a unique, but {random.choice(('mysterious', 'mundane', 'sinister', 'absurd', 'deadly'))} secret to protect."

        obj = super().generate(prompt=prompt)
        self.hitpoints = random.randint(5, 300)
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

    ############################# LINEAGE #############################
    ## MARK: LINEAGE

    def add_lineage(self, obj, relation):
        relation = f"{relation}_relation"
        if relation not in [
            "children_relation",
            "parents_relation",
            "partners_relation",
            "siblings_relation",
            "ancestor_relation",
            "descendant_relation",
        ]:
            raise ValidationError(f"Invalid relation {relation}")
        elif obj not in getattr(self, relation):
            getattr(self, relation).append(obj)

        inverse = {
            "children_relation": "parents_relation",
            "parents_relation": "children_relation",
            "siblings_relation": "siblings_relation",
            "ancestor_relation": "descendant_relation",
            "descendant_relation": "ancestor_relation",
        }.get(relation, relation)
        if self not in getattr(obj, inverse):
            getattr(obj, inverse).append(self)
        (
            obj.associations.append(c)
            for r, cat in self.lineage.items()
            for c in cat
            if c not in obj.associations
        )
        (
            self.associations.append(c)
            for r, cat in obj.lineage.items()
            for c in cat
            if c not in self.associations
        )
        obj.save()
        self.save()
        return self.lineage

    def remove_lineage(self, obj):
        for relation, objs in self.lineage.items():
            if obj in objs:
                objs.remove(obj)
        self.save()
        return self.lineage

    ############################# CHAT #############################
    ## MARK: CHAT

    def chat(self, message=""):
        # summarize conversation
        if self.chats["message"] and self.chats["response"]:
            primer = f"""As an expert AI in {self.world.genre} TTRPG Worldbuilding, use the previous chat CONTEXT as a starting point to generate a readable summary from the PLAYER MESSAGE and NPC RESPONSE that clarifies the main points of the conversation. Avoid unnecessary details.
            """
            text = f"""
            CONTEXT:\n{self.chats["summary"] or "This is the beginning of the conversation."}
            PLAYER MESSAGE:\n{self.chats['message']}
            NPC RESPONSE:\n{self.chats['response']}"
            """

            self.chats["summary"] = self.system.text_agent.summarize_text(
                text, primer=primer
            )

        message = message.strip() or "Tell me a little more about yourself..."
        primer = f"You are playing the role of the Character {self.name} talking to a Player. You should reference the Character model information in the uploaded file with the primary key: {self.pk}."
        prompt = "Respond as the NPC matching the following description:"
        prompt += f"""
            PERSONALITY: {self.traits}

            DESCRIPTION: {self.desc}

            BACKSTORY: {self.backstory_summary}

            GOAL: {self.goal}

        Use the following chat CONTEXT as a starting point:

        CONTEXT: {self.chats["summary"]}

        PLAYER MESSAGE: {message}
        """

        response = self.system.chat(prompt, primer)
        self.chats["history"].append((message, response))
        self.chats["message"] = message
        self.chats["response"] = response
        self.save()

        return self.chats

    def clear_chat(self):
        self.chats["history"] = []
        self.save()

    ############################# AutoGM #############################
    ## MARK: AUTOGM

    def start_gm_session(self, year):
        self.autogm_summary = self.gm.start(
            year=year, player=self, scenario=self.autogm_summary
        )
        if isinstance(self.autogm_summary.get("player"), str):
            self.autogm_summary["player"] = self.get(self.autogm_summary["player"])
        self.save()

    def run_gm_session(self, message=""):
        self.autogm_summary = self.world.gm.run(message=message)
        if isinstance(self.autogm_summary.get("player"), str):
            self.autogm_summary["player"] = self.get(self.autogm_summary["player"])
        self.save()

    def end_gm_session(self, message=""):
        self.autogm_summary = self.world.gm.end(message=message)
        if isinstance(self.autogm_summary.get("player"), str):
            self.autogm_summary["player"] = self.get(self.autogm_summary["player"])
        self.save()

    ############################# Object Data #############################
    ## MARK: Object Data
    def page_data(self):
        return {
            "pk": str(self.pk),
            "name": self.name,
            "start_date": self.start_date.datestr() if self.start_date else "Unknown",
            "end_date": self.end_date.datestr() if self.end_date else "Unknown",
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
            "relations": self.get_relations_data(),
        }

    def get_relations_data(self):
        return {
            "children": [
                {"name": o.name, "pk": str(o.pk)} for o in self.children_relation
            ],
            "parents": [
                {"name": o.name, "pk": str(o.pk)} for o in self.parents_relation
            ],
            "partners": [
                {"name": o.name, "pk": str(o.pk)} for o in self.partners_relation
            ],
            "sibling": [
                {"name": o.name, "pk": str(o.pk)} for o in self.siblings_relation
            ],
            "ancestor": [
                {"name": o.name, "pk": str(o.pk)} for o in self.ancestor_relation
            ],
            "descendant": [
                {"name": o.name, "pk": str(o.pk)} for o in self.descendant_relation
            ],
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

    def post_save_ac(self):
        if not self.ac:
            self.ac = max(
                10,
                (int(self.dexterity) - 10) // 2 + (int(self.strength) - 10) // 2 + 10,
            )
