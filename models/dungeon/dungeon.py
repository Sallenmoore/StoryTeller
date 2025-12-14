import random

from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel

from autonomous import log
from models.dungeon.dungeonroom import DungeonRoom
from models.images.map import Map
from models.ttrpgobject.character import Character


class Dungeon(AutoModel):
    location = ReferenceAttr(choices=["Location", "District"], required=True)
    theme = StringAttr(default="")
    desc = StringAttr(default="")
    map = ReferenceAttr(choices=["Map"])
    rooms = ListAttr(ReferenceAttr(choices=["DungeonRoom"]))

    @property
    def associations(self):
        return [a for r in self.rooms for a in r.associations]

    @property
    def entrances(self):
        return [e for e in self.rooms if e.is_entrance]

    @property
    def genre(self):
        return self.location.genre

    @property
    def path(self):
        return f"dungeon/{self.pk}"

    @property
    def world(self):
        return self.location.world

    def generate_map(self):
        if self.map:
            self.map.delete()
        prompt = f"""Create a top-down, black and white line art map of a TTRPG dungeon. The style should be reminiscent of {random.choice(["a hand drawn map by an individual planning something", "old parchment paper weathered by time, adorned with hand written notes along the sides in a mysterious script", "old-school 1970s/80s RPG modules: clean lines, high contrast, and minimal shading"])}. Focus purely on the layout and connectivity of the rooms. Avoid any complex furniture, rubble, or detailed textures—this map is about clarity and function.

The layout must include the following distinct areas connected by corridors:

{"\n\n".join([f"{room.name} {"[Area Entrance/Exit]" if room.is_entrance else ""}\n  - connected rooms: {[cr.name for cr in room.connected_rooms]}" for room in self.rooms])}

Ensure logical connections between these rooms with clear doorways. Entrances are noted above. The goal is a clear, valid layout.
"""
        log(prompt, _print=True)
        self.map = Map.generate(
            prompt=prompt,
            tags=["map", "dungeonroom", self.genre],
            aspect_ratio="16:9",
            image_size="2K",
            text=True,
        )
        self.map.save()
        self.save()
        return self.map

    def create_rooms(self, min_rooms, max_rooms=None):
        if max_rooms is None:
            max_rooms = min_rooms
        num_rooms = random.randint(min_rooms, max_rooms)
        for _ in range(num_rooms):
            new_room = self.create_room()
            new_room.connect(random.choice(self.rooms))
            obj = random.choice(
                *self.location.creatures,
                *self.location.characters,
                *self.location.items,
            )
            if obj:
                new_room.associations += [obj]
            new_room.save()
        return self.rooms

    def create_room(self):
        room = DungeonRoom(dungeon=self)
        room.theme = self.theme
        room.save()
        self.rooms.append(room)
        self.save()
        return room

    def create_room_from_location(self, location):
        for subroom in location.locations:
            if subroom.parent == location:
                sub_dungeon_room = self.create_room_from_location(subroom)
                self.rooms.append(sub_dungeon_room)
                subroom.delete()
        room = DungeonRoom.create_from_location(self, location)
        self.rooms.append(room)
        self.save()
        return room

    def delete(self, *args, **kwargs):
        for room in self.rooms:
            room.delete()
        super().delete(*args, **kwargs)

    def page_data(self):
        return {
            "pk": str(self.pk),
            "theme": self.theme,
            "desc": self.desc,
            "rooms": [r.page_data() for r in self.rooms],
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
