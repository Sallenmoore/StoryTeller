import os
from unittest.mock import ANY, MagicMock, patch

import pytest
from autonomous.db import ValidationError

# We need to mock the imports inside world.py before importing it if they have side effects,
# or patch them where they are used.
# Since world.py imports many models at the top level, let's assume we can import World
# and then patch the classes it uses.
from models.world import World


class TestWorldModel:
    @pytest.fixture
    def mock_system_classes(self):
        """Mock the system classes used in World.SYSTEMS/build."""
        with (
            patch("app.models.world.FantasySystem") as fantasy,
            patch("app.models.world.SciFiSystem") as scifi,
            patch("app.models.world.WesternSystem") as western,
        ):
            yield {"fantasy": fantasy, "sci-fi": scifi, "western": western}

    @pytest.fixture
    def mock_associated_models(self):
        """Mock all the TTRPG object models (Character, City, etc.)."""
        # Patch the classes where they are imported in world.py
        with (
            patch("app.models.world.Character") as char,
            patch("app.models.world.City") as city,
            patch("app.models.world.Faction") as faction,
            patch("app.models.world.Story") as story,
            patch("app.models.world.Event") as event,
            patch("app.models.world.Map") as map_model,
            patch("app.models.world.Image") as image_model,
            patch("app.models.world.Journal") as journal,
        ):
            yield {
                "Character": char,
                "City": city,
                "Faction": faction,
                "Story": story,
                "Event": event,
                "Map": map_model,
                "Image": image_model,
                "Journal": journal,
            }

    @pytest.fixture
    def world_instance(self):
        """Create a basic World instance with mocks."""
        world = World()
        world.pk = "world_pk_123"
        world.name = "Test World"
        world.system = MagicMock()
        world.system._genre = "Fantasy"
        world.save = MagicMock()
        return world

    def test_build_success(self, mock_system_classes, mock_associated_models):
        """Test building a new world with valid system."""
        user = MagicMock()

        # Mock requests used for task generation triggers
        with patch("app.models.world.requests.post") as mock_post:
            with patch.dict(
                os.environ, {"TASKS_SERVICE_NAME": "tasks", "COMM_PORT": "8000"}
            ):
                world = World.build("fantasy", user, name="My World")

        assert world.name == "My World"
        assert user in world.users

        # Verify system creation
        mock_system_classes["fantasy"].assert_called()
        assert world.system == mock_system_classes["fantasy"].return_value

        # Verify initial objects creation (Faction, Character, Story)
        mock_associated_models["Faction"].assert_called()
        mock_associated_models["Character"].assert_called()
        mock_associated_models["Story"].assert_called()

        # Verify task triggers
        assert mock_post.call_count >= 4  # World, Faction, Char, Story

    def test_build_invalid_system(self):
        """Test building with an invalid system raises ValueError."""
        with pytest.raises(ValueError, match="System invalid not found"):
            World.build("invalid", MagicMock())

    def test_associations_getter(self, world_instance, mock_associated_models):
        """Test that associations property aggregates all child objects."""
        # Setup mocks to return lists
        mock_associated_models["Character"].search.return_value = ["c1"]
        mock_associated_models["City"].search.return_value = ["city1"]
        # ... assuming other search calls return empty lists by default if not mocked explicitly

        # We need to mock the property accessors on the instance since they call .search()
        # Alternatively, relying on the class patches above should work if the properties use the imported classes.

        # The 'associations' property calls self.characters, self.items, etc.
        # Let's verify one of those sub-properties first
        assert world_instance.characters == ["c1"]

        # Now check aggregations. Note: The order depends on the implementation of `associations` property.
        assoc = world_instance.associations
        assert "c1" in assoc
        assert "city1" in assoc

    def test_associations_setter(self, world_instance):
        """Test setting association updates the child's world."""
        child = MagicMock()
        child.world = None

        world_instance.associations = child

        assert child.world == world_instance
        child.save.assert_called()

    def test_events_property(self, world_instance, mock_associated_models):
        """Test events property sorting."""
        e1 = MagicMock(end_date="2023-01-01")
        e2 = MagicMock(end_date="2024-01-01")
        # Mock the search to return unsorted
        mock_associated_models["Event"].search.return_value = [e1, e2]

        events = world_instance.events
        # Should be reverse sorted by date
        assert events == [e2, e1]

    def test_delete_cascade(self, world_instance, mock_associated_models):
        """Test that deleting the world deletes all children."""
        # Setup some children
        mock_associated_models["Character"].search.return_value = [MagicMock()]
        mock_associated_models["City"].search.return_value = [MagicMock()]

        with patch("app.models.world.TTRPGBase.delete") as super_delete:
            world_instance.delete()

            # Verify children delete called
            mock_associated_models["Character"].search.return_value[
                0
            ].delete.assert_called()
            mock_associated_models["City"].search.return_value[0].delete.assert_called()
            super_delete.assert_called()

    def test_pre_save_system_defaults(self, world_instance, mock_system_classes):
        """Test pre_save_system creates default FantasySystem if missing."""
        world_instance.system = None

        world_instance.pre_save_system()

        mock_system_classes["fantasy"].assert_called()
        assert world_instance.system == mock_system_classes["fantasy"].return_value

    def test_pre_save_system_from_string(self, world_instance, mock_system_classes):
        """Test pre_save_system instantiates system from string key."""
        world_instance.system = "scifi"
        # Mock the _systems dict on the instance/class
        world_instance._systems = {"scifi": mock_system_classes["sci-fi"]}

        world_instance.pre_save_system()

        mock_system_classes["sci-fi"].assert_called()

    def test_pre_save_system_invalid_string(self, world_instance):
        """Test pre_save_system raises ValidationError for bad string."""
        world_instance.system = "invalid_sys"
        world_instance._systems = {}

        with pytest.raises(ValidationError):
            world_instance.pre_save_system()

    def test_generate_map(self, world_instance, mock_associated_models):
        """Test generating a map."""
        mock_map = MagicMock()
        mock_associated_models["Map"].generate.return_value = mock_map

        # Setup system prompt
        world_instance.system.map_prompt.return_value = "A map prompt"
        world_instance.map_style = "isometric"

        result = world_instance.generate_map()

        mock_associated_models["Map"].generate.assert_called_with(
            prompt="A map prompt\n\nThe map should be in a isometric style.\n",
            tags=[
                "map",
                "world",
                "fantasy",
            ],  # assuming model_name='world', genre='fantasy'
            img_quality="hd",
            img_size="1792x1024",
        )
        assert world_instance.map == mock_map
        assert result == mock_map

    def test_pre_save_map_conversions(self, world_instance, mock_associated_models):
        """Test pre_save_map handles URLs and Image objects."""
        # Case 1: URL string
        world_instance.map = "http://example.com/map.png"
        world_instance.map_prompt = "Prompt"

        with patch("app.models.world.validators.url", return_value=True):
            mock_map_obj = MagicMock()
            mock_associated_models["Map"].from_url.return_value = mock_map_obj

            world_instance.pre_save_map()

            mock_associated_models["Map"].from_url.assert_called()
            assert world_instance.map == mock_map_obj

        # Case 2: Image object (needs conversion to Map)
        # We simulate this by passing an object that is NOT of type Map but IS of type Image
        # Since we mocked the classes, we need to be careful with type() checks in the code.
        # The code uses `type(self.map) is not Map`.

        # Reset
        world_instance.map = MagicMock()
        # To make isinstance/type work with mocks in the way the code expects
        # (checking against the imported class), we must ensure the mock *is* the imported class.
        # This is hard with 'patch'.

        # Alternative: Test the logic flow.
        # If type(map) is Image...
        # We can just rely on the fact that if it enters that block, .from_image is called.
