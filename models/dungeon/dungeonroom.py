from autonomous.model.autoattr import (
    BoolAttr,
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
    is_entrance = BoolAttr(default=False)
    theme = StringAttr(default="")
    desc = StringAttr(default="")
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
                "map_prompt": {
                    "type": "string",
                    "description": "A prompt to generate a map image for this room using AI]",
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
    def location(self):
        return self.dungeon.location

    @property
    def path(self):
        return f"dungeonroom/{self.pk}"

    @property
    def world(self):
        return self.dungeon.world

    def generate(self):
        # log(f"Generating data with AI for {self.name} ({self})...", _print=True)
        prompt = f"""
Generate a {self.genre} TTRPG {self.location.location_type} room located in {self.location.name}. {f"The situation is described as: {self.dungeon.desc}" if self.dungeon.desc else ""} {f"The locations relevant history: {self.location.history or self.location.backstory}"}.

{f"The location currently has the following rooms: {', '.join([f'{room.name}: {room.desc}' for room in self.dungeon.rooms if room != self])}." if len(self.dungeon.rooms) > 1 else ""}

{f"This room is connected to the following rooms: {', '.join([f'{room.name}' for room in self.connected_rooms])}." if self.connected_rooms else ""}

{f"This specific room is described as: {self.desc}." if self.desc else ""}

Provide the following details for the room:

Visual Description: A detailed sensory description of the room's appearance, lighting, and atmosphere. Include logical connections to other rooms (e.g., 'north door leads to armory', 'hidden passage behind tapestry').

Sensory Details: Specific sounds, smells, or tactile sensations present in the room (e.g., dripping water, smell of burning, cold draft).

Notable Features: List a few interesting objects, architectural details, or points of interest in the room that players might investigate.
"""
        log(f"Prompt:\n{prompt}", _print=True)
        results = self.world.system.generate_json(
            prompt=prompt,
            primer=f"Generate a dungeon room, ensuring all generated content fits the {self.genre} genre and the specific tone of the dungeon.",
            funcobj=self._funcobj,
        )
        log(results)
        if results:
            self.name = results.get("name", self.name)
            self.theme = results.get("theme", self.theme)
            self.desc = results.get("desc", self.desc)
            self.sensory_details = results.get("sensory_details", self.sensory_details)
            self.features = results.get("features", self.features)
            self.map_prompt = results.get("map_prompt", self.map_prompt)
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

- GENRE: {self.genre}
- SCALE: 1 inch == 5 feet
- DESCRIPTION: A foreboding, expansive complex of interlinked metallic structures set within a barren, desolate landscape, perpetually shrouded in fog and mystery.

!!IMPORTANT!!: DIRECTLY OVERHEAD TOP DOWN VIEW, NO TEXT, NO CREATURES, NO CHARACTERS, NO GRID, NO UI, NO ICONS, NO SYMBOLS, NO SCALE BAR, NO LEGEND, NO WATERMARK, NO BORDER, IMAGE EDGE TO EDGE, NO TITLE, NO COMPASS ROSE, HIGH DETAIL LEVEL, VIVID COLORS, HIGH CONTRAST, DETAILED TEXTURE AND SHADING
"""
        self.map = Map.generate(
            prompt=prompt,
            tags=["map", "dungeonroom", self.genre],
            aspect_ratio="16:9",
            image_size="4K",
        )
        self.map.save()
        self.save()
        return self.map

    def is_connected(self, other_room):
        return other_room in self.connected_rooms or self in other_room.connected_rooms

    def connect(self, other_room):
        if other_room not in self.connected_rooms:
            self.connected_rooms += [other_room]
            self.save()
        if self not in other_room.connected_rooms:
            other_room.connected_rooms += [self]
            other_room.save()

    def disconnect(self, other_room):
        if other_room in self.connected_rooms:
            self.connected_rooms.remove(other_room)
            self.save()
        if self in other_room.connected_rooms:
            other_room.connected_rooms.remove(self)
            other_room.save()

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
