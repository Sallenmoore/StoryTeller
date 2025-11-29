from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel

from autonomous import log
from models.images.map import Map
from models.ttrpgobject.character import Character


class DungeonRoom(AutoModel):
    dungeon = ReferenceAttr(choices=["Dungeon"], required=True)
    name = StringAttr(default="")
    theme = StringAttr(default="")
    desc = StringAttr(default="")
    traps = ListAttr(StringAttr(default=""))
    puzzle = StringAttr(default="")
    sensory_details = ListAttr(StringAttr(default=""))
    features = ListAttr(StringAttr(default=""))
    connected_rooms = ListAttr(ReferenceAttr(choices=["DungeonRoom"]))
    loot = ListAttr(ReferenceAttr(choices=["Item"]))
    creatures = ListAttr(ReferenceAttr(choices=["Creature"]))
    characters = ListAttr(ReferenceAttr(choices=["Character"]))
    encounters = ListAttr(ReferenceAttr(choices=["Encounter"]))
    map = ReferenceAttr(choices=["Map"])
    map_prompt = StringAttr(default="")

    _funcobj = {
        "name": "generate_room",
        "description": "builds a Room model object that is a part of an explorable, connected location, such as a dungeon, large building, or cave system",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the room. It should be more descriptive than decorative, e.g., 'Armory' instead of 'The Old Armory' ",
                },
                "theme": {
                    "type": "string",
                    "description": "The overall theme or mood of the room, such as eerie, grand, or dilapadated",
                },
                "desc": {
                    "type": "string",
                    "description": "A physical description that will be used to generate an evocative image of the location with AI",
                },
                "sensory_details": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of sensory details, such as sight, sound, smell, and touch, that a GM can use to bring the room to life",
                },
                "features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of notable features or points of interest in the room that players might investigate",
                },
                "traps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of traps or hazards that players may encounter in this room",
                },
                "puzzle": {
                    "type": "string",
                    "description": "A puzzle or challenge that players may encounter in this room",
                },
                "map_prompt": {
                    "type": "string",
                    "description": "A prompt to generate a map image for this room",
                },
            },
        },
    }

    @classmethod
    def create_from_location(cls, dungeon, location):
        if location.model_name() != "Location":
            raise ValueError("location must be a Place instance")
        room = cls(dungeon=dungeon)
        room.name = location.name
        room.theme = location.traits
        room.desc = location.desc
        room.sensory_details = location.sensory_details
        room.loot = location.items
        room.creatures = location.creatures
        room.characters = location.characters
        room.encounters = location.encounters
        room.save()
        for ass in room.associations:
            ass.parent = location
            ass.save()
        room.map = location.map
        if room.map and room not in room.map.associations:
            room.map.associations.append(room)
            room.map.save()
        room.map_prompt = location.map_prompt
        room.save()
        return room

    @property
    def associations(self):
        return self.loot + self.creatures + self.characters + self.encounters

    @property
    def genre(self):
        return self.dungeon.genre

    @property
    def path(self):
        return f"dungeonroom/{self.pk}"

    @property
    def world(self):
        return self.dungeon.world

    def delete(self, *args, **kwargs):
        if self.map and self in self.map.associations:
            if len(self.map.associations) <= 1:
                self.map.delete()
            else:
                self.map.associations.remove(self)
                self.map.save()
        for encounter in self.encounters:
            encounter.delete()
        super().delete(*args, **kwargs)

    def generate(self, prompt=""):
        # log(f"Generating data with AI for {self.name} ({self})...", _print=True)
        prompt = f"""
Generate a {self.genre} TTRPG {self.dungeon.location_type} room located in {self.dungeon.name}. {f"The dungeon is described as: {self.dungeon.description}" if self.dungeon.description else ""} {f"Relevant history: {self.dungeon.history or self.dungeon.backstory}"}. {f"This specific room is described as: {self.desc}." if self.desc else ""}

{f"This room is connected to the following rooms: {', '.join([room.desc for room in self.connected_rooms])}." if self.connected_rooms else ""}

Provide the following details for the room:

Visual Description: A detailed sensory description of the room's appearance, lighting, and atmosphere. Include logical connections to other rooms (e.g., 'north door leads to armory', 'hidden passage behind tapestry').

Sensory Details: Specific sounds, smells, or tactile sensations present in the room (e.g., dripping water, smell of burning, cold draft).

Notable Features: List a few interesting objects, architectural details, or points of interest in the room that players might investigate.

Traps (if any): Describe any traps, including their trigger, effect, and how to detect/disarm them. If none, suggest where one might fit.

Puzzle (if any): Describe a puzzle or riddle relevant to the room's theme or function.
"""
        results = self.world.system.generate_json(
            prompt=prompt,
            primer=f"Generate a dungeon room, ensuring all generated content fits the {self.genre} genre and the specific tone of the dungeon.",
            funcobj=self._funcobj,
        )
        log(results)
        if results:
            self.name = results.get("name", self.name)
            self.theme = (results.get("theme", self.theme),)
            self.desc = results.get("desc", self.desc)
            self.sensory_details = results.get("sensory_details", self.sensory_details)
            self.features = results.get("features", self.features)
            self.traps = results.get("traps", self.traps)
            self.puzzle = results.get("puzzle", self.puzzle)
            self.save()
        return self

    def generate_map(self):
        # log(f"Generating Map with AI for {self.name} ({self})...", _print=True)
        if self.map and self in self.map.associations:
            if len(self.map.associations) <= 1:
                self.map.delete()
            else:
                self.map.associations.remove(self)
                self.map.save()
        prompt = f"""{self.map_prompt}

The map should be in a {self.world.map_style} style.
"""
        self.map = Map.generate(
            prompt=prompt,
            tags=["map", "dungeon room", self.genre],
            aspect_ratio="16:9",
            image_size="4K",
        )
        self.map.save()
        self.save()
        return self.map

    def page_data(self):
        return {
            "pk": str(self.pk),
            "map": str(self.map.url()) if self.map else None,
            "name": self.name,
            "theme": self.theme,
            "desc": self.description,
            "traps": self.traps,
            "puzzle": self.puzzle,
            "sensory_details": self.sensory_details,
            "features": self.features,
            "connected_rooms": [
                {"pk": str(room.pk), "desc": room.desc} for room in self.connected_rooms
            ],
            "loot": [{"pk": str(item.pk), "name": item.name} for item in self.loot],
            "creatures": [
                {"pk": str(creature.pk), "name": creature.name}
                for creature in self.creatures
            ],
            "characters": [
                {"pk": str(char.pk), "name": char.name} for char in self.characters
            ],
            "encounters": [
                {"pk": str(enc.pk), "name": enc.name} for enc in self.encounters
            ],
        }

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    # @classmethod
    # def auto_pre_save(cls, sender, document, **kwargs):
    #     super().auto_pre_save(sender, document, **kwargs)
    #     document.pre_save_owner()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################
