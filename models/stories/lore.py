import random

import markdown
import validators
from autonomous.model.autoattr import ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel

from autonomous import log
from models.calendar.date import Date
from models.images.image import Image


class Lore(AutoModel):
    name = StringAttr(default="")
    scope = StringAttr(default="Local", choices=["Local", "Regional", "Global", "Epic"])
    summary = StringAttr(default="")
    backstory = StringAttr(default="")
    situation = StringAttr(default="")
    potential_events = ListAttr(StringAttr(default=""))
    start_date = ReferenceAttr(choices=["Date"])
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    party = ListAttr(ReferenceAttr(choices=["Character"]))
    story = ReferenceAttr(choices=["Story"])
    world = ReferenceAttr(choices=["World"], required=True)

    funcobj = {
        "name": "generate_story",
        "description": "creates a compelling narrative consistent with the described world for the players to engage with, explore, and advance in creative and unexpected ways.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "A summary of all of the lore details.",
                },
                "backstory": {
                    "type": "string",
                    "description": "A detailed description of the entire backstory leading up to the current situation.",
                },
                "situation": {
                    "type": "string",
                    "description": "A description of the current situation the main characters find themselves in and its effects on the TTRPG world. This should be a specific, concrete situation that the players can engage with and explore.",
                },
                "potential_events": {
                    "type": "array",
                    "description": "A list of potential events related to the story and involving the main characters that could have far-reaching consequences.",
                    "items": {"type": "string"},
                },
            },
        },
    }

    @property
    def calendar(self):
        return self.world.calendar

    @property
    def bbeg(self):
        return self.story.bbeg if self.story else None

    ############# CRUD #############

    def delete(self):
        if self.start_date:
            self.start_date.delete()
        super().delete()

    ############# image generation #############
    def generate(self, lore_prompt):
        prompt = f"Your task is to create expanded lore for a {self.world.genre} TTRPG world. The expanded lore should incorporate the listed world elements and relationships. Here is some context about the world: {self.world.name}, {self.world.history}. "

        if self.start_date:
            prompt += "\n\nThe Lore has the following dates: "
            if self.start_date:
                prompt += f"\n\nThe lore starts on {self.start_date}, with he following notable events happening recently: "
                for event in self.story.events:
                    if (
                        event.end_date
                        and self.start_date.year - 20
                        < event.end_date.year
                        < self.start_date.year
                    ):
                        if not event.summary:
                            event.summarize()
                        prompt += f"\n\n{event.name}: {event.summary}. "
        if self.story:
            prompt += f"\n\nThe lore is part of the following storylines: \n{self.story.name}: {self.story.summary or self.story.backstory}. "

        if self.party:
            prompt += "\n\nThe lore involves the following main characters: "
            for member in self.party:
                prompt += f"\n\n{member.name}: {member.history}. "

        if self.associations:
            prompt += "\n\nHere are some existing elements related to this lore: "
            for assoc in self.associations:
                if assoc not in self.party:
                    prompt += f"\n\n{assoc.name}: {assoc.history}."

        if self.summary:
            prompt += (
                f"\n\nThe lore currently has the following summary: {self.summary}. "
            )

        prompt += (
            f"\n\nUse the following prompt to guide the expanded lore: {lore_prompt}. "
        )

        log("Generating Expanded Lore with prompt: " + prompt, __print=True)
        result = self.world.system.generate_json(
            prompt=prompt,
            primer=f"Create expanded lore that fits into the described world. Respond in JSON format consistent with this structure: {self.funcobj['parameters']}.",
            funcobj=self.funcobj,
        )
        if result:
            log(f"Generated Lore: {result}", __print=True)
            for k, v in result.items():
                if isinstance(v, str) and "#" in v:
                    result[k] = self.system.htmlize(v)
                setattr(self, k, result[k])
            self.save()
        else:
            log("Failed to generate Lore", __print=True)

    ############# Association Methods #############
    # MARK: Associations
    def add_association(self, obj):
        # log(len(self.associations), obj in self.associations)
        if obj not in self.associations:
            self.associations += [obj]
            self.save()
        return obj

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                   ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_associations()
        document.pre_save_dates()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    def pre_save_associations(self):
        self.associations = sorted(
            set(self.associations),
            key=lambda a: (a.model_name(), getattr(a, "name", "")),
        )

    def pre_save_dates(self):
        log(self.pk)
        if self.pk:
            if isinstance(self.start_date, dict):
                if dates := Date.search(obj=self, calendar=self.calendar):
                    while len(dates):
                        dates[-1].delete()
                        dates.pop()
                start_date = Date(obj=self, calendar=self.calendar, **self.start_date)
                start_date.month = (
                    self.calendar.months.index(start_date.month.title())
                    if start_date.month
                    else random.randrange(len(self.calendar.months))
                )
                start_date.day = (
                    int(start_date.day) if start_date.day else random.randint(1, 28)
                )
                start_date.year = int(start_date.year) if start_date.year else -1
                self.start_date = start_date
            elif not self.start_date:
                self.start_date = Date(
                    obj=self,
                    calendar=self.calendar,
                    day=random.randint(1, 28),
                    month=random.randrange(len(self.calendar.months) or 12),
                    year=0,
                )
            self.start_date.save()

            if self.start_date and self.start_date.day <= 0:
                self.start_date.day = random.randint(1, 28)
            if self.start_date and self.start_date.month < 0:
                self.start_date.month = random.randint(0, 11)
