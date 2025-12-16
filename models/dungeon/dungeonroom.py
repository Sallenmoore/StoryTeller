import random

from autonomous.model.autoattr import (
    BoolAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel

from autonomous import log
from models.images.map import Map
from models.stories.encounter import Encounter
from models.ttrpgobject.character import Character
from models.utility import parse_attributes
from models.utility import tasks as utility_tasks


class DungeonRoom(AutoModel):
    dungeon = ReferenceAttr(choices=["Dungeon"], required=True)
    name = StringAttr(default="")
    foundry_client_id = StringAttr(default="")
    foundry_id = StringAttr(default="")
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
    structure_type = StringAttr(default="")
    dimensions = StringAttr(default="")
    shape = StringAttr(default="")
    map = ReferenceAttr(choices=["Map"])
    map_prompt = StringAttr(default="")

    _funcobj = {
        "name": "generate_sub_location",
        "description": "builds a location object that is a part of an explorable, connected location, such as a dungeon, large building, or cave system",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the location. It should be more descriptive than decorative, e.g., 'Armory' instead of 'The Old Armory' ",
                },
                "structure_type": {
                    "type": "string",
                    "description": "The structural category of this area, such as Room, Hallway, Crypt, Chamber, Vault, Corridor, Gallery, Tunnel, Cavern, etc. 'Hallway' implies length and connectivity; 'Chamber' implies size and height; 'Room' implies a standard enclosure; etc.",
                },
                "dimensions": {
                    "type": "string",
                    "description": "The approximate size and shape (e.g., '10ft wide by 60ft long', '40ft diameter circle', 'Irregular cavern approx 100ft across').",
                },
                "theme": {
                    "type": "string",
                    "description": "The overall theme or mood of the location, such as eerie, grand, or dilapadated",
                },
                "shape": {
                    "type": "string",
                    "description": "The general shape of the room, such as rectangular, circular, or irregular",
                },
                "desc": {
                    "type": "string",
                    "description": "A vivid physical description of the area, focusing on its specific structural type (e.g., describing the length of a hallway or the height of a chamber).",
                },
                "sensory_details": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Distinct sensory inputs (smell, sound, temperature) that characterize the area.",
                },
                "features": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Notable structural or decorative features (e.g., 'A collapsed ceiling', 'A row of statues', 'A deep chasm').",
                },
                "map_prompt": {
                    "type": "string",
                    "description": "A precise prompt for an AI image generator to create a top-down battlemap. It MUST include the structure type and dimensions (e.g., 'A long, narrow stone corridor, 10ft wide, 60ft long, top-down battlemap, black and white line art').",
                },
            },
        },
    }

    @property
    def associations(self):
        return self.loot + self.creatures + self.characters + self.encounters

    @associations.setter
    def associations(self, value):
        self.loot = [
            a for a in value if a.model_name().lower() == "item" and a not in self.loot
        ]
        self.creatures = [
            a
            for a in value
            if a.model_name().lower() == "creature" and a not in self.creatures
        ]
        self.characters = [
            a
            for a in value
            if a.model_name().lower() == "character" and a not in self.characters
        ]
        self.encounters = [
            a
            for a in value
            if a.model_name().lower() == "encounter" and a not in self.encounters
        ]

    @property
    def description(self):
        return self.desc

    @property
    def layout(self):
        return (
            f"""
A {self.shape} shaped {self.structure_type} that is {self.dimensions}
"""
            if self.shape or self.structure_type or self.dimensions
            else ""
        )

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
Generate a {self.genre} TTRPG {self.structure_type or self.location.location_type} located in {self.location.name}. {f"The locations relevant history: {self.location.history or self.location.backstory}"}. {f"The area is described as: {self.dungeon.desc}" if self.dungeon.desc else ""}

{f"The location currently has the following areas: \n\n{'\n\n'.join([f'{room.name} [{room.structure_type}]: {room.desc}' for room in self.dungeon.rooms if room != self and room.desc])}." if len(self.dungeon.rooms) > 1 else ""}

{f"This area has {len(self.connected_rooms)} entrances/exits and is connected to the following areas: {','.join([room.name for room in self.connected_rooms])}." if self.connected_rooms else ""}

{f"This specific area is described as: {self.layout}, {self.theme}, {self.desc}." if self.desc or self.theme or self.layout else ""}

