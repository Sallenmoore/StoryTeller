import json
import os
import random
import re

import markdown
import requests
from bs4 import BeautifulSoup

from autonomous import log
from autonomous.model.autoattr import (
    DictAttr,
    FileAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.base.ttrpgbase import TTRPGBase
from models.calendar.date import Date
from models.campaign.scenenote import SceneNote
from models.ttrpgobject.character import Character
from models.ttrpgobject.district import District
from models.ttrpgobject.location import Location


class Episode(AutoModel):
    name = StringAttr(default="")
    episode_num = IntAttr(default=0)
    description = StringAttr(default="")
    scenenotes = ListAttr(ReferenceAttr(choices=[SceneNote]))
    start_date_obj = ReferenceAttr(choices=["Date"])
    end_date_obj = ReferenceAttr(choices=["Date"])
    campaign = ReferenceAttr(choices=["Campaign"], required=True)
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    episode_report = StringAttr(default="")
    summary = StringAttr(default="")
    outline = StringAttr(default="")
    images = ListAttr(ReferenceAttr(choices=["Image"]))

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
    def genre(self):
        return self.world.genre

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
    def start_date(self):
        if self.start_date_obj:
            self.save()
            self.start_date_obj.obj = self
            self.start_date_obj.calendar = self.world.calendar
            self.start_date_obj.save()
        return self.start_date_obj

    @start_date.setter
    def start_date(self, date):
        if isinstance(date, Date):
            self.start_date_obj = date
        elif isinstance(date, dict):
            self.start_date_obj = Date(obj=self, calendar=self.world.calendar, **date)
            self.start_date_obj.save()
        elif isinstance(date, str):
            verify_date_format = date.split()
            if verify_date_format[0].isdigit() and verify_date_format[2].isdigit():
                date = Date.from_string(self, self.world.calendar, date)
                self.start_date_obj = date
                self.start_date_obj.save()
            else:
                raise ValueError(
                    "date must be a Date object or a string in the format: <day> <month> <year>"
                )

    @property
    def end_date(self):
        if self.end_date_obj:
            self.end_date_obj.obj = self
            self.end_date_obj.calendar = self.world.calendar
            self.end_date_obj.save()
        return self.end_date_obj

    @end_date.setter
    def end_date(self, date):
        if isinstance(date, Date):
            self.end_date_obj = date
        elif isinstance(date, dict):
            self.end_date_obj = Date(obj=self, calendar=self.world.calendar, **date)
            self.end_date_obj.save()
        elif isinstance(date, str):
            verify_date_format = date.split()
            if verify_date_format[0].isdigit() and verify_date_format[2].isdigit():
                date = Date.from_string(self, self.world.calendar, date)
                self.end_date_obj = date
                self.end_date_obj.save()
            else:
                raise ValueError(
                    "date must be a Date object or a string in the format: <day> <month> <year>"
                )

    @property
    def world(self):
        # IMPORTANT: this is here to register the model
        # without it, the model may not have been registered yet and it will fail
        from models.world import World

        return self.campaign.world

    ##################### INSTANCE METHODS ####################
    def delete(self):
        all(e.delete() for e in self.scenenotes)
        return super().delete()

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
        scenenote.actors += self.players
        scenenote.save()
        self.scenenotes += [scenenote]
        self.save()
        return scenenote

    def generate_gn(self):
        for scene in self.scenenotes:
            scene.generate_image()

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
        document.pre_save_dates()
        document.pre_save_outline()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify methods ##################
    def pre_save_campaign(self):
        if self not in self.campaign.episodes:
            self.campaign.episodes += [self]
            if self.pk:
                self.campaign.save()

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

    def pre_save_dates(self):
        if self.end_date_obj and self.end_date_obj > self.world.current_date:
            self.world.current_date = self.end_date_obj
            self.world.save()

    def pre_save_outline(self):
        # if not isinstance(self.outline, str):
        #     self.outline = ""
        #     log("Outline is not a string. FIXED.")
        pass
