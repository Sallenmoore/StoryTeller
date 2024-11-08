import pytest

from autonomous import log
from models.campaign.campaign import Campaign
from models.campaign.session import Session
from models.character import Character
from models.city import City
from models.creature import Creature
from models.events.calendar import Calendar
from models.events.event import Event
from models.item import Item
from models.journal import Journal, JournalEntry
from models.location import Location
from models.poi import POI
from models.region import Region
from models.user import User
from models.world import World


class TestCreature:
    def test_create(self, world):
        obj = Creature(name="TestCreature", world=world)
        obj.save()
        assert obj.name == "TestCreature"
        assert obj.pk
        assert obj.user == world.user

    def test_update(self, world):
        for _ in range(3):
            Creature(name=f"TestCreature{_}", world=world).save()
        objs = Creature.all()
        for obj in objs:
            assert obj.world
            obj.name += " --updated"
            obj.backstory += " --updated"
            obj.desc += " --updated"
            obj.traits += " --updated"
            obj.save()
        objs = Creature.all()
        for obj in objs:
            assert "--updated" in obj.name
            assert "--updated" in obj.backstory
            assert "--updated" in obj.desc
            assert "--updated" in obj.traits

    def test_read(self, world):
        for _ in range(3):
            Creature(name=f"TestCreature{_}", world=world).save()
        objs = Creature.all()
        for obj in objs:
            ret_obj = Creature.get(obj.pk)
            assert ret_obj

    def test_search(self, world):
        for _ in range(3):
            Creature(name=f"TestCreature{_}", world=world).save()
        objs = Creature.search(world=world)
        assert objs

    def test_all(self, world):
        for _ in range(3):
            Creature(name=f"TestCreature{_}", world=world).save()
        objs = Creature.all()
        assert len(objs)
        for obj in objs:
            assert obj.name
            assert obj.pk

    def test_attributes(self):
        pass

    def test_relations(self):
        pass

    def test_delete(self):
        objs = Creature.all()
        for obj in objs:
            obj.delete()
