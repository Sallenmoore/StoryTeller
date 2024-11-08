import random

from autonomous import log
from autonomous.model.autoattr import (
    BoolAttr,
    DictAttr,
    IntAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel


class Event(AutoModel):
    obj = ReferenceAttr(choices=["TTRPGBase", "Session"])
    year = IntAttr(default=0)
    month = IntAttr(default=lambda: random.randint(0, 11))
    day = IntAttr(default=lambda: random.randint(1, 30))
    episode = ReferenceAttr(choices=["Session"])
    visibility = BoolAttr(default=True)
    name = StringAttr(default="")
    coordinates = DictAttr(default=lambda: {"x": 0, "y": 0})

    visibility_options = ["public", "owner"]
    event_options = ["1st Appearance", "Critical Event"]
    icon_options = {
        "basic": {
            "Character": "el:person",
            "Creature": "fa-solid:spider",
            "Encounter": "game-icons:battle-gear",
            "Item": "ph:treasure-chest-fill",
            "Location": "fa-solid:map-marked-alt",
            "POI": "tabler:building-castle",
            "Region": "mdi:landscape",
            "City": "mdi:city",
            "Faction": "clarity:group-line",
        },
        "start": {
            "Character": "el:person",
            "Creature": "fa-solid:spider",
            "Encounter": "game-icons:battle-gear",
            "Item": "ph:treasure-chest-fill",
            "Location": "fa-solid:map-marked-alt",
            "POI": "tabler:building-castle",
            "Region": "mdi:landscape",
            "City": "mdi:city",
            "Faction": "clarity:group-line",
        },
        "end": {
            "Character": "mdi:death",
            "Creature": "healthicons:death-alt",
            "Encounter": "mdi:shop-complete",
            "Item": "streamline:lost-and-found",
            "Location": "game-icons:castle-ruins",
            "POI": "game-icons:ancient-ruins",
            "Region": "pepicons-pop:flag-circle-off",
            "City": "game-icons:stone-pile",
            "Faction": "bi:heartbreak",
        },
    }

    ################### Dunder Methods #####################
    def __str__(self):
        return self.datestr()

    def __lt__(self, other):
        if other:
            if self.year < other.year:
                return True
            elif self.year == other.year:
                if self.month < other.month:
                    return True
                elif self.month == other.month:
                    return self.day < other.day
        return False

    def __gt__(self, other):
        if other:
            if self.year > other.year:
                return True
            elif self.year == other.year:
                if self.month > other.month:
                    return True
                elif self.month == other.month:
                    return self.day > other.day
        return False

    def __eq__(self, other):
        if other:
            return (
                self.year == other.year
                and self.month == other.month
                and self.day == other.day
            )
        return False

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return self > other or self == other

    def __ne__(self, other):
        return not self == other

    ################### Property Methods #####################
    @property
    def calendar(self):
        return self.obj.calendar

    @property
    def month_str(self):
        return self.calendar.get_month_str(self.month)

    @property
    def placed(self):
        if isinstance(self.coordinates, list):
            self.coordinates = {
                "x": int(self.coordinates[0]),
                "y": int(self.coordinates[1]),
            }
        return (
            self.coordinates and self.coordinates.get("x") and self.coordinates.get("y")
        )

    @property
    def summary(self):
        summary = f"""
        <h6>{self.obj.name}</h6>
        <h5 class='has-text-center has-text-primary'>{self.name or 'Unknown Event'}</h5>
        <h6>{self.obj.calendar.stringify(self.date)}</h6>
        """
        if self.episode and self.episode.summary:
            summary += f"""
            <p>{self.episode.summary}<p>
            <span class="tag">{self.episode.name}</span>
            """
        return summary

    @property
    def world(self, value):
        return self.obj.world if self.obj else None

    ################### Crud Methods #####################

    def icon(self, etype="basic"):
        return self.icon_options[etype][self.obj.model_name()]

    def datestr(self, sep=" ", order=None):
        return (
            self.obj.calendar.stringify(self, sep=sep, order=order) if self.obj else ""
        )

    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        # document.pre_save_date()
        document.pre_save_coordinates()
        document.pre_save_episode()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################# Verification Methods ##################

    # def pre_save_date(self):
    #     log(self.day, self.month, self.year)

    def pre_save_coordinates(self):
        if not self.coordinates:
            self.coordinates = {}
        elif isinstance(self.coordinates, list):
            self.coordinates = {
                "x": int(self.coordinates[0]),
                "y": int(self.coordinates[1]),
            }

    def pre_save_episode(self):
        if self.obj and self.obj.model_name() == "Session":
            self.episode = self.obj
        elif not self.obj and self.episode:
            self.obj = self.episode
