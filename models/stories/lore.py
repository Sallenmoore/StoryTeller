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
    start_date = ReferenceAttr(choices=["Date"])
    end_date = ReferenceAttr(choices=["Date"])
    image = ReferenceAttr(choices=[Image])
    desc = StringAttr(default="")
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    party = ListAttr(ReferenceAttr(choices=["Character"]))
    story = ListAttr(ReferenceAttr(choices=["Story"]))
    inciting_event = ReferenceAttr(choices=["Event"])
    world = ReferenceAttr(choices=["World"], required=True)

    @property
    def calendar(self):
        return self.world.calendar

    @property
    def description(self):
        return self.desc

    @description.setter
    def description(self, value):
        self.desc = value

    ############# CRUD #############

    def delete(self):
        if self.image:
            if self in self.image.associations:
                self.image.associations.remove(self)
                self.image.save()
            if len(self.image.associations) == 0:
                self.image.delete()
        if self.start_date:
            self.start_date.delete()
        if self.end_date:
            self.end_date.delete()
        super().delete()

    ############# image generation #############
    def generate(self):
        prompt = f"Your task is to create a new event for a {self.world.genre} TTRPG world. The event should incorporate the listed world elements and relationships. Here is some context about the world: {self.world.name}, {self.world.history}. "

        if self.start_date or self.end_date:
            prompt += "\n\nThe event has the following dates: "
            if self.start_date:
                prompt += f"\n\nThe event starts on {self.start_date}. "
            if self.end_date:
                prompt += f"\n\nThe event ends on {self.end_date}. "
        if self.stories:
            prompt += "\n\nThe event is part of the following storylines: "
            for story in self.stories:
                prompt += f"\n\n{story.name}: {story.summary or story.backstory}. "

        if self.associations:
            prompt += "\n\nHere are some existing elements related to this event: "
            for assoc in self.associations:
                prompt += f"\n\n{assoc.name}: {assoc.history}. "

        if self.impact or self.backstory or self.outcome:
            prompt += f"\n\nUse the following prompt to create the event: {self.backstory} {self.outcome} {self.impact}. "

        log("Generating Event with prompt: " + prompt, __print=True)
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
            result.get("outcome") and setattr(self, "outcome", result.get("outcome"))
            result.get("impact") and setattr(self, "impact", result.get("impact"))
            result.get("desc") and setattr(self, "desc", result.get("desc"))
            log(f"Generated Event: {self.name}", __print=True)
            self.save()
        else:
            log("Failed to generate Event", __print=True)
        if not self.image and self.desc:
            self.generate_image()

    def generate_image(self):
        if self.image:
            if self in self.image.associations:
                self.image.associations.remove(self)
                self.image.save()
            if len(self.image.associations) == 0:
                self.image.delete()
            self.image = None
        if image := Image.generate(
            prompt=self.desc, tags=["event", self.world.name, str(self.world.pk)]
        ):
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
        self.summary = self.summary.replace("```markdown", "").replace("```", "")
        self.summary = (
            markdown.markdown(self.summary)
            .replace("h1>", "h3>")
            .replace("h2>", "h3>")
            .replace("h3>", "h4>")
            .replace("h4>", "h5>")
        )
        self.save()

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
        document.pre_save_image()

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
        if self.pk and self.calendar:
            if isinstance(self.start_date, dict):
                if dates := Date.search(obj=self, calendar=self.calendar):
                    while len(dates):
                        dates[-1].delete()
                        dates.pop()
                start_date = Date(obj=self, calendar=self.calendar)
                start_date.day, start_date.month, start_date.year = (
                    self.start_date["day"],
                    self.start_date["month"],
                    self.start_date["year"],
                )
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
                end_date.month = (
                    self.calendar.months.index(end_date.month.title())
                    if end_date.month
                    else random.randrange(len(self.calendar.months))
                )
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

        if self.start_date and self.start_date.day <= 0:
            self.start_date.day = random.randint(1, 28)
        if self.start_date and self.start_date.month <= 0:
            self.start_date.month = random.randint(1, 12)
        if self.end_date and self.end_date.day <= 0:
            self.end_date.day = random.randint(1, 28)
        if self.end_date and self.end_date.month <= 0:
            self.end_date.month = random.randint(1, 12)

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

        if self.image and self not in self.image.associations:
            self.image.associations += [self]
            self.image.save()
