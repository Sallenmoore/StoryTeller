import random
from copy import deepcopy

from autonomous.db import ValidationError
from autonomous.model.autoattr import BoolAttr, ListAttr, ReferenceAttr, StringAttr

from autonomous import log
from models.base.ttrpgbase import TTRPGBase
from models.calendar.date import Date
from models.utility.parse_attributes import parse_date

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
    parent_list = []

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
                ancestry.append(ancestor.parent)
                ancestor = ancestor.parent
                self.add_association(ancestor)
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

        # MIGRATION: remove encountrers from associations
        document.associations = [
            a for a in document.associations if a.model_name() != "Encounter"
        ]

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    def pre_save_associations(self):
        if self in self.associations:
            self.associations.remove(self)

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

        if start_date := parse_date(self, self.start_date):
            if self.start_date:
                self.start_date.delete()
            self.start_date = start_date
            self.start_date.save()

        if end_date := parse_date(self, self.end_date):
            if self.end_date:
                self.end_date.delete()
            self.end_date = end_date
            self.end_date.save()

        if self.start_date:
            if self.start_date.day <= 0:
                self.start_date.day = random.randint(1, 28)
            if self.start_date.month <= 0:
                self.start_date.month = random.randint(1, 12)
        if self.end_date:
            if self.end_date.day <= 0:
                self.end_date.day = random.randint(1, 28)
            if self.end_date.month <= 0:
                self.end_date.month = random.randint(1, 12)
