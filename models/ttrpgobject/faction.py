import random

import markdown

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    BoolAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from models.autogm.autogmscene import AutoGMScene
from models.ttrpgobject.ttrpgobject import TTRPGObject

from .character import Character


class Faction(TTRPGObject):
    goal = StringAttr(default="")
    status = StringAttr(default="")
    leader = ReferenceAttr(choices=["Character"])
    is_player_faction = BoolAttr(default=False)
    # autogm attributes
    next_scene = ReferenceAttr(choices=["AutoGMScene"])
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
    def first_scene(self):
        return self.autogm_summary[0] if self.autogm_summary else None

    @property
    def gm(self):
        return self.world.gm

    @property
    def image_prompt(self):
        return f"""A full color poster for a group named {self.name} and described as {self.desc}.
        """

    @property
    def last_scene(self):
        return self.autogm_summary[-1] if self.autogm_summary else None

    @property
    def map(self):
        return self.parent.map if self.parent else self.world.map

    @property
    def quests(self):
        return self.last_scene.quest_log if self.last_scene else []

    @property
    def players(self):
        return [c for c in self.characters if c.is_player]

    @property
    def ready(self):
        return len(self.is_ready()) == len(self.players)

    @ready.setter
    def ready(self, val):
        self.next_scene.is_ready = bool(val)

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

    def end_gm_session(self):
        self.gm.end(party=self)
        self.save()

    def autogm_session(self):
        self.gm.run(party=self)

        self.save()

    def autogm_combat(self):
        if self.last_scene.type == "combat":
            if self.last_scene.initiative.combat_ended:
                self.gm.run_combat_round(party=self)
            else:
                self.next_scene.type = "investigation"
                self.next_scene.save()
                self.autogm_session()
        else:
            raise ValueError("Invalid Scene Type")

    def end_autogm(self):
        self.autogm_history += self.autogm_summary
        self.autogm_summary = []
        self.save()

    def clear_autogm(self):
        for ags in self.autogm_summary:
            ags.delete()
        self.save()

    def get_next_scene(self, create=False):
        if self.next_scene and create:
            prompt = (
                self.autogm_summary[3].summary if len(self.autogm_summary) > 3 else ""
            )
            for ags in self.autogm_summary[:3]:
                prompt += f" {ags.description}"

            primer = "Generate an evocative, narrative summary of less than 250 words for the given players and events of a TTRPG in MARKDOWN format."
            summary = self.system.generate_summary(prompt, primer)
            summary = summary.replace("```markdown", "").replace("```", "")
            summary = (
                markdown.markdown(summary).replace("h1>", "h3>").replace("h2>", "h3>")
            )
            self.next_scene.summary = summary
            self.next_scene.save()
            self.autogm_summary += [self.next_scene]
            self.next_scene = None
            self.save()

        if not self.next_scene:
            date = (self.last_scene and self.last_scene.date) or self.world.current_date
            ags = AutoGMScene(party=self, date=date)
            ags.save()
            self.next_scene = ags

            if self.last_scene:
                self.next_scene.gm_mode = self.last_scene.gm_mode
                self.next_scene.tone = self.last_scene.tone
                self.next_scene.image_style = self.last_scene.image_style
                self.next_scene.associations = self.last_scene.associations
                self.next_scene.npcs = self.last_scene.npcs
                self.next_scene.combatants = self.last_scene.combatants
                self.next_scene.places = self.last_scene.places
                self.next_scene.loot = self.last_scene.loot
                self.next_scene.quest_log = self.last_scene.quest_log
                self.next_scene.current_quest = self.last_scene.current_quest

                for assoc in self.last_scene.associations:
                    assoc.add_associations(ags.associations)

                for player in self.players:
                    self.next_scene.set_player_message(player)

                self.next_scene.save()
                # log(next_scene=self.next_scene.gm_mode, _print=True)
            self.save()
        return self.next_scene

    def get_last_player_message(self, player):
        return self.last_scene.get_player_message(player) if self.last_scene else ""

    def is_ready(self, player=None):
        if not player:
            return self.next_scene.is_ready

        return bool(
            all(
                [
                    msg.ready
                    for msg in self.next_scene.player_messages
                    if msg.player == player
                ]
            )
        )

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
