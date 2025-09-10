import random
from copy import deepcopy

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import BoolAttr, ListAttr, ReferenceAttr, StringAttr
from models.base.ttrpgbase import TTRPGBase
from models.calendar.date import Date

MAX_NUM_IMAGES_IN_GALLERY = 100
IMAGES_BASE_PATH = "static/images/tabletop"


class TTRPGObject(TTRPGBase):
    meta = {"abstract": True, "allow_inheritance": True, "strict": False}
    world = ReferenceAttr(choices=["World"])
    canon = BoolAttr(default=False)
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    parent = ReferenceAttr(choices=[TTRPGBase])
    start_date = ReferenceAttr(choices=["Date"])
    end_date = ReferenceAttr(choices=["Date"])
    status = StringAttr(default="")
    parent_list = []

    start_date_label = "Founded"
    end_date_label = "Abandoned"

    is_ttrpgobject = True

    @property
    def calendar(self):
        return self.world.calendar

    @property
    def campaigns(self):
        return [c for c in self.world.campaigns if self in c.associations]

    @property
    def characters(self):
        return [a for a in self.associations if a.model_name() == "Character"]

    @property
    def children(self):
        return [obj for obj in self.associations if obj.parent == self]

    @property
    def cities(self):
        return [a for a in self.associations if a.model_name() == "City"]

    @property
    def creatures(self):
        return [a for a in self.associations if a.model_name() == "Creature"]

    @property
    def districts(self):
        return [a for a in self.associations if a.model_name() == "District"]

    @property
    def encounters(self):
        return [a for a in self.associations if a.model_name() == "Encounter"]

    @property
    def factions(self):
        return [a for a in self.associations if a.model_name() == "Faction"]

    @property
    def genre(self):
        return self.world.genre.lower()

    @property
    def geneology(self):
        ancestry = []
        if self.parent:
            ancestry.append(self.parent)
            ancestor = self.parent
            while ancestor.parent and ancestor.parent not in ancestry:
                log(f"Adding ancestor {ancestor} to ancestry of {self}")
                ancestry.append(ancestor.parent)
                ancestor = ancestor.parent
        if self.world not in ancestry:
            ancestry.append(self.world)
        return ancestry

    @property
    def items(self):
        return [a for a in self.associations if a.model_name() == "Item"]

    @property
    def locations(self):
        return [a for a in self.associations if a.model_name() == "Location"]

    @property
    def regions(self):
        return [a for a in self.associations if a.model_name() == "Region"]

    @property
    def shops(self):
        return [a for a in self.associations if a.model_name() == "Shop"]

    @property
    def stories(self):
        stories = [s for s in self.world.stories if self in s.associations]
        return stories

    @property
    def system(self):
        return self.world.system

    @property
    def title(self):
        return self.get_title(self)

    @property
    def titles(self):
        return self.world.system._titles

    @property
    def user(self):
        return self.world.user

    @property
    def vehicles(self):
        return [a for a in self.associations if a.model_name() == "Vehicle"]

    ############# Boolean Methods #############

    def is_owner(self, user):
        try:
            return self.world.is_owner(user)
        except Exception as e:
            log(e, self, "Object has no world")
            raise e

    def in_parent_list(self, obj):
        return obj.model_name() in self.parent_list

    ########## Object Data ######################
    def get_world(self):
        # IMPORTANT: this is here to register the model
        # without it, the model may not have been registered yet and it will fail
        from models.world import World

        return self.world

    def get_episodes(self, campaign):
        return [c for c in campaign.episodes if self in c.associations]

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
        document.pre_save_world()
        document.pre_save_associations()
        document.pre_save_dates()
        document.pre_save_canon()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    def pre_save_associations(self):
        if self in self.associations:
            self.associations.remove(self)

        for children in self.children:
            for grand in children.children:
                self.associations += [grand]
        # Remove duplicates and sort associations by model_name, then by name
        self.associations = sorted(
            set(self.associations),
            key=lambda a: (a.model_name(), getattr(a, "name", "")),
        )

    def pre_save_canon(self):
        for campaign in self.world.campaigns:
            for ass in campaign.associations:
                if str(self.pk) == str(ass.pk):
                    self.canon = True
                    return
        self.canon = False

    def pre_save_world(self):
        if not self.world:
            raise ValidationError("Must be associated with a World object")

    def pre_save_dates(self):
        if hasattr(self.start_date, "pk") and not self.start_date.pk:
            self.start_date = None
        if hasattr(self.end_date, "pk") and not self.end_date.pk:
            self.end_date = None

        if self.pk and self.calendar:
            # log(f"Pre-saving dates for {self}", self.start_date, self.end_date)
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
                start_date.save()
                self.start_date = start_date
            elif not self.start_date or not isinstance(self.start_date, Date):
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
                    dates.sort(key=lambda x: (x.year, x.month, x.day))
                    log(dates)
                    while len(dates) > 1:
                        dates[-1].delete()
                        dates.pop()
                    log(dates)
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
                end_date.save()
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
