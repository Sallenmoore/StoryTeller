import json
import os
import random
import re

import markdown
import requests
from autonomous.model.autoattr import (
    DictAttr,
    FileAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from bs4 import BeautifulSoup

from autonomous import log
from models.base.ttrpgbase import TTRPGBase
from models.calendar.date import Date
from models.images.image import Image
from models.ttrpgobject.character import Character
from models.ttrpgobject.district import District
from models.ttrpgobject.location import Location


class Episode(AutoModel):
    name = StringAttr(default="")
    episode_num = IntAttr(default=0)
    description = StringAttr(default="")
    start_date_obj = ReferenceAttr(choices=["Date"])
    end_date_obj = ReferenceAttr(choices=["Date"])
    campaign = ReferenceAttr(choices=["Campaign"], required=True)
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    graphic = ReferenceAttr(choices=["Image"])
    episode_report = StringAttr(default="")
    loot = StringAttr(default="")
    hooks = StringAttr(default="")
    summary = StringAttr(default="")
    story = ReferenceAttr(choices=["Story"])

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
    def path(self):
        return f"episode/{self.pk}"

    @property
    def places(self):
        return [a for a in [*self.scenes, *self.cities, *self.regions]]

    @property
    def regions(self):
        return [a for a in self.associations if a.model_name() == "Region"]

    @property
    def report(self):
        return self.episode_report

    @report.setter
    def report(self, value):
        self.episode_report = value

    @property
    def shops(self):
        return [a for a in self.associations if a.model_name() == "Shop"]

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
        return self.start_date_obj

    @start_date.setter
    def start_date(self, value):
        if self.start_date_obj:
            self.start_date_obj.delete()
            self.start_date_obj = None
        if not value:
            self.start_date_obj = None
            return
        if isinstance(value, dict):
            self.start_date_obj = Date(obj=self, calendar=self.world.calendar, **value)
        elif isinstance(value, Date):
            self.start_date_obj = value
        else:
            log(f"Invalid start_date value: {value}")
            raise ValueError("start_date must be a Date instance or dict")
        self.start_date_obj.save()

    @property
    def end_date(self):
        return self.end_date_obj

    @end_date.setter
    def end_date(self, value):
        if self.end_date_obj:
            self.end_date_obj.delete()
            self.end_date_obj = None
        if not value:
            self.end_date_obj = None
            return
        if isinstance(value, dict):
            self.end_date_obj = Date(obj=self, calendar=self.world.calendar, **value)
        elif isinstance(value, Date):
            self.end_date_obj = value
        else:
            log(f"Invalid end_date value: {value}")
            raise ValueError("end_date must be a Date instance or dict")
        self.end_date_obj.save()

    @property
    def world(self):
        return self.campaign.world if self.campaign else None

    ##################### INSTANCE METHODS ####################

    def resummarize(self):
        if not self.episode_report:
            return ""
        prompt = f"Summarize the following episode report for a {self.world.genre} TTRPG world. The summary should be concise and engaging, highlighting the key elements of the episode and its significance within the larger story. Here is some context about the world: {self.world.name}, {self.world.history}. Here is some context about the campaign: {self.campaign.name}, {self.campaign.summary}. Here is the episode report: {self.episode_report}."
        self.summary = self.world.system.generate_summary(
            prompt,
            primer="Provide an engaging, narrative summary of the episode, highlighting its key elements and significance within the larger story.",
        )

        self.summary = self.summary.replace("```markdown", "").replace("```", "")
        self.summary = (
            markdown.markdown(self.summary).replace("h1>", "h3>").replace("h2>", "h3>")
        )
        self.save()
        return self.summary

    def generate_graphic(self):
        prompt = f"Create a detailed description of a paneled graphic novel page for an AI-generated image that captures the essence of the following episode in a {self.world.genre} TTRPG world. The description for each panel should include key visual elements, atmosphere, and any significant characters or locations featured in the episode. Here is some context about the world: {self.world.name}, {self.world.history}. Here is some context about the campaign: {self.campaign.name}, {self.campaign.summary}. Here is the episode name and summary: {self.name}, {self.summary if self.summary else self.episode_report}. "
        description = self.world.system.generate_summary(
            prompt,
            primer="Provide a vivid and detailed description for an AI-generated image that captures the essence of the episode, including key visual elements, atmosphere, and significant characters or locations.",
        )
        description = description.replace("```markdown", "").replace("```", "")
        description += f"\n\nArt Style: Comic Book, Graphic Novel, Illustrated\n\n Use the attached image files as a reference for character appearances.\n\nMain character descriptions:\n\n{'\n\n'.join([f'{c.name}: ({c.lookalike}){c.description_summary}' for c in self.players])}."
        log(f"Graphic Description: {description}", _print=True)
        party = [c.image for c in self.players if c.image]
        if image := Image.generate(
            prompt=description, tags=["episode", "graphic"], files=party
        ):
            if self.graphic:
                self.graphic.delete()
            self.graphic = image
            self.graphic.associations += [self]
            self.graphic.save()
            self.save()
        else:
            log("Image generation failed.", _print=True)
        return self.graphic

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
        document.pre_save_dates()

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

    def pre_save_dates(self):
        if self.end_date_obj:
            self.world.current_date = self.end_date_obj
            self.world.save()
