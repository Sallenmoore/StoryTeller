import json
import os
import random
import traceback

import requests
import validators
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)

from autonomous import log
from models.base.ttrpgbase import TTRPGBase
from models.calendar.calendar import Calendar
from models.campaign.campaign import Campaign
from models.images.image import Image
from models.images.map import Map
from models.journal import Journal
from models.stories.encounter import Encounter
from models.stories.event import Event
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
from models.ttrpgobject.ability import Ability
from models.ttrpgobject.character import Character
from models.ttrpgobject.city import City
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.district import District
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
    start_date = ReferenceAttr(choices=["Date"])
    map = ReferenceAttr(choices=["Map"])
    tone = StringAttr(default="")
    map_prompt = StringAttr(default="")
    image_style = StringAttr(default="illustrated")
    map_style = StringAttr(default="isometric")
    campaigns = ListAttr(ReferenceAttr(choices=["Campaign"]))
    stories = ListAttr(ReferenceAttr(choices=["Story"]))

    TONES = {
        "Grimdark": "Dystopian, amoral, and violent, where hope is rare and the setting is generally brutal and bleak.",
        "Noblebright": "Features characters actively fighting for positive change, kindness, and communal responses to challenges, often in a world that may still have serious issues.",
        "Dark Fantasy": "Incorporates elements of horror into a fantasy setting, focusing on dark atmospheres, moral ambiguity, and gothic elements without necessarily being completely without hope.",
        "High Fantasy": "Clear distinction between good and evil, with powerful heroes, high levels of magic, and large-scale, epic stories, sometimes involving direct intervention from gods.",
        "Low Fantasy": "Grounded in a more realistic world with limited magic, where characters are often anti-heroes struggling to get by in a harsh environment.",
        "Heroic Fantasy": "Focuses on 'shiny good guys' and straightforward heroic narratives, often involving powerful heroes (e.g., Conan-style 'sword and sorcery').",
        "Cozy Fantasy": "Features low stakes, minimal violence, and focuses on comfort and positive interactions,  slice-of-life.",
        "Urban Fantasy": "Sets the narrative in the modern world with hidden or overt magical elements.",
        "Whimsical/Zany": "Light-hearted, sometimes manic or ridiculous surface tone, which can sometimes have deeper, more melancholy undertones.",
    }

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

    start_date_label = "Founding"
    end_date_label = "Current"

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
                "image_style": {
                    "type": "string",
                    "description": "The artistic style of the world's character, creature, item, ands location images",
                },
                "map_style": {
                    "type": "string",
                    "description": "The artistic style of the world's geographic and battlemap images",
                },
                "map_prompt": {
                    "type": "string",
                    "description": "A text prompt describing the world's map to be used for image generation",
                },
            },
        },
    }
    ########################## Dunder Methods #############################

    ########################## Class Methods #############################

    @classmethod
    def build(cls, system, user, name="", tone="", backstory=""):
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

        world = cls(
            name=name.strip(),
            tone=tone.strip(),
            backstory=backstory,
            system=system,
            users=[user],
        )
        system.world = world
        if user not in world.users:
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
        s = Story(world=world, name="Main Story")
        s.save()
        world.stories += [s]
        world.save()
        requests.post(
            f"http://{os.environ.get('TASKS_SERVICE_NAME')}:{os.environ.get('COMM_PORT')}/generate/{world.path}"
        )
        requests.post(
            f"http://{os.environ.get('TASKS_SERVICE_NAME')}:{os.environ.get('COMM_PORT')}/generate/{f.path}"
        )
        requests.post(
            f"http://{os.environ.get('TASKS_SERVICE_NAME')}:{os.environ.get('COMM_PORT')}/generate/{c.path}"
        )
        requests.post(
            f"http://{os.environ.get('TASKS_SERVICE_NAME')}:{os.environ.get('COMM_PORT')}/generate/story/{s.pk}"
        )
        return world

    ############################ PROPERTIES ############################
    @property
    def associations(self):
        # import traceback

        # traceback.print_stack()
        # log(traceback.format_exc())
        # log("Getting associations for world...", _print=True)
        result = [
            *self.characters,
            *self.items,
            *self.creatures,
            *self.factions,
            *self.locations,
            *self.vehicles,
            *self.shops,
            *self.cities,
            *self.districts,
            *self.regions,
        ]
        # log(f"Found {len(result)} associations", _print=True)
        return result

    @associations.setter
    def associations(self, obj):
        if obj.world != self:
            obj.world = self
            obj.save()

    @property
    def abilities(self):
        return sorted(
            Ability.search(world=self) if self.pk else [], key=lambda x: x.name
        )

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
    def events(self):
        return sorted(
            [e for e in Event.search(world=self) if e.end_date and e.end_date.year]
            if self.pk
            else [],
            key=lambda x: x.end_date,
            reverse=True,
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
    def lore(self):
        from models.stories.lore import Lore

        return sorted(Lore.search(world=self) if self.pk else [], key=lambda x: x.name)

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
    def tone_description(self):
        return self.TONES.get(
            self.tone, "A balanced tone with a mix of light and dark elements."
        )

    @property
    def user(self):
        return self.users[0] if self.users else None

    @property
    def vehicles(self):
        return sorted(
            Vehicle.search(world=self) if self.pk else [], key=lambda x: x.name
        )

    @property
    def world(self):
        return self

    ########################## CRUD Methods #############################

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
    def add_user(self, user):
        user.save()
        if user not in self.users:
            self.users += [user]
            self.save()
        return self.users

    def add_association(self, obj):
        obj.world = self
        obj.save()
        return self.associations

    def set_current_date(self):
        event_dates = (
            [e.end_date for e in self.events if e.end_date and e.end_date.year > 0]
            if self.events
            else []
        )

        episode_dates = (
            [
                e.end_date
                for c in self.campaigns
                for e in c.episodes
                if e.end_date and e.end_date.year > 0
            ]
            if self.campaigns
            else []
        )

        all_dates = event_dates + episode_dates
        if all_dates:
            self.current_date = max(all_dates)
            self.save()
        return self.current_date

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
        prompt = f"""{self.system.map_prompt(self)}

The map should be in a {self.world.map_style} style.
"""
        map = Map.generate(
            prompt=prompt,
            tags=["map", self.model_name().lower(), self.genre],
            img_quality="hd",
            img_size="1792x1024",
        )
        if map and self.map:
            self.map.delete()
        self.map = map
        self.map.save()
        self.save()
        return self.map

    def get_map_list(self):
        maps = []
        for img in Map.all():
            # log(img.asset_id)
            if all(
                t in img.tags for t in ["map", self.model_name().lower(), self.genre]
            ):
                maps.append(img)
        return maps

    def page_data(self):
        response = {
            "worldname": self.name,
            "genre": self.genre,
            "backstory": self.history,
            "current_date": str(self.current_date),
            "campaigns": [c.page_data() for c in self.campaigns],
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
    @classmethod
    def auto_post_init(cls, sender, document, **kwargs):
        # log("Auto Pre Save World")
        super().auto_post_init(sender, document, **kwargs)
        if not document.current_date and document.calendar:
            document.set_current_date()

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        from models.gmscreen.gmscreen import GMScreen

        super().auto_pre_save(sender, document, **kwargs)

        document.pre_save_system()
        document.pre_save_map()

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)
        document.post_save_system()

    # def clean(self):
    #     super().clean()

    ################### verification methods ##################

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
            elif map := Map.get(self.map):
                self.map = map
            elif image := Image.get(self.map):
                self.map = Map.from_image(image)
                self.map.save()
            else:
                raise ValidationError(
                    f"Image must be an Map object, url, or Image, not {self.map}"
                )
        elif type(self.map) is not Map and type(self.map) is Image:
            log("converting to map...", self.map, _print=True)
            self.map = Map.from_image(self.map)
            self.map.save()
            log("converted to map", self.map, _print=True)

        if self.map and not self.map.tags:
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

    def post_save_system(self):
        # log(f"Verifying system for {self.name}: self.system={self.system}")
        if self.system.world != self:
            self.system.world = self
            self.system.save()
