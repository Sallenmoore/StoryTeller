import random

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    BoolAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from models.ttrpgobject.ttrpgobject import TTRPGObject

from .character import Character


class Faction(TTRPGObject):
    goal = StringAttr(default="")
    status = StringAttr(default="")
    leader = ReferenceAttr(choices=["Character"])
    is_player_faction = BoolAttr(default=False)
    autogm_summary = ListAttr(ReferenceAttr(choices=["AutoGMScene"]))
    autogm_history = ListAttr(ReferenceAttr(choices=["AutoGMScene"]))

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

    def start_gm_session(self, scenario):
        self.gm.start(party=self, scenario=scenario)
        self.save()

    def run_gm_session(self, message=""):
        self.gm.run(party=self, message=message)
        self.save()

    def end_gm_session(self, message=""):
        self.gm.end(party=self, message=message)
        self.save()

    def page_data(self):
        return {
            "pk": str(self.pk),
            "name": self.name,
            "backstory": self.backstory,
            "histroy": self.history,
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
        else:
            self.is_player_faction = False
        log(self.is_player_faction)
