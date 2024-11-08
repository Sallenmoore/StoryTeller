import json
import random
import re

import markdown

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    BoolAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.abstracts.place import Scene
from models.abstracts.ttrpgbase import TTRPGBase
from models.character import Character
from models.events.event import Event
from models.images.image import Image
from models.location import Location
from models.poi import POI


class Session(AutoModel):
    name = StringAttr(default="")
    episode_num = IntAttr(default=0)
    description = StringAttr(default="")
    start_date = ReferenceAttr(choices=[Event])
    end_date = ReferenceAttr(choices=[Event])
    campaign = ReferenceAttr(choices=["Campaign"], required=True)
    show = ReferenceAttr(choices=[TTRPGBase])
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    session_report = StringAttr(default="")
    current_scene = ReferenceAttr(choices=[Scene])
    summary = StringAttr(default="")
    comic = ReferenceAttr(choices=[Image])
    comic_prompt = StringAttr(default="")
    last_roll = StringAttr(default="")
    last_roll_result = IntAttr(default=0)
    is_updated = BoolAttr(default=False)

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
    def pois(self):
        return [a for a in self.associations if a.model_name() == "POI"]

    @property
    def players(self):
        return [
            a
            for a in self.associations
            if a.model_name() == "Character" and a.is_player
        ]

    @property
    def locations(self):
        return [a for a in self.associations if a.model_name() == "Location"]

    @property
    def cities(self):
        return [a for a in self.associations if a.model_name() == "City"]

    @property
    def regions(self):
        return [a for a in self.associations if a.model_name() == "Region"]

    @property
    def scenes(self):
        return [a for a in self.associations if a.model_name() in ["Location", "POI"]]

    @property
    def calendar(self):
        return self.world.calendar

    @property
    def events(self):
        events = []
        if (
            self.start_date
            and self.end_date
            and self.start_date.year
            and self.end_date.year
        ):
            for obj in self.associations:
                if (
                    obj.end_date
                    and obj.end_date.year
                    and obj.end_date not in events
                    and self.start_date <= obj.end_date <= self.end_date
                ):
                    events += [obj.end_date]
                    if not obj.end_date.episode:
                        obj.end_date.episode = self
                        obj.end_date.save()
                if (
                    obj.start_date
                    and obj.start_date.year
                    and obj.start_date not in events
                    and self.start_date <= obj.start_date <= self.end_date
                ):
                    if self.start_date <= obj.start_date <= self.end_date:
                        events += [obj.start_date]
                        if not obj.start_date.episode:
                            obj.start_date.episode = self
                            obj.start_date.save()
                for event in obj.events:
                    if (
                        event.year
                        and event not in events
                        and self.start_date <= event <= self.end_date
                    ):
                        events += [event]
                        if not event.episode:
                            event.episode = self
                            event.save()
        return events

    @property
    def free_characters(self):
        characters = Character.search(world=self.world)
        log(characters)
        return [c for c in characters if c.canon]

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
                self.session_report,
                primer="Generate a summary of less than 100 words of the episode events in MARKDOWN format with a paragraph breaks where appropriate, but after no more than 4 sentences.",
            )
            if len(self.session_report) > 256
            else self.session_report
        )
        self.summary = self.summary.replace("```markdown", "").replace("```", "")
        self.summary = (
            markdown.markdown(self.summary).replace("h1>", "h3>").replace("h2>", "h3>")
        )
        self.save()
        return self.summary

    def get_scene(self, pk):
        return Location.get(pk) or POI.get(pk)

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
        self.associations = [a for a in self.associations if a.pk != obj.pk]
        self.save()

    def generate_scene(self):
        comic_prompt = """Rewrite the following episode summary information as markdown and optimized for generating a 6 scene comic book panel using Dall-E. Use vivid and detailed language by incorporating the provided descriptions to produce consistent character and location images for each panel.

        Provide a description for each of the following 6 panels: Top-Left, Top-Right, Mid-Left, Mid-Right, Bottom-Left, Bottom-Right

        """

        comic_prompt += """
Character Descriptions:
        """
        for ass in self.characters:
            if not ass.description_summary:
                ass.resummarize()
            comic_prompt += f"""
  - {ass.name}: {ass.description_summary}
                """

        comic_prompt += """
Location Descriptions:
        """
        for ass in self.scenes:
            if not ass.description_summary:
                ass.resummarize()
            comic_prompt += f"""
  - {ass.name}: {ass.description_summary}
"""

        comic_prompt += f"""
Events:
{self.summary or self.session_report}
"""
        scene_text = self.world.system.generate_text(
            comic_prompt,
            primer="As an expert AI assitant in writing detailed descriptions that are optimized for generating a series of images with consistent character and locations using Dall-E, generate a vivid description for a 6 scene comic book panel.",
        )

        result = markdown.markdown(scene_text.strip())
        self.comic_prompt = f"""
        A photogrid of an adventuring party consisting of the following characters:
        {"- ".join([f"{c.name} [{c.gender} {c.race}]: {c.description_summary}\n\n" for c in self.characters])}

        {result}
        """
        self.save()

    def generate_comic(self):
        if self.comic:
            self.comic.delete()
        log("=========> prompt length", len(self.comic_prompt))
        if 80 < len(self.comic_prompt) < 3900:
            prompt = f"""
            Based on the following description of the events and elements of a TTRPG {self.campaign.world.genre} Session, generate a 6 panel photogrid in a comic book style using consistent character and location represenations across each panel.

            {self.comic_prompt}
            """
            if panel := Image.generate(
                prompt,
                tags=["comic-panel", "episode"],
                text=True,
            ):
                panel.save()
                self.comic = panel
                self.save()
        return self.comic

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
        document.pre_save_campaign()
        document.pre_save_associations()
        document.pre_save_dates()
        document.pre_save_current_scene()
        document.pre_save_comic()
        document.pre_save_episode_num()

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)
        document.post_save_dates()

    # def clean(self):
    #     super().clean()

    ################### verify startdate ##################
    def pre_save_campaign(self):
        if self not in self.campaign.episodes:
            self.campaign.episodes += [self]

    def pre_save_associations(self):
        for a in self.associations:
            pass  # ??? - why does this fix the issue?
            # log(a)

    def pre_save_dates(self):
        if (
            self.pk
            and isinstance(self.start_date, dict)
            and all(
                (
                    "day" in self.start_date,
                    "month" in self.start_date,
                    "year" in self.start_date,
                )
            )
        ):
            for e in Event.search(obj=self, name="Began"):
                e.delete()
            start_date = Event(obj=self, name="Began")
            start_date.day = int(self.start_date["day"] or random.randint(1, 30))
            start_date.month = int(self.start_date["month"] or random.randint(0, 12))
            start_date.year = int(self.start_date["year"] or 0)
            start_date.save()
            self.start_date = start_date

        if (
            self.pk
            and isinstance(self.end_date, dict)
            and all(
                (
                    "day" in self.start_date,
                    "month" in self.start_date,
                    "year" in self.start_date,
                )
            )
        ):
            for e in Event.search(obj=self, name="Ended"):
                e.delete()
            end_date = Event(obj=self, name="Ended")
            end_date.day = int(self.end_date["day"] or random.randint(1, 30))
            end_date.month = int(self.end_date["month"] or random.randint(0, 12))
            end_date.year = int(self.end_date["year"] or 0)
            end_date.save()
            self.end_date = end_date
        if (
            self.start_date
            and self.end_date
            and self.end_date.year < self.start_date.year
        ):
            self.end_date.year = self.start_date.year + 1

        if (
            self.start_date
            and self.end_date
            and self.start_date.year > self.end_date.year
        ):
            self.start_date.year = self.end_date.year

    ################### verify current_scene ##################
    def pre_save_current_scene(self):
        if not self.current_scene and self.scenes:
            self.current_scene = self.scenes[0]

    ################### verify associations ##################
    def pre_save_comic(self):
        if not self.comic_prompt:
            self.comic_prompt = ""
        if self.comic_prompt and isinstance(self.comic_prompt, list):
            self.comic_prompt = "\n\n".join(self.comic_prompt)
        if self.comic and isinstance(self.comic, list):
            self.comic = self.comic[0]

    ################### verify summary ##################
    def post_save_dates(self):
        if not self.start_date:
            self.start_date = Event(obj=self, name="Began")
            self.start_date.save()
            self.save()
        if (
            not self.start_date.year
            and self.campaign.episodes
            and self != self.campaign.episodes[-1]
        ):
            index = self.campaign.episodes.index(self)
            prev_episode = self.campaign.episodes[index + 1]
            if prev_episode.end_date and prev_episode.end_date.year:
                self.start_date.year = prev_episode.end_date.year
                self.start_date.month = prev_episode.end_date.month
                self.start_date.day = prev_episode.end_date.day
            self.start_date.save()

    def pre_save_episode_num(self):
        if not self.episode_num:
            num = re.search(r"\b\d+\b", self.name).group(0)
            if num.isdigit():
                self.episode_num = int(num)
