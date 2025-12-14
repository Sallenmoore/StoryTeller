import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from models.base.ttrpgbase import TTRPGBase  # Adjust import based on your structure
from autonomous.model.autoattr import StringAttr, IntAttr
from autonomous.model.automodel import AutoModel

# Mock dependencies that TTRPGBase imports
# This is crucial because TTRPGBase imports from models.images.image, etc.
# which might try to connect to DBs or do other things on import.
# However, for unit testing the class logic itself, we can often rely on patching
# where the class is used.
# If imports fail at the top level, we might need sys.modules patching in conftest.


class TestTTRPGBase:
    @pytest.fixture
    def concrete_ttrpg_model(self):
        """Creates a concrete subclass of TTRPGBase for testing."""

        class ConcreteItem(TTRPGBase):
            # TTRPGBase requires a 'world' attribute for many methods (e.g. current_date, events)
            # Typically this is a ReferenceAttr to a World model.
            # We'll mock it or add a dummy attr for testing.
            # In TTRPGBase it seems expected to exist or be reachable.
            # Let's add a dummy world attribute for the mock.
            pass

        # We need to simulate the 'meta' behavior if AutoModel uses it for registration
        ConcreteItem.__name__ = "ConcreteItem"
        return ConcreteItem

    @pytest.fixture
    def mock_instance(self, concrete_ttrpg_model):
        """Creates an instance of the concrete model with mocked world/system."""
        instance = concrete_ttrpg_model()
        instance.pk = "test_pk_123"
        instance.name = "Test Object"

        # Mock the 'world' object which is heavily used
        mock_world = MagicMock()
        mock_world.current_date = "2023-01-01"
        mock_world.events = []
        mock_world.image_style = "fantasy"
        mock_world.tone = "dark"
        mock_world.theme = "survival"
        mock_world.history = "Ancient history"
        mock_world.stories = []

        # Attach world to instance. In real usage this is likely a ReferenceAttr
        instance.world = mock_world

        # Mock the 'system' object used for generation
        instance.system = MagicMock()
        instance.system._titles = {"concreteitem": "Concrete Item"}
        instance.system._themes_list = {
            "concreteitem": {"themes": ["Theme A"], "motifs": ["Motif B"]}
        }

        return instance

    def test_initialization_defaults(self, concrete_ttrpg_model):
        """Test that default values are set correctly."""
        # Patch random.randint to have deterministic age
        with patch("random.randint", return_value=25):
            obj = concrete_ttrpg_model()
            assert obj.name == ""
            assert obj.backstory == ""
            assert obj.current_age == 25
            assert obj.foundry_id == ""

    def test_dunder_methods(self, mock_instance):
        """Test __eq__, __ne__, __lt__, __gt__, __hash__."""
        other = MagicMock()
        other.pk = "test_pk_123"
        other.name = "Test Object"

        # Equality
        assert mock_instance == other

        other.pk = "different_pk"
        assert mock_instance != other

        # Comparison (based on name)
        other.name = "ZObject"  # 'Test Object' < 'ZObject'
        assert mock_instance < other

        other.name = "AObject"  # 'Test Object' > 'AObject'
        assert mock_instance > other

        # Hash
        assert hash(mock_instance) == hash(mock_instance.pk)

    def test_child_list_key(self, concrete_ttrpg_model):
        """Test child_list_key class method."""
        # Using the default mapping defined in TTRPGBase
        assert TTRPGBase.child_list_key("city") == "cities"
        # Fallback
        assert TTRPGBase.child_list_key("unknown") == "unknowns"

    @patch("app.models.ttrpgbase.TTRPGBase.__subclasses__")
    def test_all_subclasses(self, mock_subclasses, concrete_ttrpg_model):
        """Test all_subclasses recursive retrieval."""

        # Setup a hierarchy: TTRPGBase -> Sub1 -> Sub2
        class Sub1(TTRPGBase):
            pass

        class Sub2(Sub1):
            pass

        # TTRPGBase.__subclasses__() returns [Sub1]
        # Sub1.__subclasses__() returns [Sub2]

        # We need to mock the return values for different calls.
        # This is tricky with a single patch.
        # Alternatively, since we defined ConcreteItem, we can just check if it appears.

        # Let's rely on the actual method logic with our dynamic class
        # concrete_ttrpg_model is a subclass of TTRPGBase

        subclasses = TTRPGBase.all_subclasses()
        # Since ConcreteItem was defined in this file, it might not be in the global registry
        # depending on how AutoModel works, but let's assume standard python inheritance.
        assert concrete_ttrpg_model in subclasses

    def test_get_model(self, concrete_ttrpg_model):
        """Test retrieving a model class by name."""
        # We need to make sure all_subclasses returns our concrete model
        with patch.object(
            TTRPGBase, "all_subclasses", return_value=[concrete_ttrpg_model]
        ):
            model_class = TTRPGBase.get_model("ConcreteItem")
            assert model_class == concrete_ttrpg_model

            # Case insensitive
            model_class = TTRPGBase.get_model("concreteitem")
            assert model_class == concrete_ttrpg_model

            # Test with PK (should call .get())
            concrete_ttrpg_model.get = MagicMock(return_value="Instance")
            instance = TTRPGBase.get_model("ConcreteItem", pk="123")
            assert instance == "Instance"
            concrete_ttrpg_model.get.assert_called_with("123")

    def test_properties(self, mock_instance):
        """Test various property getters."""
        # Age
        mock_instance.current_age = 30
        assert mock_instance.age == 30

        # Current Date (delegates to world)
        assert mock_instance.current_date == "2023-01-01"

        # Path
        # Assuming model_name() returns class name lowercased
        with patch.object(mock_instance, "model_name", return_value="concreteitem"):
            assert mock_instance.path == "concreteitem/test_pk_123"

        # Slug
        assert mock_instance.slug == "test-object"

        # Theme
        mock_instance.traits = " brave; strong "
        assert mock_instance.theme == "brave; strong"

    def test_geneology(self, mock_instance):
        """Test geneology property traversal."""
        parent = MagicMock()
        parent.parent = None
        parent.world = mock_instance.world
        mock_instance.parent = parent

        # geneology should be [world, parent] (ancestors reversed)
        # The code is: ancestors.append(obj.parent)... if world not in ancestors... return ancestors[::-1]

        # Mock add_association to avoid side effects
        mock_instance.add_association = MagicMock()

        gen = mock_instance.geneology
        assert len(gen) == 2
        assert gen[0] == mock_instance.world
        assert gen[1] == parent

    @patch("app.models.ttrpgbase.markdown.markdown")
    def test_generate_history(self, mock_markdown, mock_instance):
        """Test the generate_history method logic."""
        mock_instance.backstory = "A very long backstory..." * 10
        mock_instance.description = "A description"
        mock_instance.status = "Active"

        # Mock system generation
        mock_instance.system.generate_summary.side_effect = [
            "Short Summary",
            "Description Summary",
            "Markdown History",
        ]
        mock_markdown.return_value = "<h1>History</h1>"

        mock_instance.save = MagicMock()

        mock_instance.generate_history()

        # Verify summaries were generated
        assert mock_instance.backstory_summary == "<h1>History</h1>".replace(
            "h1>", "h3>"
        )
        assert mock_instance.description_summary == "Description Summary"
        assert mock_instance.history == "<h1>History</h1>".replace("h1>", "h3>")

        mock_instance.save.assert_called()

    @patch("app.models.ttrpgbase.get_template_attribute")
    def test_get_icon(self, mock_get_template, mock_instance):
        """Test get_icon template rendering."""
        # Mock the callable returned by get_template_attribute
        mock_macro = MagicMock(return_value="<svg>...</svg>")
        mock_get_template.return_value = mock_macro

        # Test default
        icon = mock_instance.get_icon()
        mock_get_template.assert_called()
        # The icon name is derived from get_title -> "Concrete Item" -> "concrete_item"
        args, _ = mock_get_template.call_args
        assert "concrete_item" in args[1] or "concreteitem" in args[1]
        assert icon == "<svg>...</svg>"

    def test_add_association(self, mock_instance):
        """Test adding associations."""
        obj = MagicMock()
        obj.associations = []
        obj.save = MagicMock()

        mock_instance.associations = []
        mock_instance.save = MagicMock()

        mock_instance.add_association(obj)

        assert mock_instance in obj.associations
        assert obj in mock_instance.associations
        obj.save.assert_called()
        mock_instance.save.assert_called()

        # Test adding world (should return early)
        res = mock_instance.add_association(mock_instance.world)
        assert res == mock_instance.world

    @patch("app.models.ttrpgbase.Image")
    def test_generate_image(self, MockImage, mock_instance):
        """Test AI image generation trigger."""
        mock_instance.image_prompt = "A prompt"
        mock_instance.model_name = MagicMock(return_value="concreteitem")
        mock_instance.genre = "fantasy"

        mock_generated_image = MagicMock()
        MockImage.generate.return_value = mock_generated_image

        mock_instance.save = MagicMock()

        result = mock_instance.generate_image()

        MockImage.generate.assert_called()
        assert mock_instance.image == mock_generated_image
        mock_instance.image.save.assert_called()
        mock_instance.save.assert_called()

    def test_pre_save_hooks(self, mock_instance):
        """Test pre-save logic like backstory formatting and traits."""
        # Test Backstory header replacement
        mock_instance.backstory_summary = "<h1>Title</h1>"
        mock_instance.pre_save_backstory()
        assert mock_instance.backstory_summary == "<h3>Title</h3>"

        # Test Trait generation
        mock_instance.traits = ""
        with patch("random.choice", side_effect=["Theme", "Motif"]):
            mock_instance.pre_save_traits()
            assert mock_instance.traits == "Theme; Motif"

    def test_pre_save_image_url(self, mock_instance):
        """Test pre_save_image when image is a URL string."""
        mock_instance.image = "http://example.com/image.png"
        mock_instance.image_prompt = "Prompt"
        mock_instance.image_tags = ["tag"]

        with patch("app.models.ttrpgbase.Image") as MockImage:
            with patch("app.models.ttrpgbase.validators.url", return_value=True):
                mock_img_obj = MagicMock()
                MockImage.from_url.return_value = mock_img_obj

                mock_instance.pre_save_image()

                MockImage.from_url.assert_called_with(
                    "http://example.com/image.png", prompt="Prompt", tags=["tag"]
                )
                assert mock_instance.image == mock_img_obj
                mock_img_obj.save.assert_called()
