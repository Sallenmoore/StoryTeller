import random

from autonomous import log
from autonomous.model.autoattr import ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.calendar.date import Date
from models.images.image import Image


class Event(AutoModel):
    name = StringAttr(default="")
    scope = StringAttr(default="Local", choices=["Local", "Regional", "Global", "Epic"])
    impact = StringAttr(default="")
    backstory = StringAttr(default="")
    outcome = StringAttr(default="")
    start_date = ReferenceAttr(choices=["Date"])
    end_date = ReferenceAttr(choices=["Date"])
    image = ReferenceAttr(choices=[Image])
    desc = StringAttr(default="")
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    episode = ReferenceAttr(choices=["Episode"])
    story = ReferenceAttr(choices=["Story"])
    world = ReferenceAttr(choices=["World"], required=True)

    @classmethod
    def create_event_from_encounter(cls, encounter):
        event = cls()
        event.name = encounter.name
        event.scope = "Local"
        event.impact = (
            f"A {encounter.enemy_type} encounter of {encounter.difficulty} difficulty."
        )
        event.backstory = encounter.backstory
        event.outcome = ";----;".join(encounter.potential_outcomes)
        event.impact = encounter.history
        event.start_date = encounter.start_date
        event.end_date = encounter.end_date
        event.desc = encounter.description
        event.associations = encounter.associations
        event.episode = encounter.episodes[0] if encounter.episodes else None
        event.story = encounter.story
        event.world = encounter.world
        event.save()
        return event

    @classmethod
    def create_event_from_episode(cls, episode):
        event = cls()
        event.name = episode.name
        event.scope = "Local"
        event.impact = episode.summary
        event.backstory = episode.campaign.summary
        event.outcome = episode.episode_report
        event.start_date = episode.start_date
        event.end_date = episode.end_date
        event.story = episode.story
        event.associations = episode.associations
        event.episode = episode
        event.world = episode.world
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
    def path(self):
        return f"event/{self.pk}"

    ############# image generation #############
    def generate_image(self):
        if self.image:
            self.image.delete()
            self.image = None
        if image := Image.generate(prompt=self.desc, tags=["event"]):
            self.image = image
            self.image.save()
            self.save()
        else:
            log(self.image_prompt, "Image generation failed.", _print=True)
        return self.image

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
    @classmethod
    def auto_post_init(cls, sender, document, **kwargs):
        super().auto_post_init(sender, document, **kwargs)
        # MIGRATION: old Date to new Date
        if document.start_date and not isinstance(document.start_date, Date):
            document.start_date = None
        if document.end_date and not isinstance(document.end_date, Date):
            document.end_date = None

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

        # log(
        #     f"Pre-saved dates for {self}",
        #     self.start_date,
        #     self.end_date,
        #     self.world.current_date,
        # )
