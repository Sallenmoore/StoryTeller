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
from models.ttrpgobject.creature import Creature
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
                "rumors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of rumors about the faction",
                },
                "sensory_details": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of sensory details, such as sight, sound, smell, and touch, that a GM can use to bring the faction to life",
                },
            },
        },
    }

    ################### Instance Properties #####################

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
    def members(self):
        return [*Character.search(faction=self), *Creature.search(faction=self)]

    @property
    def owner(self):
        return self.leader

    ################### Crud Methods #####################

    def generate(self):
        prompt = f"Generate a {self.genre} faction using the following trait as a motif: {self.traits}. The faction should have a backstory that gives them a goal they are working toward"
        results = super().generate(prompt=prompt)
        self.save()
        return results

    ################### Instance Methods #####################

    ############################# Serialization Methods #############################
    ## MARK: Serialization
    def page_data(self):
        if not self.history:
            self.generate_history()
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
