import json

import pytest

from autonomous import log
from models.character import Character
from models.city import City
from models.creature import Creature
from models.faction import Faction
from models.item import Item
from models.location import Location
from models.poi import POI
from models.region import Region
from models.world import World


class TestAIIntegration:
    @pytest.mark.skip("Working")
    def test_world_generation(self, user):
        world = World.build(system="fantasy", user=user, name="The Hallows")
        bs = world.backstory
        desc = world.description
        world.generate()
        assert world.name
        assert world.backstory != bs
        assert world.description != desc
        for note in world.journal.entries:
            print(note.text)
            assert note.text

    @pytest.mark.skip("Working")
    def test_model_generation(self, world):
        models = [
            Region,
            # City,
            # POI,
            # Location,
            # Character,
            # Creature,
            # Faction,
            # Item,
        ]
        for Model in models:
            log(Model, _print=True)
            obj = Model(world=world)
            obj.save()
            bs = obj.backstory
            desc = obj.description
            obj.generate()
            assert obj.name
            assert obj.backstory != bs
            assert obj.description != desc
            for note in obj.journal.entries:
                assert note.text
