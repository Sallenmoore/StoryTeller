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
from models.audio.audio import Audio
from models.base.ttrpgbase import TTRPGBase
from models.calendar.date import Date
from models.images.image import Image
from models.stories.event import Event
from models.ttrpgobject.character import Character
from models.ttrpgobject.district import District
from models.ttrpgobject.location import Location
from models.utility.parse_attributes import parse_text


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
    stories = ListAttr(ReferenceAttr(choices=["Story"]))
    audio = ReferenceAttr(choices=["Audio"])
    transcription = StringAttr(default="")

    ##################### PROPERTY METHODS ####################

    @property
    def actors(self):
        return [*self.characters, *self.creatures]

    @property
    def characters(self):
        return [a for a in self.associations if a.model_name() == "Character"]

    @property
    def children(self):
        return self.associations

    @property
    def creatures(self):
        return [a for a in self.associations if a.model_name() == "Creature"]

    @property
    def events(self):
        return [e for e in Event.search(world=self.world) if self in e.episodes]

    @property
    def encounters(self):
        encs = []
        for p in self.places:
            encs += p.encounters
        return encs

    @property
    def factions(self):
        return [a for a in self.associations if a.model_name() == "Faction"]

    @property
    def genre(self):
        return self.world.genre

    @property
    def geneology(self):
        return [self.campaign, self.world]

    @property
    def items(self):
        return [a for a in self.associations if a.model_name() == "Item"]

    @property
    def image(self):
        return self.graphic

    @property
    def districts(self):
        return [a for a in self.associations if a.model_name() == "District"]

    @property
    def players(self):
        return [a for a in self.characters if a.is_player]

    @property
    def party(self):
        return self.campaign.party

    @property
    def locations(self):
        return [a for a in self.associations if a.model_name() == "Location"]

    @property
    def cities(self):
        return [a for a in self.associations if a.model_name() == "City"]

    @property
    def next_episode(self):
        for ep in self.campaign.episodes:
            if ep.episode_num == self.episode_num + 1:
                return ep
        return None

    @property
    def path(self):
        return f"episode/{self.pk}"

    @property
    def places(self):
        return [
            *self.locations,
            *self.districts,
            *self.vehicles,
            *self.cities,
            *self.regions,
            *self.shops,
        ]

    @property
    def previous_episode(self):
        for ep in self.campaign.episodes:
            if ep.episode_num == self.episode_num - 1:
                return ep
        return None

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
    def start_date(self):
        return self.start_date_obj

    @start_date.setter
    def start_date(self, value):
        if isinstance(value, Date):
            if value != self.start_date_obj:
                if self.start_date_obj:
                    self.start_date_obj.delete()
                self.start_date_obj = value
        elif not value:
            self.start_date_obj = None
            return
        elif isinstance(value, dict):
            if self.start_date_obj:
                self.start_date_obj.delete()
            self.start_date_obj = Date(obj=self, calendar=self.world.calendar, **value)
        else:
            log(f"Invalid start_date value: {value}")
            raise ValueError("start_date must be a Date instance or dict")
        self.start_date_obj.save()

    @property
    def end_date(self):
        return self.end_date_obj

    @end_date.setter
    def end_date(self, value):
        if isinstance(value, Date):
            if value != self.end_date_obj:
                if self.end_date_obj:
                    self.end_date_obj.delete()
                self.end_date_obj = value
        elif isinstance(value, dict):
            if self.end_date_obj:
                self.end_date_obj.delete()
            self.end_date_obj = Date(obj=self, calendar=self.world.calendar, **value)
        elif not value:
            self.end_date_obj = None
            return
        else:
            log(f"Invalid start_date value: {value}")
            raise ValueError("start_date must be a Date instance or dict")
        self.end_date_obj.save()

    @property
    def world(self):
        return self.campaign.world if self.campaign else None

    ##################### CRUD METHODS ####################
    def delete(self):
        if self.start_date_obj:
            self.start_date_obj.delete()
        if self.end_date_obj:
            self.end_date_obj.delete()
        if self.audio:
            self.audio.delete()
        if self.graphic:
            self.graphic.delete()
        return super().delete()

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

    def summarize_transcription(self):
        if self.transcription:
            # Remove all lines starting with "TRANSCRIPTION:"
            self.transcription = "\n".join(
                [
                    line.strip()
                    for line in self.transcription.split("\n")
                    if line.strip() and not line.strip().startswith("TRANSCRIPTION:")
                ]
            )
            prompt = f"Summarize the following transcription of a TTRPG session for a {self.world.genre} world using a snarky and observational tone. The summary should be concise and engaging, highlighting the key elements of the transcription and its significance within the larger story, while leaving out any irrelevant remarks or conversation,  . Here is some context about the world: {self.world.name}, {self.world.history}. Here is some context about the campaign: {self.campaign.name}, {self.campaign.summary}. Here is the transcription: {self.transcription}."
            transcription_summary = self.world.system.generate_summary(
                prompt,
                primer="Provide an engaging, narrative summary of the transcription, highlighting its key elements and significance within the larger story.",
            )

            transcription_summary = transcription_summary.replace(
                "```markdown", ""
            ).replace("```", "")
            transcription_summary = (
                markdown.markdown(transcription_summary)
                .replace("h1>", "h3>")
                .replace("h2>", "h3>")
            )
            self.episode_report = f"## Transcription Summary <br><br> {transcription_summary} {f'<br><br> === Previous Notes === <br><br>{self.episode_report}' if self.episode_report else ''}"
            self.save()
        return self.episode_report

    def regenerate_report(self):
        if not self.episode_report:
            return ""
        prompt = f"Rewrite and expand on the following session notes for a {self.world.genre} TTRPG in MARKDOWN to be an engaging and exciting narrative, highlighting the key elements of the session and its significance within the larger story. Here is some context about the world: {self.world.name}, {self.world.history}. Here is some context about the campaign: {self.campaign.name}, {self.campaign.summary}."

        if self.stories:
            prompt += "\n\nHere is some context about the story arcs involved in the episode:\n\n"
            for s in self.stories:
                if not s.summary:
                    s.summarize()
                prompt += f"\n\n{s.name}:{s.summary}."

        if self.associations:
            prompt += "\n\nHere are descriptions of world elements involved in the episode:\n\n"
            for assoc in self.associations:
                if assoc.history:
                    prompt += f"\n\n{assoc.name}: {assoc.history}."

        prompt += f"\n\nHere are the current session notes: {self.episode_report}."
        self.episode_report = self.world.system.generate_text(
            prompt,
            primer=f"Rewrite the following session notes in MARKDOWN for a {self.world.genre} TTRPG world in a narrative, evocative, and vivid style using a witty and judgemental narrator tone.",
        )

        self.episode_report = self.episode_report.replace("```markdown", "").replace(
            "```", ""
        )
        self.episode_report = (
            markdown.markdown(self.episode_report)
            .replace("h1>", "h3>")
            .replace("h2>", "h3>")
        )
        self.save()
        return self.episode_report

    def generate_graphic(self):
        prompt = f"Create a detailed description of a paneled graphic novel page for an AI-generated image that captures the essence of the following episode in a {self.world.genre} TTRPG world. The description for each panel should include key visual elements, atmosphere, and any significant characters or locations featured in the episode. Here is some context about the world: {self.world.name}, {self.world.history}. Here is some context about the campaign: {self.campaign.name}, {self.campaign.summary}. Here is the episode name and summary: {self.name}, {self.summary if self.summary else self.episode_report}. "
        log(f"Graphic Prompt: {prompt}", _print=True)
        description = self.world.system.generate_text(
            prompt,
            primer="Provide a vivid and detailed description for an AI-generated image that captures the essence of the episode, including key visual elements, atmosphere, and significant characters or locations.",
        )
        description = description.replace("```markdown", "").replace("```", "")
        description += f"\n\nArt Style: Comic Book, Graphic Novel, Illustrated\n\n Use the attached image files as a reference for character appearances.\n\nMain character descriptions:\n\n{'\n\n'.join([f'{c.name}: ({c.lookalike}){c.description}' for c in self.players])}."
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

    def add_event(self, event):
        if not event:
            raise ValueError("event must be a valid object")
        log(self not in event.episodes)
        if self not in event.episodes:
            event.episodes += [self]
            event.save()
        return event

    def remove_association(self, obj):
        self.associations = [a for a in self.associations if a != obj]
        self.save()

    def page_data(self):
        data = {
            "pk": str(self.pk),
            "name": self.name,
            "associations": [(a.model_name(), str(a.pk)) for a in self.associations],
            "episode_report": self.episode_report,
            "loot": self.loot,
            "hooks": self.hooks,
        }
        return data

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
        document.pre_save_report()
        document.pre_save_description()

        ##### MIGRATION: Encounters #######
        document.associations = [
            a for a in document.associations if a.model_name() != "Encounter"
        ]

        #########################################

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify methods ##################
    def pre_save_campaign(self):
        if self.pk and self not in self.campaign.episodes:
            self.campaign.episodes += [self]
            self.campaign.save()

    def pre_save_associations(self):
        self.associations = list(set([a for a in self.associations if a]))
        self.associations.sort(key=lambda x: (x.model_name(), x.name))

    ################### verify current_scene ##################
    def pre_save_episode_num(self):
        if not self.episode_num:
            if num_group := re.search(r"\b\d+\b", self.name):
                num = num_group.group(0)
                if num.isdigit():
                    self.episode_num = int(num)

    def pre_save_dates(self):
        if not self.world.current_date:
            self.world.current_date = self.end_date_obj
            self.world.save()
        elif self.end_date_obj and self.world.current_date < self.end_date_obj:
            self.world.current_date = self.end_date_obj
            self.world.save()

    def pre_save_report(self):
        """
        Checks for a full name (obj.name) in a block of text and replaces it
        with a link, while respecting existing anchor tags.

        Args:
            text (str): The block of text to search and modify.
            obj (object): An object with 'name' and 'path' attributes
                        (e.g., Character, City, etc.).

        Returns:
            str: The modified text with the name parts linked.
        """
        if self.episode_report:
            self.episode_report = parse_text(self, self.episode_report)

    def pre_save_description(self):
        """
        Checks for a full name (obj.name) in a block of text and replaces it
        with a link, while respecting existing anchor tags.

        Args:
            text (str): The block of text to search and modify.
            obj (object): An object with 'name' and 'path' attributes
                        (e.g., Character, City, etc.).

        Returns:
            str: The modified text with the name parts linked.
        """
        if self.description:
            self.description = parse_text(self, self.description)
