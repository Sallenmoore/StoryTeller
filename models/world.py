import json

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
)
from autonomous.tasks import AutoTasks
from models.abstracts.ttrpgbase import TTRPGBase
from models.campaign import Campaign
from models.character import Character
from models.city import City
from models.creature import Creature
from models.encounter import Encounter
from models.events.calendar import Calendar
from models.events.event import Event
from models.faction import Faction
from models.images.image import Image
from models.item import Item
from models.journal import Journal
from models.location import Location
from models.poi import POI
from models.region import Region
from models.systems import (
    FantasySystem,
    HardboiledSystem,
    HistoricalSystem,
    HorrorSystem,
    PostApocalypticSystem,
    SciFiSystem,
    WesternSystem,
)
from models.tools.autogm import AutoGM


class World(TTRPGBase):
    system = ReferenceAttr(choices=["BaseSystem"])
    user = ReferenceAttr(choices=["User"], required=True)
    calendar = ReferenceAttr(choices=[Calendar])
    subusers = ListAttr(ReferenceAttr(choices=["User"]))
    campaigns = ListAttr(ReferenceAttr(choices=["Campaign"]))
    current_campaign = ReferenceAttr(choices=[Campaign])
    gm = ReferenceAttr(choices=[AutoGM])
    map = ReferenceAttr(choices=["Image"])

    _possible_events = ["Began", "Abandoned", "Present Day"]
    _funcobj = {
        "name": "generate_world",
        "description": "creates, completes, and expands a World data object for a TTRPG setting",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A unique and evocative name for the world",
                },
                "desc": {
                    "type": "string",
                    "description": "A brief physical description that will be used to generate an image of the world",
                },
                "backstory": {
                    "type": "string",
                    "description": "A brief history of the world and its people. Only include publicly known information.",
                },
                "notes": {
                    "type": "array",
                    "description": "Descriptions of 4 possible epic storylines in the world",
                    "items": {"type": "string"},
                },
            },
        },
    }
    _systems = {
        "fantasy": FantasySystem,
        "sci-fi": SciFiSystem,
        "western": WesternSystem,
        "hardboiled": HardboiledSystem,
        "mystery": HardboiledSystem,
        "horror": HorrorSystem,
        "post-apocalyptic": PostApocalypticSystem,
        "historical": HistoricalSystem,
    }
    ########################## Dunder Methods #############################

    ########################## Class Methods #############################

    @classmethod
    def build(cls, system, user, name="", desc="", backstory=""):
        System = World._systems.get(system)
        if not System:
            raise ValueError(f"System {system} not found")
        else:
            system = System()
            system.save()

        ### set attributes ###
        if not name.strip():
            name = f"{system._genre} World"
        if not desc.strip():
            desc = f"An expansive, complex, and mysterious {system._genre} setting suitable for a {system._genre} {system.get_title(World)}."
        if not backstory.strip():
            backstory = f"{name} is filled with curious and dangerous points of interest filled with various creatures and characters. The complex and mysterious history of this world is known only to a few reclusive individuals. Currently, there are several factions vying for power through poltical machinations, subterfuge, and open warfare."

        # log(f"Building world {name}, {desc}, {backstory}, {system}, {user}")

        world = cls(
            name=name,
            desc=desc,
            backstory=backstory,
            system=system,
            user=user,
        )
        world.save()
        world.update_refs()
        return world

    @classmethod
    def update_system_references(cls, pk):
        if obj := cls.get(pk):
            obj.system.update_refs(obj)
        else:
            log(f"Object {pk} not found", _print=True)

    ############################ PROPERTIES ############################
    @property
    def associations(self):
        return [
            *self.items,
            *self.characters,
            *self.creatures,
            *self.factions,
            *self.cities,
            *self.locations,
            *self.pois,
            *self.regions,
            *self.encounters,
        ]

    @property
    def characters(self):
        return Character.search(world=self) if self.pk else []

    @property
    def child_models(self):
        return self._models

    @property
    def cities(self):
        return City.search(world=self) if self.pk else []

    @property
    def creatures(self):
        return Creature.search(world=self) if self.pk else []

    @property
    def encounters(self):
        return Encounter.search(world=self) if self.pk else []

    @property
    def events(self):
        events = [e for obj in self.associations for e in obj.events]
        events += [
            obj.start_date
            for obj in self.associations
            if obj.start_date and obj.start_date.year
        ]
        events += [
            obj.end_date
            for obj in self.associations
            if obj.end_date and obj.end_date.year
        ]
        events.sort(reverse=True)
        return events

    @property
    def factions(self):
        return Faction.search(world=self) if self.pk else []

    @property
    def genre(self):
        return self.system._genre.lower()

    @property
    def items(self):
        return Item.search(world=self) if self.pk else []

    @property
    def image_prompt(self):
        return f"A full color, high resolution illustrated map of a fictional {self.genre} world called {self.name} and described as {self.desc or 'filled with points of interest to explore, antagonistic factions, and a rich, mysterious history.'}"

    @property
    def locations(self):
        return Location.search(world=self) if self.pk else []

    @property
    def map_thumbnail(self):
        return self.map.image.url(100)

    @property
    def map_prompt(self):
        return self.system.map_prompt(self)

    @property
    def parent(self):
        return None

    @property
    def players(self):
        return Character.search(world=self, is_player=True) if self.pk else []

    @property
    def player_faction(self):
        return Faction.find(world=self, is_player_faction=True) if self.pk else None

    @player_faction.setter
    def player_faction(self, obj):
        if self.pk:
            if result := Faction.find(world=self, is_player_faction=True):
                result.is_player_faction = False
                result.save()
            if obj:
                obj.is_player_faction = True
                obj.save()

    @property
    def pois(self):
        return POI.search(world=self) if self.pk else []

    @property
    def regions(self):
        return Region.search(world=self) if self.pk else []

    @property
    def users(self):
        return [self.user, *self.subusers]

    ########################## Override Methods #############################

    def delete(self):
        objs = [
            *Region.search(world=self),
            *City.search(world=self),
            *Location.search(world=self),
            *POI.search(world=self),
            *Encounter.search(world=self),
            *Faction.search(world=self),
            *Creature.search(world=self),
            *Character.search(world=self),
            *Item.search(world=self),
            *Campaign.search(world=self),
            *Event.search(obj=self),
            *Journal.search(world=self),
        ]
        for campaign in self.campaigns:
            campaign.delete()
        for obj in objs:
            obj.delete()
        if self in self.user.worlds:
            self.user.worlds.remove(self)
            self.user.save()
        if self.calendar:
            self.calendar.delete()
        if self.system:
            self.system.delete()
        if self.start_date:
            self.start_date.delete()
        if self.end_date:
            self.end_date.delete()
        return super().delete()

    ###################### Boolean Methods ########################

    def is_owner(self, user):
        return self.user == user

    def is_user(self, user):
        return self.is_owner(user) or user in self.subusers

    ###################### Getter Methods ########################
    def get_world(self):
        return self

    def get_players(self, exclude_campaign=None, count_only=False):
        if exclude_campaign:
            players = [p for p in self.players if p not in exclude_campaign.players]
        else:
            players = self.players
        return players if not count_only else len(players)

    def get_campaign_sessions(self, campaign):
        return campaign.sessions

    def add_association(self, obj):
        obj.world = self
        obj.save()
        return self.associations

    def is_child(self, obj):
        return self == obj.parent

    def is_associated(self, obj):
        return self == obj.world

    ###################### Data Methods ########################
    ################### Instance Methods #####################
    def update_refs(self):
        AutoTasks().task(World.update_system_references, self.pk)

    # MARK: generate_map
    def generate_map(self):
        self.map = Image.generate(
            prompt=self.map_prompt,
            tags=["map", "world", self.genre],
            img_quality="hd",
            img_size="1792x1024",
        )
        self.map.save()
        self.save()
        return self.map

    def get_map_list(self):
        images = []
        for img in Image.all():
            # log(img.asset_id)
            if all(t in img.tags for t in ["map", "world", self.genre]):
                images.append(img)
        return images

    def page_data(self):
        response = {
            "worldname": self.name,
            "genre": self.genre,
            "backstory": self.backstory,
            "current_date": self.calendar.stringify(self.current_date),
            "canonical_history": [
                c.page_data() for c in self.campaigns if c.start_date
            ],
            "objects": {
                "Regions": [o.page_data() for o in self.regions],
                "Locations": [o.page_data() for o in self.locations],
                "Cities": [o.page_data() for o in self.cities],
                "Points of Interest": [o.page_data() for o in self.pois],
                "Factions": [o.page_data() for o in self.factions],
                "Characters": [o.page_data() for o in self.characters],
                "Items": [o.page_data() for o in self.items],
                "Creatures": [o.page_data() for o in self.creatures],
                "Encounters": [o.page_data() for o in self.encounters],
            },
        }
        # Convert the response object to JSON
        json_data = json.dumps(response, indent=4, sort_keys=True)
        # Define the file path
        file_path = f"logs/{self.name}-{self.model_name()}-{self.pk}.json"
        # Write the JSON data to the file
        with open(file_path, "w") as file:
            file.write(json_data)
        return response

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     # log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)
    #     document.campaigns.sort(key=lambda x: x.start_date, reverse=True)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_system()
        document.pre_save_calendar()
        document.pre_save_events()
        document.pre_save_end_date()
        document.pre_save_campaign()

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)
        document.post_save_system()
        document.post_save_campaign()
        document.post_save_gm()
        document.post_save_users()

    # def clean(self):
    #     super().clean()

    ################### verification methods ##################
    def pre_save_campaign(self):
        # Traverse through all elements in the list
        self.campaigns.sort(key=lambda x: (x.start_date))

    def pre_save_system(self):
        # log(f"Verifying system for {self.name}: self.system={self.system}")
        if not self.system:
            system = FantasySystem()
            system.save()
            self.system = system
        elif isinstance(self.system, str):
            if SystemModel := self._systems.get(self.system):
                self.system = SystemModel()
                self.system.save()
            else:
                raise ValidationError(
                    f"The system key does not correspond to a system: {self.system}"
                )

        # log(f"Verifying system for {self.name}: self.system={self.system}")

    def post_save_system(self):
        # log(f"Verifying system for {self.name}: self.system={self.system}")
        if self.system.world != self:
            self.system.world = self
            self.system.save()

    def pre_save_calendar(self):
        if not self.calendar:
            calendar = Calendar()
            calendar.save()
            self.calendar = calendar

    def post_save_campaign(self):
        if self.campaigns and not self.current_campaign:
            self.current_campaign = self.campaigns[-1]
            self.save()

    def pre_save_end_date(self):
        if self.start_date and not self.start_date.year:
            self.start_date.year = 1
        if (not self.end_date and self.calendar.current_date) or (
            self.calendar.current_date != self.end_date
        ):
            self.end_date = self.calendar.current_date

    def pre_save_events(self):
        if self.events:
            self.calendar.current_date = self.events[-1]
            for event in self.events:
                if (event.obj and getattr(event.obj, "canon", None)) or (
                    event.episode
                    and event.episode.end_date
                    and event.episode.end_date.year
                ):
                    # log(event.obj, event.year)
                    if event > self.calendar.current_date:
                        # log(event, event.year)
                        self.calendar.current_date = event
                        self.calendar.save()

    def post_save_gm(self):
        if not self.gm:
            gm = AutoGM(world=self)
            gm.save()
            self.gm = gm
            self.save()

    def post_save_users(self):
        from models.user import User

        if self.pk and self not in self.user.worlds:
            self.user.worlds.append(self)
            self.user.save()
