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
class TestRelations:
    def test_user_relations(self):
        user = User(email="test@test.com", name="Test User")
        user.save()
        world = World(name="TestWorld-Relations", user=user)
        world.save()
        assert world.user

    def test_region_relations(self, user):
        world = World(name="TestWorld-Relations", user=user)
        world.save()
        region = Region(name="TestRegion", world=world)
        region.save()
        world.associations.append(region)
        world.save()
        assert world.associations[0].name == "TestRegion"
        assert world.associations[0].world.name == "TestWorld-Relations"
        assert world.associations[0].world.user.name == "Test User"
        assert world.associations[0].image.url()
