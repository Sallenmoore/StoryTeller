import json
import re

import markdown

from autonomous import log
from autonomous.model.autoattr import (
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.base.ttrpgbase import TTRPGBase
from models.ttrpgobject.district import District
from models.ttrpgobject.location import Location


class SceneNote(AutoModel):
    name = StringAttr(default="")
    num = IntAttr(default=0)
    notes = StringAttr(default="")
    description = StringAttr(default="")
    setting = ListAttr(ReferenceAttr(choices=["Place"]))
    encounters = ListAttr(ReferenceAttr(choices=["Encounter"]))
    actors = ListAttr(ReferenceAttr(choices=["Character", "Creature"]))
    initiative = ListAttr(StringAttr(default=""))
    images = ListAttr(ReferenceAttr(choices=["Image"]))

    @property
    def associations(self):
        return [*self.setting, *self.encounters, *self.actors]

    def add_setting(self, obj):
        if obj not in self.setting:
            self.setting += [obj]
            self.save()
        return obj

    def remove_setting(self, obj):
        self.setting = [s for s in self.setting if s.pk != obj.pk]
        self.save()

    def add_encounter(self, obj):
        if obj not in self.encounters:
            self.encounters += [obj]
            self.save()
        return obj

    def remove_encounter(self, obj):
        self.encounters = [e for e in self.encounters if e.pk != obj.pk]
        self.save()

    def add_actor(self, obj):
        if obj not in self.actors:
            self.actors += [obj]
            self.save()
        return obj

    def remove_actor(self, obj):
        self.actors = [e for e in self.actors if e.pk != obj.pk]
        self.save()


class Episode(AutoModel):
    name = StringAttr(default="")
    episode_num = IntAttr(default=0)
    description = StringAttr(default="")
    scenenotes = ListAttr(ReferenceAttr(choices=[SceneNote]))
    start_date = StringAttr(default="")
    end_date = StringAttr(default="")
    campaign = ReferenceAttr(choices=["Campaign"], required=True)
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    episode_report = StringAttr(default="")
    summary = StringAttr(default="")

    ##################### PROPERTY METHODS ####################

    @property
    def actors(self):
        return [*self.characters, *self.creatures]

    @property
    def characters(self):
        return [a for a in self.associations if a.model_name() == "Character"]

    @property
    def creatures(self):
        return [a for a in self.associations if a.model_name() == "Creature"]

    @property
    def encounters(self):
        return [a for a in self.associations if a.model_name() == "Encounter"]

    @property
    def factions(self):
        return [a for a in self.associations if a.model_name() == "Faction"]

    @property
    def items(self):
        return [a for a in self.associations if a.model_name() == "Item"]

    @property
    def districts(self):
        return [a for a in self.associations if a.model_name() == "District"]

    @property
    def players(self):
        return [a for a in self.characters if a.is_player]

    @property
    def locations(self):
        return [a for a in self.associations if a.model_name() == "Location"]

    @property
    def cities(self):
        return [a for a in self.associations if a.model_name() == "City"]

    @property
    def places(self):
        return [a for a in [*self.scenes, *self.cities, *self.regions]]

    @property
    def regions(self):
        return [a for a in self.associations if a.model_name() == "Region"]

    @property
    def vehicles(self):
        return [a for a in self.associations if a.model_name() == "Vehicle"]

    @property
    def scenes(self):
        return [
            a for a in self.associations if a.model_name() in ["Location", "District"]
        ]

    @property
    def music_choices(self):
        return json.load(open("static/sounds/music.json"))

    @property
    def world(self):
        # IMPORTANT: this is here to register the model
        # without it, the model may not have been registered yet and it will fail
        from models.world import World

        return self.campaign.world

    ##################### INSTANCE METHODS ####################
    def resummarize(self):
        self.summary = (
            self.world.system.generate_summary(
                self.episode_report,
                primer="Generate a summary of less than 100 words of the episode events in MARKDOWN format with a paragraph breaks where appropriate, but after no more than 4 sentences.",
            )
            if len(self.episode_report) > 256
            else self.episode_report
        )
        self.summary = self.summary.replace("```markdown", "").replace("```", "")
        self.summary = (
            markdown.markdown(self.summary).replace("h1>", "h3>").replace("h2>", "h3>")
        )
        self.save()
        return self.summary

    def get_scene(self, pk):
        return Location.get(pk) or District.get(pk)

    def set_as_current(self):
        self.campaign.current_episode = self
        self.campaign.save()
        return self.campaign

    def add_association(self, obj):
        if not obj:
            raise ValueError("obj must be a valid object")
        if obj not in self.associations:
            self.associations += [obj]
            self.save()
            obj.save()
        return obj

    def add_scene_note(self, name=None):
        num = len(self.scenenotes) + 1
        if not name:
            name = f"Episode {len(self.scenenotes)}:"
        scenenote = SceneNote(name=name, num=num)
        scenenote.save()
        self.scenenotes += [scenenote]
        self.save()
        return scenenote

    def generate_gn(self):
        for sn in self.scenenotes:
            prompt = f"Generate a single comic panel for the following {self.campaign.genre} TTRPG session scene."
            for setting in sn.setting:
                prompt += f"\nSETTING: {setting.description_summary}\n"
            prompt += "\nDESCRIPTION OF CHARACTERS IN SCENE\n"
            for actor in sn.actors:
                prompt += f"""{actor.name}: {actor.description_summary}\n  - Looks Like: {actor.lookalike}\n"""
            prompt += f"\nSCENE DESCRIPTION\n\n{sn.description}\n"
            log(prompt, _print=True)

    def remove_association(self, obj):
        self.associations = [a for a in self.associations if a != obj]
        self.save()

    ## MARK: - Verification Hooks
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
        document.pre_save_campaign()
        document.pre_save_associations()
        document.pre_save_episode_num()
        document.pre_save_scene_note()

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify methods ##################
    def pre_save_campaign(self):
        if self not in self.campaign.episodes:
            self.campaign.episodes += [self]

    def pre_save_associations(self):
        assoc = []
        for a in self.associations:
            if a:
                if a not in assoc:
                    assoc += [a]
                if a not in self.campaign.associations:
                    self.campaign.associations += [a]
        self.associations = assoc
        self.associations.sort(key=lambda x: (x.model_name(), x.name))

    ################### verify current_scene ##################
    def pre_save_episode_num(self):
        if not self.episode_num:
            num = re.search(r"\b\d+\b", self.name).group(0)
            if num.isdigit():
                self.episode_num = int(num)

    def pre_save_scene_note(self):
        self.scenenotes = [s for s in self.scenenotes if s]
        self.scenenotes.sort(key=lambda x: x.num)
