import json
import random

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from models.autogm import AutoGM
from models.base.ttrpgbase import TTRPGBase
from models.journal import Journal
from models.systems import (
    FantasySystem,
    HardboiledSystem,
    HistoricalSystem,
    HorrorSystem,
    PostApocalypticSystem,
    SciFiSystem,
    WesternSystem,
)
from models.ttrpgobject.character import Character
from models.ttrpgobject.city import City
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.district import District
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.location import Location
from models.ttrpgobject.region import Region


class World(TTRPGBase):
    system = ReferenceAttr(choices=["BaseSystem"])
    users = ListAttr(ReferenceAttr(choices=["User"]))
    gm = ReferenceAttr(choices=[AutoGM])
    map = ReferenceAttr(choices=["Image"])
    current_date = StringAttr(
        default=lambda: f"{random.randint(1, 30)}, {random.choice(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec' ])} {random.randint(1, 5000)}"
    )

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

        ### set attributes ###
        if not name.strip():
            name = f"{system._genre} Setting"
        if not desc.strip():
            desc = f"An expansive, complex, and mysterious {system._genre} setting suitable for a {system._genre} {system.get_title(cls)}."
        if not backstory.strip():
            backstory = f"{name} is filled with curious and dangerous points of interest filled with various creatures and characters. The complex and mysterious history of this world is known only to a few reclusive individuals. Currently, there are several factions vying for power through poltical machinations, subterfuge, and open warfare."

        log(f"Building world {name}, {desc}, {backstory}, {system}, {user}")

        world = cls(
            name=name,
            desc=desc,
            backstory=backstory,
            system=system,
            users=[user],
        )
        system.world = world
        user.worlds += [world]
        world.save()
        system.save()
        user.save()
        cls.update_system_references(world.pk)
        return world

    @classmethod
    def update_system_references(cls, pk):
        if obj := cls.get(pk):
            world_data = obj.page_data()
            obj.system.text_agent.get_client().clear_files()
            ref_db = json.dumps(world_data).encode("utf-8")
            obj.system.text_agent.attach_file(
                ref_db, filename=f"{obj.slug}-dbdata.json"
            )

            obj.system.json_agent.get_client().clear_files()
            ref_db = json.dumps(world_data).encode("utf-8")
            obj.system.json_agent.attach_file(
                ref_db, filename=f"{obj.slug}-dbdata.json"
            )

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
            *self.regions,
            *self.districts,
        ]

    @associations.setter
    def associations(self, obj):
        if obj.world != self:
            obj.world = self
            obj.save()

    @property
    def characters(self):
        return Character.search(world=self) if self.pk else []

    @property
    def cities(self):
        return City.search(world=self) if self.pk else []

    @property
    def creatures(self):
        return Creature.search(world=self) if self.pk else []

    @property
    def districts(self):
        return District.search(world=self) if self.pk else []

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
        return f"A full color, high resolution illustrated map of a fictional {self.genre} setting called {self.name} and described as {self.desc or 'filled with points of interest to explore, antagonistic factions, and a rich, mysterious history.'}"

    @property
    def locations(self):
        return Location.search(world=self) if self.pk else []

    @property
    def parent(self):
        return None

    @property
    def players(self):
        return Character.search(world=self, is_player=True) if self.pk else []

    @property
    def parties(self):
        return Faction.search(world=self, is_player_faction=True) if self.pk else []

    @property
    def player_faction(self):
        return Faction.find(world=self, is_player_faction=True) if self.pk else None

    @player_faction.setter
    def player_faction(self, obj):
        if self.pk and obj:
            if result := Faction.find(world=self, is_player_faction=True):
                result.is_player_faction = False
                result.save()
            obj.is_player_faction = True
            obj.save()

    @property
    def regions(self):
        return Region.search(world=self) if self.pk else []

    ########################## Override Methods #############################

    def delete(self):
        objs = [
            self.gm,
            self.system,
            *Region.search(world=self),
            *City.search(world=self),
            *Location.search(world=self),
            *District.search(world=self),
            *Faction.search(world=self),
            *Creature.search(world=self),
            *Character.search(world=self),
            *Item.search(world=self),
        ]
        for obj in objs:
            if obj:
                obj.delete()
        for user in self.users:
            if self in user.worlds:
                user.worlds.remove(self)
                user.save()
        return super().delete()

    ###################### Boolean Methods ########################

    def is_associated(self, obj):
        return self == obj.world

    def is_user(self, user):
        return user in self.users

    ###################### Getter Methods ########################
    def get_world(self):
        return self

    def add_association(self, obj):
        obj.world = self
        obj.save()
        return self.associations

    ###################### Data Methods ########################
    ################### Instance Methods #####################
    def page_data(self):
        response = {
            "worldname": self.name,
            "genre": self.genre,
            "backstory": self.backstory,
            "current_date": self.current_date,
            "world_objects": {
                "Regions": [o.page_data() for o in self.regions],
                "Locations": [o.page_data() for o in self.locations],
                "Cities": [o.page_data() for o in self.cities],
                "Factions": [o.page_data() for o in self.factions],
                "Characters": [o.page_data() for o in self.characters],
                "Items": [o.page_data() for o in self.items],
                "Creatures": [o.page_data() for o in self.creatures],
                "Districts": [o.page_data() for o in self.districts],
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
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_system()

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)
        document.post_save_system()
        document.post_save_gm()
        document.post_save_users()

    # def clean(self):
    #     super().clean()

    ################### verification methods ##################

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
            raise ValidationError(
                f"{self.name} is not the world for system: {self.system}"
            )

    def post_save_gm(self):
        if not self.gm:
            gm = AutoGM(world=self)
            gm.save()
            self.gm = gm
            self.save()

    def post_save_users(self):
        for user in self.users:
            if self not in user.worlds:
                raise ValidationError(f"{user.name} is not a user of {self.name}")
