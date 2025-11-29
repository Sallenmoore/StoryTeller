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
    rooms = ListAttr(ReferenceAttr(choices=["DungeonRoom"]))
    entrances = ListAttr(ReferenceAttr(choices=["DungeonRoom"]))

    @property
    def associations(self):
        return [a for r in self.rooms for a in r.associations]

    @property
    def genre(self):
        return self.location.genre

    @property
    def path(self):
        return f"dungeon/{self.pk}"

    @property
    def world(self):
        return self.location.world

    def create_room(self):
        room = DungeonRoom(dungeon=self)
        room.theme = self.theme
        room.desc = self.desc
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
