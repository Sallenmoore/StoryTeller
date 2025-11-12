import random

from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    BoolAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)

from autonomous import log
from models.campaign.campaign import Campaign
from models.ttrpgobject.ttrpgobject import TTRPGObject

from .character import Character


class Faction(TTRPGObject):
    goal = StringAttr(default="")
    leader = ReferenceAttr(choices=["Character"])
    slogan = StringAttr(default="")
    is_player_faction = BoolAttr(default=False)
    parent_list = ["District", "City", "Region", "World"]
    rumors = ListAttr(StringAttr(default=""))

    end_date_label = "Disbanded"

    _funcobj = {
        "name": "generate_faction",
        "description": "completes Faction data object",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "An evocative and unique name",
                },
                "status": {
                    "type": "string",
                    "description": "current, immediate situation the faction is in, such as thriving, in decline, recovering from a disaster, etc.",
                },
                "desc": {
                    "type": "string",
                    "description": "A brief description of the members of the faction. Only include publicly known information.",
                },
                "backstory": {
                    "type": "string",
                    "description": "The faction's backstory",
                },
                "slogan": {
                    "type": "string",
                    "description": "The faction's slogan",
                },
                "goal": {
                    "type": "string",
                    "description": "The faction's goals and secrets",
                },
                "status": {
                    "type": "string",
                    "description": "The faction's current status",
                },
                "rumors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of rumors about the faction",
                },
            },
        },
    }

    ################### Instance Properties #####################

    @property
    def gm(self):
        return self.world.gm

    @property
    def image_prompt(self):
        return f"A full color poster for a group named {self.name} and described as {self.desc}. The poster should feature symbolic imagery that represents the faction's ideals and goals, with a dramatic and epic style."

    @property
    def jobs(self):
        jobs = []
        for c in self.characters:
            jobs += c.quests
        return jobs

    @property
    def map(self):
        return self.parent.map if self.parent else self.world.map

    @property
    def players(self):
        return [c for c in self.characters if c.is_player]

    @property
    def owner(self):
        return self.leader

    ################### Crud Methods #####################

    def generate(self):
        prompt = f"Generate a {self.genre} faction using the following trait as a motif: {self.traits}. The faction should have a backstory that gives them a goal they are working toward"
        if self.stories:
            prompt += f"""
            and is somehow connected to the following storyline:
            {random.choice(self.stories).summary}
            """
        if self.leader:
            prompt += f"""
            The current leader of the faction is:
            - Name: {self.leader.name}
            - Backstory: {self.leader.history}
            """
        results = super().generate(prompt=prompt)
        self.save()
        return results

    ################### Instance Methods #####################

    ############################# Serialization Methods #############################
    ## MARK: Serialization
    def page_data(self):
        if not self.history:
            self.resummarize()
        return {
            "pk": str(self.pk),
            "image": str(self.image.url()) if self.image else None,
            "name": self.name,
            "backstory": self.backstory,
            "history": self.history,
            "goal": self.goal,
            "slogan": self.slogan,
            "leader": {"name": self.leader.name, "pk": str(self.leader.pk)}
            if self.leader
            else "Unknown",
            "status": self.status if self.status else "Unknown",
            "character_members": [
                {"name": ch.name, "pk": str(ch.pk)} for ch in self.characters
            ],
        }

    # def foundry_export(self):
    #     source_data = self.page_data()
    #     """
    #     Transforms a generic faction JSON object into the specific Systems Without Number (SWN)
    #     "faction" Actor document schema.
    #     """
    #     # 1. Define the target schema structure with required defaults
    #     target_schema = {
    #         "name": "Faction",
    #         "type": "faction",
    #         "img": "systems/swnr/assets/icons/faction.png",
    #         "system": {
    #             "description": "",
    #             "active": True,
    #             "health": {"value": 7, "temp": 0},
    #             "facCreds": 0,
    #             "xp": 0,
    #             "homeworld": "",
    #             "forceRating": 1,
    #             "cunningRating": 1,
    #             "wealthRating": 1,
    #             "factionGoal": "",
    #             "factionGoalDesc": "",
    #             "tags": [],
    #             "log": [],
    #         },
    #         "prototypeToken": {
    #             "name": "Faction",
    #             "displayName": 0,
    #             "actorLink": False,
    #             "width": 1,
    #             "height": 1,
    #             "texture": {"src": "systems/swnr/assets/icons/faction.png"},
    #             "bar1": {"attribute": "health"},
    #             "bar2": {"attribute": "power"},
    #         },
    #         "items": [],
    #         "effects": [],
    #         "flags": {},
    #         "ownership": {"default": 0},
    #         "_stats": {},
    #     }

    #     # 2. Map core fields
    #     faction_name = source_data.get("name", "Unknown Faction").strip()
    #     target_schema["name"] = faction_name
    #     target_schema["prototypeToken"]["name"] = faction_name

    #     # Map Image if available
    #     if url := source_data.get("image", "").strip():
    #         target_schema["img"] = f"https://storyteller.stevenamoore.dev{url}"

    #     # 3. Concatenate and map description/status/history fields to the main description
    #     backstory_html = source_data.get("backstory", "")
    #     history_html = source_data.get("history", "")
    #     status_html = source_data.get("status", "")
    #     leader_name = source_data.get("leader", "Unknown")

    #     # Extract list of character members for display
    #     members = [
    #         m.get("name")
    #         for m in source_data.get("character_members", [])
    #         if m.get("name")
    #     ]

    #     # Combine content into a structured HTML description for the sheet
    #     combined_desc = f"""
    #         <h2>Organization Details</h2>
    #         <p><strong>Leader:</strong> {leader_name}</p>
    #         <p><strong>Known Members:</strong> {", ".join(members) if members else "None specified"}</p>
    #         <p><strong>Slogan:</strong> <em>{source_data.get("slogan", "").strip()}</em></p>

    #         <h2>Backstory</h2>
    #         {backstory_html}

    #         <h2>History</h2>
    #         {history_html}

    #         <h2>Status, Strengths, and Weaknesses</h2>
    #         {status_html}
    #     """

    #     target_schema["system"]["description"] = combined_desc.strip()

    #     # 4. Map Goal fields
    #     target_schema["system"]["factionGoalDesc"] = source_data.get("goal", "").strip()

    #     # NOTE: Faction Goal (the short field) is left empty as per schema default,
    #     # and the detailed HTML goal is placed in factionGoalDesc.

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
        document.pre_save_leader()
        document.pre_save_player_faction()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################
    def pre_save_leader(self):
        if isinstance(self.leader, str):
            if value := Character.get(self.leader):
                self.leader = value
            else:
                raise ValidationError(f"Character {self.leader} not found")

    def pre_save_player_faction(self):
        if self.is_player_faction == "False":
            self.is_player_faction = False
        else:
            self.is_player_faction = bool(self.is_player_faction)
