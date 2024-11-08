from copy import deepcopy

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import BoolAttr, ListAttr, ReferenceAttr
from models.abstracts.ttrpgbase import TTRPGBase

from ..events.event import Event

MAX_NUM_IMAGES_IN_GALLERY = 100
IMAGES_BASE_PATH = "static/images/tabletop"


class TTRPGObject(TTRPGBase):
    meta = {"abstract": True, "allow_inheritance": True, "strict": False}
    world = ReferenceAttr(choices=["World"])
    parent = ReferenceAttr(choices=[TTRPGBase])
    events = ListAttr(ReferenceAttr(choices=[Event]))
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    canon = BoolAttr(default="False")
    parent_list = []

    _no_copy = TTRPGBase._no_copy | {
        "parent": None,
        "associations": [],
        "events": [],
    }

    @classmethod
    def update_system_references(cls, pk):
        log(f"Updating AI reference data for ({cls}:{pk})...")
        try:
            from models.world import World

            return cls().get(pk).world.update_system_references(pk)
        except Exception as e:
            log(e, cls, "Object has no world")
            return False

    @property
    def calendar(self):
        return self.get_world().calendar

    @property
    def campaigns(self):
        campaigns = []
        for campaign in self.get_world().campaigns:
            if self in campaign.associations:
                campaigns.append(campaign)
        return campaigns

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
    def current_campaign(self):
        return self.get_world().current_campaign

    @property
    def encounters(self):
        return [a for a in self.associations if a.model_name() == "Encounter"]

    @property
    def factions(self):
        return [a for a in self.associations if a.model_name() == "Faction"]

    @property
    def genre(self):
        return self.get_world().genre.lower()

    @property
    def gm(self):
        return self.get_world().gm

    @property
    def items(self):
        return [a for a in self.associations if a.model_name() == "Item"]

    @property
    def locations(self):
        return [a for a in self.associations if a.model_name() == "Location"]

    @property
    def pois(self):
        return [a for a in self.associations if a.model_name() == "POI"]

    @property
    def regions(self):
        return [a for a in self.associations if a.model_name() == "Region"]

    @property
    def subusers(self):
        return self.get_world().subusers

    @property
    def system(self):
        return self.get_world().system

    @property
    def title(self):
        return self.get_world().system.get_title(self)

    @property
    def titles(self):
        return self.get_world().system._titles

    @property
    def user(self):
        return self.get_world().user

    ############# Boolean Methods #############

    def is_owner(self, user):
        try:
            return self.get_world().is_owner(user)
        except Exception as e:
            log(e, self, "Object has no world")
            return False

    ########## Object Data ######################
    def check_canon(self):
        if self.campaigns and (
            (hasattr(self, "group") and self.group)
            or (self.start_date and self.start_date.year)
        ):
            self.canon = True
        else:
            self.canon = False
        return self.canon

    def get_world(self):
        # IMPORTANT: this is here to register the model
        # without it, the model may not have been registered yet and it will fail
        from models.world import World

        return self.world

    def copy(self):
        obj = deepcopy(self)
        obj.pk = None
        obj.name = f"_{self.name}_ (Copy)" if "(Copy)" not in self.name else self.name
        for attr, value in self._no_copy.items():
            setattr(obj, attr, value)
        obj.save()
        return obj

    def get_campaign_sessions(self, campaign):
        sessions = []
        for session in campaign.sessions:
            if self in session.associations:
                sessions.append(session)
        log(sessions)
        return sessions

    def add_event(
        self,
        episode=None,
        date=None,
        visibility=True,
        name=None,
        coordinates=None,
    ):
        new_event = Event(
            _obj=self,
            _episode=episode,
            _date=date,
            _visibility=visibility,
            _name=name,
            _coordinates=coordinates,
        )
        new_event.save()
        self.events.append(new_event)
        self.save()
        if new_event.date > self.calendar.current_date:
            self.calendar.current_date.day = new_event.day
            self.calendar.current_date.month = new_event.month
            self.calendar.current_date.year = new_event.year
            self.calendar.save()

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
        document.pre_save_parent()
        document.pre_save_world()
        document.pre_save_associations()
        document.pre_save_canon()

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    def pre_save_parent(self):
        ancestor = self
        while ancestor:
            if ancestor.parent == self:
                ancestor.parent = None
                ancestor.save()
            else:
                ancestor = ancestor.parent

        if self.parent and (
            self.parent == self
            or self.parent.model_name()
            not in [
                "World",
                *self.parent_list,
            ]
        ):
            log(f"Parent must be a World or {self.parent_list}, not {self.parent}")
            self.parent = None

        elif self.parent not in self.associations:
            self.associations.append(self.parent)

    def pre_save_associations(self):
        if self in self.associations:
            self.associations.remove(self)

    def pre_save_world(self):
        if not self.get_world():
            raise ValidationError("Must be associated with a World object")

    def pre_save_canon(self):
        if not self.canon:
            if self.campaigns and (
                (hasattr(self, "group") and self.group)
                or (self.start_date and self.start_date.year)
            ):
                self.canon = True
            else:
                self.canon = False
        self.canon = bool(self.canon)
