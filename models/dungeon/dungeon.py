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
from models.utility import tasks as utility_tasks


class Dungeon(AutoModel):
    location = ReferenceAttr(choices=["Location", "District", "Vehicle"], required=True)
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
        prompt = f"""Create a top-down, black and white line art map of a TTRPG dungeon. The style should be reminiscent of {random.choice(["a hand drawn map by an individual planning something", "old parchment paper weathered by time, adorned with hand written notes along the sides in a mysterious script", "bluerint-style layout in b&w: clean lines, high contrast, and minimal shading"])}. Focus purely on the layout and connectivity of the rooms. Avoid any complex furniture, rubble, or detailed textures—this map is about clarity and function.

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

    def generate_rooms(self):
        log(f"Generating rooms {len(self.rooms)} for dungeon", _print=True)
        for room in self.rooms:
            room.generate()
            log(f"Generated room {room.name} for dungeon", _print=True)
        utility_tasks.start_task(f"/generate/dungeon/{self.pk}/map")
        return self.rooms

    def create_room(self):
        room = DungeonRoom(dungeon=self)
        room.theme = self.theme
        room.save()
        if self.rooms:
            room.connect(random.choice(self.rooms))
        self.rooms.append(room)
        self.save()
        obj_list = [
            *self.location.creatures,
            *self.location.characters,
            *self.location.items,
        ]
        for obj in obj_list:
            if obj not in room.associations:
                room.associations += [random.choice(obj_list)]
            if random.randint(0, 2) > 0:
                break
        room.save()
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
