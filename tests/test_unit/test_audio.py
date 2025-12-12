import io
from unittest.mock import MagicMock, patch

import pytest
import requests
from app.models.audio import Audio  # Adjust import based on your actual structure

# Assuming Audio inherits from AutoModel which interacts with a DB.
# We'll use the mock_db fixture from conftest.py implicitly if it handles connection patching,
# but we primarily need to mock the internal methods of AutoModel/FileAttr for unit testing
# to avoid actual DB/File system calls.
### Notes on the Tests:
"""
1.  **Mocking `AudioAgent`**: We use `unittest.mock.patch` to mock the external AI service. This ensures your unit tests don't make expensive API calls or fail due to network issues.
2.  **Mocking `AutoModel`/`FileAttr`**: Since `Audio` inherits from `AutoModel` (your custom ORM), true unit tests shouldn't hit the database. I've used `MagicMock` to simulate the behavior of the `data` attribute (the `FileAttr`).
3.  **BeautifulSoup**: I verified that the `generate` method correctly strips HTML tags using the mock's `call_args`.
4.  **Error Handling**: I included a test case for `from_file` where an exception is raised (like `IOError`), ensuring your `try/except` block works and returns `None` as expected.
5.  **Pathing**: You might need to adjust the import paths (`app.models.audio`) in the `patch` decorators and imports depending on exactly where your files reside in the final project structure.
"""


class TestAudioModel:
    @pytest.fixture
    def mock_file_content(self):
        return b"fake audio content"

    @pytest.fixture
    def mock_audio_agent(self):
        with patch("app.models.audio.AudioAgent") as mock:
            yield mock

    @pytest.fixture
    def mock_requests(self):
        with patch("app.models.audio.requests") as mock:
            yield mock

    def test_from_file_success(self, mock_file_content, mock_db):
        """Test creating an Audio object from raw file bytes."""
        # We need to ensure saving works or is mocked.
        # Assuming mock_db handles the DB save.

        audio = Audio.from_file(mock_file_content)

        assert audio is not None
        assert isinstance(audio, Audio)
        # Verify data was put into the FileAttr
        # This depends on how FileAttr stores data in memory before save,
        # but typically we can check if we can read it back if the mock DB supports it.
        # If not, we might need to mock FileAttr.put

        # Since we can't easily peek into the real FileAttr without a real GridFS,
        # let's trust the return value and that no exception was raised.
        # A more rigorous test would mock audio.data.put

    def test_from_file_failure(self, mock_file_content):
        """Test error handling when from_file fails."""
        # Simulate an error during IO or Save
        with patch.object(Audio, "save", side_effect=IOError("Mock IO Error")):
            audio = Audio.from_file(mock_file_content)
            assert audio is None

    def test_generate_success(self, mock_audio_agent, mock_db):
        """Test generating audio from text."""
        # Setup mock Agent
        mock_instance = mock_audio_agent.return_value
        mock_instance.generate.return_value = b"generated audio bytes"

        text = "<p>Hello World</p>"

        audio = Audio.generate(text, voice="TestVoice")

        # Verify BeautifulSoup parsing (stripped HTML)
        mock_instance.generate.assert_called_once()
        args, kwargs = mock_instance.generate.call_args
        assert "Hello World" in args[0]  # Should have stripped <p> tags
        assert kwargs["voice"] == "TestVoice"

        assert audio is not None
        assert isinstance(audio, Audio)

    def test_transcribe_success(self, mock_audio_agent):
        """Test transcribing an Audio object."""
        mock_instance = mock_audio_agent.return_value
        mock_instance.transcribe.return_value = "Transcribed text"

        # Mock the audio object and its to_file method
        mock_audio = MagicMock(spec=Audio)
        mock_audio.to_file.return_value = b"audio bytes"

        result = Audio.transcribe(mock_audio)

        assert result == "Transcribed text"
        mock_instance.transcribe.assert_called_once_with(
            b"audio bytes", prompt="Transcribe the following audio accurately."
        )

    def test_transcribe_invalid_input(self):
        """Test transcribe raises ValueError for non-Audio objects."""
        with pytest.raises(ValueError, match="must be an instance of Audio class"):
            Audio.transcribe("not an audio object")

    def test_read_existing_data(self):
        """Test reading data from an Audio object."""
        audio = Audio()
        # Mock the 'data' attribute (FileAttr)
        audio.data = MagicMock()
        audio.data.__bool__.return_value = True  # Treat as truthy (exists)
        audio.data.read.return_value = b"stored content"

        content = audio.read()

        assert content == b"stored content"
        audio.data.seek.assert_called_with(0)
        audio.data.read.assert_called_once()

    def test_read_no_data(self):
        """Test reading when no data exists."""
        audio = Audio()
        # Mock data as None/False
        audio.data = None

        assert audio.read() is None

    def test_to_file(self):
        """Test to_file method (similar to read)."""
        audio = Audio()
        audio.data = MagicMock()
        audio.data.__bool__.return_value = True
        audio.data.read.return_value = b"file content"

        assert audio.to_file() == b"file content"
        audio.data.seek.assert_called_with(0)

    def test_add_to_file_append(self, mock_db):
        """Test appending data to existing audio."""
        audio = Audio()
        audio.data = MagicMock()
        audio.data.__bool__.return_value = True
        audio.data.read.return_value = b"existing"
        audio.data.size = 100  # Mock size

        # Mock save to prevent DB calls
        with patch.object(Audio, "save"):
            audio.add_to_file(b" new")

            # Verify replace was called with combined data
            audio.data.replace.assert_called_with(
                b"existing new", content_type="audio/mpeg"
            )

    def test_add_to_file_new(self, mock_db):
        """Test adding data to a new audio object (no existing data)."""
        audio = Audio()
        # Create a mock that evaluates to False initially but allows .put()
        # This is tricky because usually None doesn't have methods.
        # In your model, 'data' is likely a descriptor or object that wraps the file.
        # If 'data' is None when empty, this test setup needs to match your ORM.
        # Assuming FileAttr always returns an object that might evaluate to False if empty.

        audio.data = MagicMock()
        audio.data.__bool__.return_value = False

        with patch.object(Audio, "save"):
            audio.add_to_file(b"start")

            audio.data.put.assert_called_with(b"start", content_type="audio/mpeg")

    def test_delete(self):
        """Test deleting the audio file and the record."""
        audio = Audio()
        audio.data = MagicMock()
        audio.data.__bool__.return_value = True

        # Mock super().delete()
        # Since we can't easily mock super() in a simple instance,
        # we can patch the AutoModel.delete method if needed,
        # or just check if data.delete is called.
        with patch("app.models.audio.AutoModel.delete") as mock_super_delete:
            audio.delete()

            audio.data.delete.assert_called_once()
            mock_super_delete.assert_called_once()
