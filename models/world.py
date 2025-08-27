import json
import os
import random

import requests
import validators

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from models.base.ttrpgbase import TTRPGBase
from models.calendar.calendar import Calendar
from models.campaign.campaign import Campaign
from models.images.image import Image
from models.images.map import Map
from models.journal import Journal
from models.stories.story import Story
from models.systems import (
    FantasySystem,
    HardboiledSystem,
    HistoricalSystem,
    HorrorSystem,
    PostApocalypticSystem,
    SciFiSystem,
    WesternSystem,
)
from models.systems.swn import StarsWithoutNumber
from models.ttrpgobject.character import Character
from models.ttrpgobject.city import City
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.district import District
from models.ttrpgobject.encounter import Encounter
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.location import Location
from models.ttrpgobject.region import Region
from models.ttrpgobject.shop import Shop
from models.ttrpgobject.vehicle import Vehicle


class World(TTRPGBase):
    system = ReferenceAttr(choices=["BaseSystem"])
    users = ListAttr(ReferenceAttr(choices=["User"]))
    calendar = ReferenceAttr(choices=["Calendar"])
    current_date = ReferenceAttr(choices=["Date"])
    map = ReferenceAttr(choices=["Image"])
    map_prompt = StringAttr(default="")
    campaigns = ListAttr(ReferenceAttr(choices=["Campaign"]))
    stories = ListAttr(ReferenceAttr(choices=["Story"]))

    SYSTEMS = {
        "fantasy": FantasySystem,
        "scifi": SciFiSystem,
        "swn": StarsWithoutNumber,
        "hardboiled": HardboiledSystem,
        "horror": HorrorSystem,
        "historical": HistoricalSystem,
        "postapocalyptic": PostApocalypticSystem,
        "western": WesternSystem,
    }

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
            },
        },
    }
    ########################## Dunder Methods #############################

    ########################## Class Methods #############################

    @classmethod
    def build(cls, system, user, name="", desc="", backstory=""):
        # log(f"Building world {name}, {desc}, {backstory}, {system}, {user}")
        System = {
            "fantasy": FantasySystem,
            "sci-fi": SciFiSystem,
            "western": WesternSystem,
            "hardboiled": HardboiledSystem,
            "horror": HorrorSystem,
            "post-apocalyptic": PostApocalypticSystem,
            "historical": HistoricalSystem,
        }.get(system)
        if not System:
            raise ValueError(f"System {system} not found")
        else:
            system = System()
            system.save()
        # log(f"Building world {name}, {desc}, {backstory}, {system}, {user}")
        ### set attributes ###
        if not name.strip():
            name = f"{system._genre} Setting"
        if not desc.strip():
            desc = f"An expansive, complex, and mysterious {system._genre} setting suitable for a {system._genre} {system.get_title(cls)}."
        if not backstory.strip():
            backstory = f"{name} is filled with curious and dangerous points of interest filled with various creatures and characters. The complex and mysterious history of this world is known only to a few reclusive individuals. Currently, there are several factions vying for power through poltical machinations, subterfuge, and open warfare."

        # log(f"Building world {name}, {desc}, {backstory}, {system}, {user}")

        world = cls(
            name=name,
            desc=desc,
            backstory=backstory,
            system=system,
            users=[user],
        )
        system.world = world
        world.users += [user]
        world.save()
        system.save()
        f = Faction(world=world, is_player_faction=True)
        f.save()
        world.add_association(f)
        c = Character(world=world, parent=f, is_player=True)
        c.save()
        c.add_association(f)
        world.add_association(c)
        f.add_association(c)
        requests.post(
            f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{world.path}"
        )
        requests.post(f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{f.path}")
        requests.post(f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{c.path}")
        return world

    ############################ PROPERTIES ############################
    @property
    def associations(self):
        return sorted(
            [
                *self.items,
                *self.characters,
                *self.creatures,
                *self.factions,
                *self.cities,
                *self.locations,
                *self.encounters,
                *self.regions,
                *self.vehicles,
                *self.shops,
                *self.districts,
            ],
            key=lambda x: (
                x.name.startswith("_"),
                "",
                x.name,
            ),
        )

    @associations.setter
    def associations(self, obj):
        if obj.world != self:
            obj.world = self
            obj.save()

    @property
    def characters(self):
        return sorted(
            Character.search(world=self) if self.pk else [], key=lambda x: x.name
        )

    @property
    def children(self):
        return self.associations

    @property
    def cities(self):
        return sorted(City.search(world=self) if self.pk else [], key=lambda x: x.name)

    @property
    def creatures(self):
        return sorted(
            Creature.search(world=self) if self.pk else [], key=lambda x: x.name
        )

    @property
    def districts(self):
        return sorted(
            District.search(world=self) if self.pk else [], key=lambda x: x.name
        )

    @property
    def encounters(self):
        return sorted(
            Encounter.search(world=self) if self.pk else [], key=lambda x: x.name
        )

    @property
    def factions(self):
        return sorted(
            Faction.search(world=self) if self.pk else [], key=lambda x: x.name
        )

    @property
    def genre(self):
        return self.system._genre.lower()

    @property
    def items(self):
        return sorted(Item.search(world=self) if self.pk else [], key=lambda x: x.name)

    @property
    def image_prompt(self):
        return f"A full color, high resolution illustrated map of a fictional {self.genre} setting called {self.name} and described as {self.desc or 'filled with points of interest to explore, antagonistic factions, and a rich, mysterious history.'}"

    @property
    def jobs(self):
        jobs = []
        for c in self.characters:
            jobs += c.quests
        jobs = list(set(jobs))
        return jobs

    @property
    def locations(self):
        return sorted(
            Location.search(world=self) if self.pk else [], key=lambda x: x.name
        )

    @property
    def map_thumbnail(self):
        return self.map.image.url(100)

    @property
    def parent(self):
        return None

    @property
    def players(self):
        return Character.search(world=self, is_player=True) if self.pk else []

    @property
    def parties(self):
        ps = []
        for f in Faction.search(world=self, is_player_faction=True):
            ps += [f]
        return ps

    @property
    def end_date(self):
        return self.current_date

    @end_date.setter
    def end_date(self, date):
        self.current_date = date

    @property
    def regions(self):
        return sorted(
            Region.search(world=self) if self.pk else [], key=lambda x: x.name
        )

    @property
    def shops(self):
        return sorted(Shop.search(world=self) if self.pk else [], key=lambda x: x.name)

    @property
    def user(self):
        return self.users[0] if self.users else None

    @property
    def vehicles(self):
        return sorted(
            Vehicle.search(world=self) if self.pk else [], key=lambda x: x.name
        )

    ########################## Override Methods #############################

    def delete(self):
        objs = [
            self.system,
            *Campaign.search(world=self),
            *Region.search(world=self),
            *City.search(world=self),
            *Location.search(world=self),
            *Journal.search(parent=self),
            *Vehicle.search(world=self),
            *District.search(world=self),
            *Encounter.search(world=self),
            *Faction.search(world=self),
            *Creature.search(world=self),
            *Character.search(world=self),
            *Vehicle.search(world=self),
            *Item.search(world=self),
        ]
        for obj in objs:
            if obj:
                obj.delete()
        return super().delete()

    ###################### Boolean Methods ########################

    def is_associated(self, obj):
        return self == obj.world

    def is_user(self, user):
        return user in self.users

    ###################### Getter Methods ########################
    def get_world(self):
        return self

    ###################### Setter Methods ########################
    def add_association(self, obj):
        obj.world = self
        obj.save()
        return self.associations

    def set_system(self, System):
        if System:
            self.system.delete()
            self.system = System(world=self)
            self.system.save()
            self.save()

        for obj in [*self.characters, *self.creatures]:
            obj.skills = self.system.skills.copy()
            obj.save()

        for obj in self.creatures:
            obj.skills = self.system.skills.copy()
            obj.save()

        return self.system

    ###################### Data Methods ########################

    ################### Instance Methods #####################

    # MARK: generate_map
    def generate_map(self):
        self.map = Map.generate(
            prompt=self.map_prompt or self.system.map_prompt(self),
            tags=["map", self.model_name().lower(), self.genre],
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
            if all(
                t in img.tags for t in ["map", self.model_name().lower(), self.genre]
            ):
                images.append(img)
        return images

    def page_data(self):
        response = {
            "worldname": self.name,
            "genre": self.genre,
            "backstory": self.backstory,
            "current_date": str(self.current_date),
            "world_objects": {
                "Regions": [o.page_data() for o in self.regions],
                "Locations": [o.page_data() for o in self.locations],
                "Vehicles": [o.page_data() for o in self.vehicles],
                "Cities": [o.page_data() for o in self.cities],
                "Factions": [o.page_data() for o in self.factions],
                "Players": [o.page_data() for o in self.players],
                "Characters": [o.page_data() for o in self.characters],
                "Items": [o.page_data() for o in self.items],
                "Creatures": [o.page_data() for o in self.creatures],
                "Districts": [o.page_data() for o in self.districts],
                "Shops": [o.page_data() for o in self.shops],
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
    #     =

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        from models.gmscreen.gmscreen import GMScreen

        super().auto_pre_save(sender, document, **kwargs)

        ##### MIGRATION #####
        stories = []
        for story in document.stories:
            if isinstance(story, Story):
                stories.append(story)

        document.stories = stories

        document.pre_save_users()
        document.pre_save_system()
        document.pre_save_map()
        document.pre_save_current_date()

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)
        document.post_save_system()

    # def clean(self):
    #     super().clean()

    ################### verification methods ##################

    def pre_save_users(self):
        users = []
        for u in self.users:
            if u not in users:
                users.append(u)
        self.users = users

    def pre_save_map(self):
        if not self.map_prompt:
            self.map_prompt = self.description_summary or self.description

        if isinstance(self.map, str):
            if validators.url(self.map):
                self.map = Map.from_url(
                    self.map,
                    prompt=self.map_prompt,
                    tags=["map", *self.image_tags],
                )
                self.map.save()
            elif image := Image.get(self.map):
                self.map = Map.from_image(image)
                self.map.save()
            elif image := Map.get(self.map):
                self.map = image
            else:
                raise ValidationError(
                    f"Image must be an Map object, url, or Image, not {self.map}"
                )
        elif type(self.map) is Image:
            log("converting to map...", self.map, _print=True)
            self.map = Map.from_image(self.map)
            self.map.save()
            log("converted to map", self.map, _print=True)
        elif self.map and not self.map.tags:
            self.map.tags = self.map_tags
            self.map.save()

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

    def pre_save_current_date(self):
        # log(
        #     f"Verifying current_date for {self.name}: self.current_date={self.current_date}:{type(self.current_date)}"
        # )
        if not self.calendar:
            self.calendar = Calendar()
            self.calendar.save()

    def post_save_system(self):
        # log(f"Verifying system for {self.name}: self.system={self.system}")
        if self.system.world != self:
            self.system.world = self
            self.system.save()
