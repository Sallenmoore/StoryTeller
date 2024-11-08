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
class TestUser:
    def test_create(self):
        user = User(email="test@test.com", name="Test User")
        user.save()
        assert user.name == "Test User"
        assert user.pk

    def test_update(self):
        objs = User.all()
        for o in objs:
            o.name = "Updated User"
            o.email = "updated@test.com"
            o.save()
        objs = User.all()
        for o in objs:
            assert o.name == "Updated User"
            assert o.email == "updated@test.com"

    def test_read(self):
        objs = User.all()
        for o in objs:
            read_obj = User.get(o.pk)
            assert read_obj

    def test_search(self):
        obj = User.search(email="updated@test.com")
        assert obj

    def test_all(self):
        objs = User.all()
        for o in objs:
            assert o.name
            assert o.pk

    def test_attributes(self):
        pass

    def test_relations(self):
        pass

    def test_delete(self):
        objs = User.all()
        for o in objs:
            o.delete()
