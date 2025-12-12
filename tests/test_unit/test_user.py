from unittest.mock import MagicMock, patch

import pytest
from app.models.user import User  # Adjust import based on structure

# ### Notes

# 1.  **Generators**: The `worlds` property is a generator (`yield`). I converted it to a list `list(user.worlds)` to verify the contents in the test.
# 2.  **Mocking Relationships**: The core logic here relies on checking membership (`self in w.users`). I simulated this by creating mock objects and manually adding the test `user_instance` to their lists.
# 3.  **Imports**: As always, verify `app.models.user` matches your actual package structure.


class TestUserModel:
    @pytest.fixture
    def mock_world_class(self):
        """Mock the World class imported in user.py"""
        with patch("app.models.user.World") as mock_world:
            # Setup TONES constant on the class
            mock_world.TONES = {"Fantasy": "Standard fantasy setting"}
            yield mock_world

    @pytest.fixture
    def user_instance(self, mock_world_class):
        """Create a User instance."""
        # Assuming AutoUser (parent) doesn't do heavy lifting in __init__ that breaks without DB
        # If it does, we might need to patch AutoUser as well or use a concrete mock.

        # User inherits from AutoUser. Let's assume basic instantiation works.
        user = User()
        user.pk = "user_123"
        return user

    def test_world_tones_access(self, mock_world_class):
        """Test accessing World.TONES via User class."""
        # This accesses the class attribute directly
        assert User.WORLD_TONES == {"Fantasy": "Standard fantasy setting"}

    def test_worlds_property(self, user_instance, mock_world_class):
        """Test the worlds generator property."""
        # Setup mock worlds
        world1 = MagicMock()
        world1.name = "My World"
        world1.users = [user_instance]  # User is in this world

        world2 = MagicMock()
        world2.name = "Other World"
        world2.users = [MagicMock()]  # User NOT in this world

        # Mock World.all() to return these
        mock_world_class.all.return_value = [world1, world2]

        # Execute the generator
        worlds = list(user_instance.worlds)

        # Verify
        assert len(worlds) == 1
        assert worlds[0] == world1
        assert world1 in worlds
        assert world2 not in worlds

    def test_world_user_method_true(self, user_instance):
        """Test world_user returns True when user is in world.users."""
        # Mock an object that has a .world.users list
        mock_obj = MagicMock()
        mock_obj.world.users = [user_instance, MagicMock()]

        assert user_instance.world_user(mock_obj) is True

    def test_world_user_method_false(self, user_instance):
        """Test world_user returns False when user is NOT in world.users."""
        mock_obj = MagicMock()
        mock_obj.world.users = [MagicMock()]  # Different users

        assert user_instance.world_user(mock_obj) is False

    def test_default_screens_list(self, user_instance):
        """Test that screens list initializes empty."""
        assert user_instance.screens == []

    def test_current_screen_default(self, user_instance):
        """Test current_screen defaults to None."""
        assert user_instance.current_screen is None
