import random

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    BoolAttr,
    ReferenceAttr,
    StringAttr,
)
from models.campaign.campaign import Campaign
from models.ttrpgobject.ttrpgobject import TTRPGObject

from .character import Character


class Faction(TTRPGObject):
    goal = StringAttr(default="")
    status = StringAttr(default="")
    leader = ReferenceAttr(choices=["Character"])
    is_player_faction = BoolAttr(default=False)
    current_campaign = ReferenceAttr(choices=["Campaign"])
    parent_list = ["District", "City", "Region", "World"]
    _traits_list = [
        "secretive",
        "reckless",
        "cautious",
        "suspicious",
        "violent",
        "sinister",
        "religous",
        "racist",
        "egalitarian",
        "ambitious",
        "corrupt",
        "charitable",
        "greedy",
        "generous",
    ]

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
                "desc": {
                    "type": "string",
                    "description": "A brief description of the members of the faction. Only include publicly known information.",
                },
                "backstory": {
                    "type": "string",
                    "description": "The faction's backstory",
                },
                "goal": {
                    "type": "string",
                    "description": "The faction's goals and secrets",
                },
                "status": {
                    "type": "string",
                    "description": "The faction's current status",
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
        return f"""A full color poster for a group named {self.name} and described as {self.desc}.
        """

    @property
    def map(self):
        return self.parent.map if self.parent else self.world.map

    @property
    def players(self):
        return [c for c in self.characters if c.is_player]

    ################### Crud Methods #####################

    def generate(self):
        prompt = f"Generate a {self.genre} faction using the following trait as a guideline: {self.traits}. The faction should have a backstory containing a {random.choice(('boring', 'mysterious', 'sinister'))} secret that gives them a goal they are working toward."
        if self.leader:
            prompt += f"""
            The current leader of the faction is:
            - NAME: {self.leader.name}
            - Backstory: {self.leader.backstory_summary or self.leader.desc}
            - Location: {self.backstory_summary or "Indoors"}
            """
        results = super().generate(prompt=prompt)
        self.save()
        return results

    ################### Instance Methods #####################

    ############################# AutoGM #############################
    ## MARK: AUTOGM

    def generate_campaign(self, pc=None):
        if not self.current_campaign:
            self.current_campaign = Campaign(world=self.world)
            self.current_campaign.save()
            self.save()
        self.current_campaign.generate_outline()

    ############################# Serialization Methods #############################
    ## MARK: Serialization
    def page_data(self):
        return {
            "pk": str(self.pk),
            "name": self.name,
            "backstory": self.backstory,
            "history": self.history,
            "goal": self.goal,
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
        document.pre_save_current_campaign()

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
        if self.is_player_faction == "on":
            self.is_player_faction = True
        # log(self.is_player_faction)

    def pre_save_current_campaign(self):
        if not self.current_campaign:
            self.current_campaign = Campaign(
                world=self.world, players=self.players, associations=self.associations
            )
        else:
            self.current_campaign.world = self.world
            self.current_campaign.players = self.players[:]
            for ass in self.associations:
                if ass not in self.current_campaign.associations[:]:
                    self.current_campaign.associations += [ass]
        log(self.current_campaign.associations)
        self.current_campaign.save()
        log(self.current_campaign.associations)
