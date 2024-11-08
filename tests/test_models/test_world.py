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

# @pytest.mark.skip("Working")
class TestWorld:
    def test_create(self, user):
        world = World(name="TestWorld", user=user)
        world.save()
        assert world.name == "TestWorld"
        assert world.pk
        assert world.user.pk == user.pk

    def test_update(self, user):
        for _ in range(3):
            World(name="TestWorld", user=user).save()
        worlds = World.all()
        for world in worlds:
            assert world.user
            world.name += " --updated"
            world.backstory += " --updated"
            world.desc += " --updated"
            world.traits += " --updated"
            world.save()
        worlds = World.all()
        for world in worlds:
            assert "--updated" in world.name
            assert "--updated" in world.backstory
            assert "--updated" in world.desc
            assert "--updated" in world.traits

    def test_read(self):
        worlds = World.all()
        for world in worlds:
            wobj = World.get(world.pk)
            assert wobj

    def test_search(self, user):
        for _ in range(3):
            World(name="TestWorld", user=user).save()
        world = World.search(user=user)
        assert world

    def test_all(self, user):
        for _ in range(3):
            World(name="TestWorld", user=user).save()
        worlds = World.all()
        assert len(worlds)
        for world in worlds:
            assert world.name
            assert world.pk

    def test_attributes(self):
        pass

    def test_relations(self):
        pass


    def test_delete(self):
        worlds = World.all()
        for world in worlds:
            world.delete()
