import random

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    BoolAttr,
    ReferenceAttr,
    StringAttr,
)
from models.abstracts.ttrpgobject import TTRPGObject

from .character import Character


class Faction(TTRPGObject):
    goal = StringAttr(default="")
    status = StringAttr(default="")
    leader = ReferenceAttr(choices=["Character"])
    is_player_faction = BoolAttr(default=False)

    _no_copy = TTRPGObject._no_copy | {"_leader":None, "_is_player_faction":False}
    _possible_events = [
        "Founded",
        *TTRPGObject._possible_events,
        "Defeated",
        "Disbanded",
    ]
    parent_list = ["City", "Region", "World"]
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
                "notes": {
                    "type": "array",
                    "description": "3 short descriptions of potential secret side quests involving the faction",
                    "items": {"type": "string"},
                },
            },
        },
    }

    ################### Instance Properties #####################

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
            - Location: {self.leader.parent.backstory_summary if self.leader.parent else "Indoors"}
            """
        results = super().generate(prompt=prompt)
        self.save()
        return results

    ################### Instance Methods #####################

    def label(self, model):
        if not isinstance(model, str):
            model = model.__name__
        if model == "Character":
            return "Members"
        return super().label(model)

    def page_data(self):
        return {
            "pk": str(self.pk),
            "name": self.name,
            "start_date": self.start_date.datestr() if self.start_date else "Unknown",
            "end_date": self.end_date.datestr() if self.end_date else "Unknown",
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
        if not document.world:
            raise ValidationError

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)
        if not document.world:
            raise ValidationError

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################
    def pre_save_leader(self):
        if isinstance(self.leader, str):
            if value := Character.get(self.leader):
                self.leader = value
            else:
                raise ValidationError(f"Character {self.leader} not found")
