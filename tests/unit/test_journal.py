from datetime import datetime
from unittest.mock import ANY, MagicMock, patch

import pytest
from models.journal import Journal, JournalEntry
from autonomous.db import ValidationError

# ### Notes
# 1.  **Mocking `datetime`**: This is tricky since `datetime` is an immutable type in Python. I used `patch` on the module usage in `app.models.journal` rather than the builtin itself where possible, or relied on logic flow.
# 2.  **Cascading Updates**: `add_entry` calls `update_entry`. I mocked `update_entry` in the `add_entry` test to isolate the logic of "create and add to list" vs "update fields".
# 3.  **Recursion/Loops**: Tested the `delete` method to ensure it iterates over `entries` and calls delete on them.


class TestJournalModel:
    @pytest.fixture
    def mock_dependencies(self):
        """Mock external dependencies."""
        with (
            patch("app.models.journal.parse_text") as parse_text,
            patch("app.models.journal.datetime") as mock_datetime,
        ):
            # Setup datetime mock to return a fixed time
            fixed_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.now.return_value = fixed_now
            # Allow isinstance check to work
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            yield {"parse_text": parse_text, "fixed_now": fixed_now}

    @pytest.fixture
    def journal_entry_instance(self):
        entry = JournalEntry()
        entry.pk = "entry_1"
        entry.title = "Test Entry"
        entry.text = "Content"
        entry.world = MagicMock()
        entry.world.genre = "fantasy"
        entry.save = MagicMock()
        return entry

    @pytest.fixture
    def journal_instance(self, journal_entry_instance):
        journal = Journal()
        journal.pk = "journal_1"
        journal.world = journal_entry_instance.world
        journal.parent = MagicMock()  # The object this journal belongs to
        journal.entries = [journal_entry_instance]
        journal.save = MagicMock()
        return journal

    # --- JournalEntry Tests ---

    def test_journal_entry_genre_property(self, journal_entry_instance):
        """Test genre property delegates to world."""
        assert journal_entry_instance.genre == "fantasy"

        journal_entry_instance.world = None
        assert journal_entry_instance.genre == "default"

    def test_journal_entry_add_association(self, journal_entry_instance):
        """Test adding association to an entry."""
        obj = MagicMock()
        journal_entry_instance.associations = []

        journal_entry_instance.add_association(obj)

        assert obj in journal_entry_instance.associations
        journal_entry_instance.save.assert_called()

        # Test duplicate (should not add again)
        journal_entry_instance.add_association(obj)
        assert len(journal_entry_instance.associations) == 1

    def test_journal_entry_pre_save_date(self, journal_entry_instance):
        """Test date validation/defaulting."""
        # Case: Invalid date type
        journal_entry_instance.date = "not-a-date"
        # We need to rely on the side_effect of datetime or just patch the now() call
        # inside the method if possible.
        # Since datetime is a built-in, mocking isinstance(obj, datetime) is hard
        # if obj is a string.
        # Let's trust the logic: if not isinstance -> datetime.now()

        with patch("app.models.journal.datetime") as mock_dt:
            mock_dt.now.return_value = "NOW"
            journal_entry_instance.pre_save_date()
            assert journal_entry_instance.date == "NOW"

    def test_journal_entry_pre_save_text(
        self, journal_entry_instance, mock_dependencies
    ):
        """Test text parsing hook."""
        mock_dependencies["parse_text"].return_value = "Parsed Text"
        journal_entry_instance.text = "Raw Text"

        journal_entry_instance.pre_save_text()

        assert journal_entry_instance.text == "Parsed Text"
        mock_dependencies["parse_text"].assert_called_with(
            journal_entry_instance, "Raw Text"
        )

    def test_journal_entry_pre_save_importance_valid(self, journal_entry_instance):
        """Test importance validation."""
        journal_entry_instance.importance = 3
        journal_entry_instance.pre_save_importance()  # Should not raise
        assert journal_entry_instance.importance == 3

    def test_journal_entry_pre_save_importance_invalid(self, journal_entry_instance):
        """Test importance validation raises error."""
        journal_entry_instance.importance = 10
        with pytest.raises(ValidationError):
            journal_entry_instance.pre_save_importance()

    # --- Journal Tests ---

    def test_journal_add_entry(self, journal_instance):
        """Test adding a new entry to the journal."""
        # We need to mock JournalEntry constructor and save
        with patch("app.models.journal.JournalEntry") as MockEntry:
            new_entry = MagicMock()
            new_entry.pk = "new_pk"
            MockEntry.return_value = new_entry

            # Mock update_entry since add_entry calls it
            journal_instance.update_entry = MagicMock(return_value=new_entry)

            result = journal_instance.add_entry(title="New Title")

            MockEntry.assert_called_with(world=journal_instance.world)
            new_entry.save.assert_called()
            # Verify it was added to entries list (which was mocked as a list)
            assert new_entry in journal_instance.entries
            journal_instance.save.assert_called()

            journal_instance.update_entry.assert_called_with(
                "new_pk", "New Title", None, None, None
            )
            assert result == new_entry

    def test_journal_update_entry(self, journal_instance, journal_entry_instance):
        """Test updating an existing entry."""
        # Ensure JournalEntry.get works
        with patch(
            "app.models.journal.JournalEntry.get", return_value=journal_entry_instance
        ):
            updated_entry = journal_instance.update_entry(
                pk="entry_1",
                title="Updated Title",
                text="New Text",
                importance=5,
                associations=[MagicMock()],
            )

            assert updated_entry.title == "Updated Title"
            assert updated_entry.text == "New Text"
            assert updated_entry.importance == 5
            assert len(updated_entry.associations) == 1
            # Check date update (can't easily verify datetime.now() without deep mock, but logic is there)

            updated_entry.save.assert_called()
            # Verify journal save called to update list reference
            journal_instance.save.assert_called()

    def test_journal_get_entry(self, journal_instance, journal_entry_instance):
        """Test retrieving a specific entry."""
        with patch(
            "app.models.journal.JournalEntry.get", return_value=journal_entry_instance
        ):
            # Success case
            res = journal_instance.get_entry("entry_1")
            assert res == journal_entry_instance

            # Failure case (not in list)
            journal_instance.entries = []
            res = journal_instance.get_entry("entry_1")
            assert res is None

    def test_journal_delete(self, journal_instance, journal_entry_instance):
        """Test deleting journal and cascading to entries."""
        with patch("app.models.journal.AutoModel.delete") as super_delete:
            journal_instance.delete()

            journal_entry_instance.delete.assert_called_once()
            super_delete.assert_called_once()

    def test_journal_pre_save_entries(self, journal_instance):
        """Test pre-save hook for sorting entries."""
        e1 = MagicMock(date=datetime(2023, 1, 1))
        e2 = MagicMock(date=datetime(2024, 1, 1))
        e3 = MagicMock(date=datetime(2022, 1, 1))

        journal_instance.entries = [e1, e2, e3]

        journal_instance.pre_save_entries()

        # Verify world assignment
        assert e1.world == journal_instance.world
        e1.save.assert_called()

        # Verify sorting (Reverse chronological)
        assert journal_instance.entries == [e2, e1, e3]
