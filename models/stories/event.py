import random

import markdown
import validators
from autonomous.model.autoattr import ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from bs4 import BeautifulSoup

from autonomous import log
from models.calendar.date import Date
from models.images.image import Image
from models.utility import parse_attributes


class Event(AutoModel):
    name = StringAttr(default="")
    scope = StringAttr(default="Local", choices=["Local", "Regional", "Global", "Epic"])
    summary = StringAttr(default="")
    impact = StringAttr(default="")
    backstory = StringAttr(default="")
    outcome = StringAttr(default="")
    start_date = ReferenceAttr(choices=["Date"])
    end_date = ReferenceAttr(choices=["Date"])
    image = ReferenceAttr(choices=[Image])
    desc = StringAttr(default="")
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    stories = ListAttr(ReferenceAttr(choices=["Story"]))
    episodes = ListAttr(ReferenceAttr(choices=["Episode"]))
    world = ReferenceAttr(choices=["World"], required=True)

    funcobj = {
        "name": "generate_event",
        "description": "creates the description and details surrounding an event that occured.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A name for the event.",
                },
                "summary": {
                    "type": "string",
                    "description": "A brief summary of the event.",
                },
                "scope": {
                    "type": "string",
                    "description": "The scope of the story and how it fits into the larger world. One of the following: 'Local', 'Regional', 'Global', or 'Epic'",
                },
                "impact": {
                    "type": "string",
                    "description": "The overall impact the event had on the world. This should be a brief summary of the consequences of the event.",
                },
                "backstory": {
                    "type": "string",
                    "description": "A detailed description of the backstory leading up to the event.",
                },
                "outcome": {
                    "type": "string",
                    "description": "A description of the actual the event.",
                },
                "desc": {
                    "type": "string",
                    "description": "A prompt with the physical description of the event that could be used to generate an image with AI",
                },
            },
        },
    }

    @classmethod
    def create_event_from_encounter(cls, encounter):
        event = cls()
        event.name = encounter.name
        event.scope = "Local"
        event.impact = (
            f"A {encounter.enemy_type} encounter of {encounter.difficulty} difficulty."
        )
        event.backstory = encounter.backstory
        event.outcome = "\n---\n".join(encounter.post_scenes)
        event.desc = encounter.description
        event.associations = encounter.associations
        event.episodes = [
            ep for ep in encounter.parent.get_episodes() if encounter in ep.encounters
        ]
        event.story = encounter.story
        event.world = encounter.world
        if encounter.image:
            event.image = encounter.image
            encounter.image = None
            encounter.save()
        event.save()
        if start_date := encounter.world.current_date:
            event.start_date = start_date.copy(event)
            event.start_date.day -= random.randint(1, 3)
            event.end_date = start_date.copy(event)
            event.end_date.save()
        event.save()
        return event

    @classmethod
    def create_event_from_episode(cls, episode):
        event = cls(
            world=episode.world,
            name=episode.name,
            associations=episode.associations,
            story=episode.story,
            outcome=episode.episode_report,
            backstory=episode.campaign.summary,
            impact=episode.summary,
        )
        event.save()
        event.scope = "Local"
        event.start_date = episode.start_date.copy(event)
        event.end_date = episode.end_date.copy(event)
        event.episodes = [episode]
        event.save()
        return event

    @property
    def calendar(self):
        return self.world.calendar

    @property
    def description(self):
        return self.desc

    @description.setter
    def description(self, value):
        self.desc = value

    @property
    def genre(self):
        return self.world.genre

    @property
    def geneology(self):
        return [self.world]

    @property
    def path(self):
        return f"event/{self.pk}"

    @property
    def players(self):
        return [
            p
            for p in self.associations
            if p.model_name() == "Character" and p.is_player
        ]

    ############# CRUD #############

    def delete(self):
        if self.image:
            self.image.delete()
            self.image = None
        if self.start_date:
            self.start_date.delete()
        if self.end_date:
            self.end_date.delete()
        super().delete()

    ############# image generation #############
    def generate(self):
        prompt = f"""
Your task is to create a new event for a {self.world.genre} TTRPG world. The event should incorporate the listed world elements and relationships. Here is some context about the world: {self.world.name}, {self.world.backstory}.
The timeline of the world is as follows:
{"".join([f"\n\n{e.start_date} - {e.end_date}: {e.name}: {e.summary or e.backstory}." for e in self.world.events[::-1]])}
"""

        if self.start_date or self.end_date:
            prompt += "\n\nThis event has the following dates: "
            if self.start_date:
                prompt += f"\n\nThe event starts on {self.start_date}. "
            if self.end_date:
                prompt += f"\n\nThe event ends on {self.end_date}. "
        if self.stories:
            prompt += "\n\nThe event is part of the following storylines: "
            for story in self.stories:
                prompt += f"\n\n{story.name}: {story.summary or story.backstory}. "

        if self.associations:
            prompt += "\n\nHere are some world elements related to this event: "
            for assoc in self.associations:
                prompt += f"\n\n{assoc.name}: {assoc.history or assoc.backstory}. "

        if self.impact or self.backstory or self.outcome:
            prompt += f"""\n\nUse the following information to create the event:
            {f"BACKSTORY: {self.backstory}" if self.backstory else ""}
            {f"OUTCOME: {self.outcome}" if self.outcome else ""}
            {f"IMPACT: {self.impact}" if self.impact else ""}
            """

        log("Generating Event with prompt: " + prompt, _print=True)
        prompt = parse_attributes.sanitize(prompt)
        result = self.world.system.generate_json(
            prompt=prompt,
            primer=f"Create a new event that fits into the described world. Respond in JSON format consistent with this structure: {self.funcobj['parameters']}.",
            funcobj=self.funcobj,
        )
        if result:
            for k, v in result.items():
                if isinstance(v, str) and "#" in v:
                    result[k] = parse_attributes.parse_text(self, v)
                setattr(self, k, result[k])
            self.save()
        else:
            log("Failed to generate Event", _print=True)
        if not self.image and self.desc:
            self.generate_image()

    def generate_from_events(self, events):
        prompt = f"""Your task is to create a new event for a {self.world.genre} TTRPG world. The event should provide a connecting thread for the following events:

{"\n".join([f"{e.name} ({e.start_date} - {e.end_date}): {e.summary or e.backstory}" for e in events])}.

Here is some context about the world: {self.world.name}, {self.world.history}.
"""

        prompt += "\n\nThe event is part of the following storylines: "
        for e in events:
            for story in e.stories:
                prompt += f"\n\n{story.name}: {story.summary or story.backstory}."
        prompt += "\n\nThe event is related to the following world elements: "
        for e in events:
            for assoc in e.associations:
                if assoc not in self.associations:
                    prompt += f"\n\n{assoc.name}: {assoc.backstory_summary}."
                    self.add_association(assoc)

        log("Generating Event with prompt: " + prompt, _print=True)
        result = self.world.system.generate_json(
            prompt=prompt,
            primer=f"Create a new event that fits into the described world. Respond in JSON format consistent with this structure: {self.funcobj['parameters']}.",
            funcobj=self.funcobj,
        )
        if result:
            result.get("name") and setattr(self, "name", result.get("name"))
            result.get("scope") and setattr(self, "scope", result.get("scope"))
            result.get("backstory") and setattr(
                self, "backstory", result.get("backstory")
            )
            if end_date := result.get("end_date"):
                self.backstory = f"{end_date}\n\n{self.backstory}"
            if start_date := result.get("start_date"):
                self.backstory = f"{start_date}\n\n{self.backstory}"
            result.get("outcome") and setattr(self, "outcome", result.get("outcome"))
            result.get("impact") and setattr(self, "impact", result.get("impact"))
            result.get("desc") and setattr(self, "desc", result.get("desc"))
            log(f"Generated Event: {self.name}", _print=True)
            self.save()
        else:
            log("Failed to generate Event", _print=True)
        if not self.image and self.desc:
            self.generate_image()

    def generate_image(self):
        prompt = f"{self.desc}\n\nUse the attached image files as a reference for character appearances.\n\nMain character descriptions:\n\n{'\n\n'.join([f'{c.name}: {c.description}' for c in self.players])}."
        prompt = f"""{prompt}

The image should be in a {self.world.image_style} style.
"""
        party = {f"{c.name}.webp": c.image for c in self.players if c.image}
        if image := Image.generate(
            prompt=prompt,
            tags=["event", self.world.name, str(self.world.pk)],
            files=party,
        ):
            if self.image:
                self.image = self.image.delete()
            self.image = image
            self.image.save()
            self.save()
        else:
            log(self.desc, "Image generation failed.", _print=True)
        return self.image

    def get_image_list(self):
        return [i.image for i in self.associations if i.image]

    def summarize(self):
        prompt = f"Summarize the following event that occurred in a {self.world.genre} TTRPG world. The event has the following details: Backstory: {self.backstory}. Outcome: {self.outcome}. Impact: {self.impact}."
        primer = "Provide an engaging summary of the event, highlighting its key elements in less than 65 words."
        log(f"Generating summary...\n{prompt}", _print=True)
        self.summary = self.world.system.generate_summary(prompt, primer)
        self.world.set_current_date()
        self.save()

    ############# Association Methods #############
    # MARK: Associations
    def add_association(self, obj):
        # log(len(self.associations), obj in self.associations)
        if obj not in self.associations:
            self.associations += [obj]
            self.save()
        return obj

    def remove_association(self, obj):
        # log(len(self.associations), obj in self.associations)
        if obj in self.associations:
            self.associations.remove(obj)
            self.save()
        return obj

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                   ##
    ###############################################################
    @classmethod
    def auto_post_init(cls, sender, document, **kwargs):
        super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_associations()
        document.pre_save_dates()
        document.pre_save_image()

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    def pre_save_associations(self):
        self.associations = sorted(
            set(self.associations),
            key=lambda a: (a.model_name(), getattr(a, "name", "")),
        )

    def pre_save_dates(self):
        if self.pk and self.calendar:
            if isinstance(self.start_date, dict):
                if dates := Date.search(obj=self, calendar=self.calendar):
                    while len(dates):
                        dates[-1].delete()
                        dates.pop()
                start_date = Date(obj=self, calendar=self.calendar)
                start_date.day, start_date.month, start_date.year = (
                    int(self.start_date["day"]),
                    self.start_date["month"],
                    int(self.start_date["year"]),
                )
                start_date.month = self.calendar.months.index(start_date.month.title())
                start_date.day = (
                    int(start_date.day) if start_date.day else random.randint(1, 28)
                )
                start_date.year = int(start_date.year) if start_date.year else -1
                self.start_date = start_date
                log(start_date.month)
            elif not self.start_date:
                self.start_date = Date(
                    obj=self,
                    calendar=self.calendar,
                    day=random.randint(1, 28),
                    month=random.randrange(len(self.calendar.months) or 12),
                    year=0,
                )
            self.start_date.save()
            # log(self.start_date, self.end_date)

            if isinstance(self.end_date, dict):
                if dates := Date.search(obj=self, calendar=self.calendar):
                    while len(dates) - 1 > 1:
                        dates[-1].delete()
                        dates.pop()
                end_date = Date(obj=self, calendar=self.calendar)
                end_date.day, end_date.month, end_date.year = (
                    self.end_date["day"],
                    self.end_date["month"],
                    self.end_date["year"],
                )
                end_date.month = self.calendar.months.index(end_date.month.title())
                end_date.day = (
                    int(end_date.day) if end_date.day else random.randint(1, 28)
                )
                end_date.year = int(end_date.year) if end_date.year else -1
                self.end_date = end_date
            elif not self.end_date or not isinstance(self.end_date, Date):
                self.end_date = Date(
                    obj=self,
                    calendar=self.calendar,
                    day=random.randint(1, 28),
                    month=random.randrange(len(self.calendar.months) or 12),
                    year=0,
                )
            self.end_date.save()
        # log(self.start_date, self.end_date)
        if self.start_date and self.start_date.day <= 0:
            self.start_date.day = random.randint(1, 28)
        if self.start_date and self.start_date.month < 0:
            self.start_date.month = random.randint(0, 11)
        if self.end_date and self.end_date.day <= 0:
            self.end_date.day = random.randint(1, 28)
        if self.end_date and self.end_date.month < 0:
            self.end_date.month = random.randint(0, 11)
        # log(self.start_date, self.end_date)

    def pre_save_image(self):
        if isinstance(self.image, str):
            if validators.url(self.image):
                self.image = Image.from_url(
                    self.image,
                    prompt=self.image_prompt,
                    tags=[*self.image_tags],
                )
                self.image.save()
            elif image := Image.get(self.image):
                self.image = image
            else:
                raise validators.ValidationError(
                    f"Image must be an Image object, url, or Image pk, not {self.image}"
                )
        elif self.image and not self.image.tags:
            self.image.tags = self.image_tags
            self.image.save()