{"and has the following features:" + ", ".join(self.features) if self.features else ""}

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
            self.structure_type = results.get("structure_type", self.structure_type)
            self.dimensions = results.get("dimensions", self.dimensions)
            self.shape = results.get("shape", self.shape)
            if self.save():
                if not self.map:
                    utility_tasks.start_task(f"/generate/dungeon/room/{self.pk}/map")
                if not self.encounters:
                    utility_tasks.start_task(
                        f"/generate/dungeon/room/{self.pk}/encounter"
                    )
        return self

    def generate_encounter(self):
        enc = Encounter(world=self.world, parent=self.location)
        enc.theme = self.theme
        if self.creatures:
            enc.encounter_type = random.choice(["combat", "stealth"])
            enc.enemy_type = random.choice(self.creatures).name
        elif self.characters:
            enc.encounter_type = random.choice(["social interaction", "stealth"])
            enc.enemy_type = random.choice(self.characters).species
        else:
            enc.encounter_type = random.choice(["puzzle or trap", "skill challenge"])
            enc.enemy_type = "environmental challenge"
        enc.story = (
            random.choice(self.location.stories) if self.location.stories else None
        )
        enc.backstory = f"""
An encounter set in {self.name}, a {self.dimensions} {self.shape} {self.structure_type} in the {self.location.location_type} known as {self.location.name}.
The area is described as: {self.desc}.

{"The area has the following features: " + ", ".join(self.features) if self.features else "No specific features are noted."}

{"The area has the following characters/creatures: " + ", ".join([f"{a.name}: {a.backstory}" for a in self.characters + self.creatures]) if self.characters or self.creatures else "The challenge should be environmental, not an antagonist."}

{f"This area is an entrance/exit to the {self.location.location_type} known as {self.location.name}." if self.is_entrance else ""}
"""
        enc.associations = self.associations
        enc.save()
        self.encounters += [enc]
        self.save()
        enc.generate()
        enc.save()

    def build_map_prompt(self):
        base_prompt = f"Top-down 2D battlemap of a {self.theme} {self.structure_type} named {self.name}. "
        style = (
            f"Use a {self.world.map_style} RPG battlemap style, vivid, high contrast."
        )

        # Logic to handle long corridors vs rooms
        if any(
            st in self.structure_type.lower()
            for st in [
                "hallway",
                "corridor",
                "tunnel",
                "passage",
                "pathway",
                "walkway",
                "shaft",
                "channel",
            ]
        ):
            structure_desc = f"A long {self.shape} segment of {self.structure_type}, approx dimensions for scale: {self.dimensions}. Open ends for tiling."
        else:
            structure_desc = f"A detailed layout of a {self.shape} shaped {self.structure_type}, approx dimensions for scale: {self.dimensions}."

        details = f"{self.map_prompt} Features: {', '.join(self.features)}."

        constraints = "DIRECT OVERHEAD, TOP-DOWN ORTHOGRAPHIC 2D PROJECTION. NO 3D perspective, NO isometric view, NO characters, NO text, NO UI. NO GRID, NO ICONS, NO SYMBOLS, NO SCALE BAR, NO LEGEND, NO WATERMARK, NO BORDER, MAP SPANS EDGE TO EDGE, NO TITLE, NO COMPASS ROSE, HIGH DETAIL LEVEL, VIVID COLORS, HIGH CONTRAST"

        prompt = f"{base_prompt} {style} {structure_desc} {details} \n\n !!IMPORTANT: {constraints}"
        log(f"Map Prompt:\n{prompt}", _print=True)
        return prompt

    def generate_map(self):
        # log(f"Generating Map with AI for {self.name} ({self})...", _print=True)
        if self.map:
            if self.map == self.location.map:
                self.map = None
            else:
                self.map.delete()

        if map := Map.generate(
            prompt=self.build_map_prompt(),
            tags=["map", "dungeonroom", self.genre],
            aspect_ratio="16:9",
            image_size="4K",
        ):
            self.map = map
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
        if self.map:
            self.map.delete()
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

    def to_foundry(self):
        return self.location.system.foundry_export(self)

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_text()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################
    def pre_save_text(self):
        for attr in [
            "name",
            "desc",
            "theme",
            "structure_type",
            "dimensions",
            "shape",
            "map_prompt",
        ]:
            if v := getattr(self, attr):
                if isinstance(v, str) and any(ch in v for ch in ["#", "*", "- "]):
                    v = parse_attributes.parse_text(self, v.strip())
                setattr(self, attr, v.strip())
