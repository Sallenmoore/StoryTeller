from unittest.mock import MagicMock

import pytest
import requests

from autonomous import log
from autonomous.ai.jsonagent import JSONAgent
from models.autogm.autogm import AutoGM, AutoGMQuest, AutoGMScene
from models.ttrpgobject.city import City
from models.ttrpgobject.district import District
from models.ttrpgobject.location import Location
from models.ttrpgobject.region import Region


@pytest.fixture
def mock_party():
    # Mock a party with minimal attributes required for tests
    party = MagicMock()
    party.characters = []
    party.current_date = "2023-11-20"
    party.system = MagicMock()
    party.system._titles = {
        "region": "Region",
        "city": "City",
        "district": "District",
        "location": "Location",
    }
    party.name = "Test Party"
    party.world = MagicMock()
    party.world.name = "Test World"
    party.world.genre = "Fantasy"
    party.autogm_summary = []
    return party


@pytest.fixture
def mock_autogm():
    return AutoGM(world=MagicMock())


@pytest.fixture
def mock_jsonagent():
    return JSONAgent(
        name="TableTop RPG Game Master for TesterLand in a Fantasy setting",
        instructions="You are highly skilled and creative AI trained to act as a Game Master for a Fantasy TableTop RPG. Generate a new, unique story for players to explore in the world of TesterLand. Ensure that you create world elements to fill out the world of TesterLand, including regions, cities, districts, and locations. You will also create NPCs, combatants, loot, and places for players to interact with. Finally, you will create quests for players to complete and generate scenes for players to explore.",
        description="You are a helpful AI assistant trained to act as the Table Top Game Master for 1 or more players. You will create consistent, mysterious, and unique homebrewed Fantasy stories that will challenge, surprise, and delight players. You will generate a variety of world elements, including regions, cities, districts, and locations, as well as NPCs, combatants, loot, and places for players to interact with. You will also create quests for players to complete and generate scenes for players to explore.",
    )


### AutoGMQuest Tests
def test_autogmquest_creation():
    quest = AutoGMQuest(
        name="Save the Village",
        type="main quest",
        description="Rescue the villagers from the bandits.",
        status="active",
    )
    quest.save()

    # Verify quest properties
    assert quest.name == "Save the Village"
    assert quest.type == "main quest"
    assert quest.status == "active"


def test_autogmquest_update():
    quest = AutoGMQuest(
        name="Find the Artifact",
        type="side quest",
        description="Search for the ancient artifact in the ruins.",
        status="rumored",
    )
    quest.save()
    quest.status = "completed"
    quest.save()

    # Verify quest updates
    assert quest.status == "completed"


### AutoGMScene Tests


def test_autogmscene_creation():
    scene = AutoGMScene(
        type="combat",
        description="A fierce battle erupts in the forest.",
        roll_required=True,
        roll_type="savingthrow",
        roll_attribute="DEX",
    )
    scene.save()

    # Verify scene properties
    assert scene.type == "combat"
    assert scene.roll_required is True
    assert scene.roll_type == "savingthrow"
    assert scene.roll_attribute == "DEX"


@pytest.mark.skip(reason="Working, AI API call")
def test_autogmscene_generate_audio(mocker):
    # Mock AudioAgent and AudioAgent.generate
    mocker.patch(
        "autonomous.ai.audioagent.AudioAgent.generate", return_value=b"mock_audio_data"
    )

    scene = AutoGMScene(description="Test scene for audio generation.")
    scene.generate_audio()

    # Verify audio is generated and saved
    assert scene.audio.read() == b"mock_audio_data"


@pytest.mark.skip(reason="Working, AI API call")
def test_autogmscene_generate_image(mocker, mock_party):
    mocker.patch(
        "autonomous.ai.imageagent.ImageAgent.generate", return_value=MagicMock()
    )

    scene = AutoGMScene(party=mock_party, description="A beautiful meadow.")
    scene.generate_image({"description": "A serene scene.", "imgtype": "scene"})

    # Verify image is generated
    assert scene.image is not None


def test_autogmscene_delete(mocker):
    # Mock image deletion
    mock_image = MagicMock()
    scene = AutoGMScene(image=mock_image)
    scene.delete()

    # Verify image deletion
    mock_image.delete.assert_called_once()


### AutoGM Tests


def test_autogm_start(mock_autogm, mock_party, mocker):
    # Mock response from gm.generate
    mocker.patch(
        "autonomous.ai.jsonagent.JSONAgent.generate",
        return_value={"type": "social", "description": "Test scene."},
    )
    mocker.patch("models.autogm.AutoGM.update_refs", return_value=None)
    mocker.patch("models.autogm.AutoGM.parse_scene", return_value=MagicMock())
    mocker.patch("models.autogm.AutoGM.save", return_value="pk")
    mocker.patch("models.autogm.AutoGMScene.save", return_value="pk")
    scene = mock_autogm.start(mock_party)

    # Verify scene is created and saved
    assert scene is not None


def test_autogm_run(mock_autogm, mock_party, mocker):
    # Mock previous summary and gm.generate response
    mock_party.autogm_summary = [MagicMock(summary="Previous events.")]
    mocker.patch(
        "autonomous.ai.jsonagent.JSONAgent.generate",
        return_value={"type": "combat", "description": "Battle scene."},
    )
    mocker.patch("models.autogm.AutoGM.update_refs", return_value=None)
    mocker.patch("models.autogm.AutoGM.parse_scene", return_value=MagicMock())
    mocker.patch("models.autogm.AutoGM.save", return_value="pk")
    mocker.patch("models.autogm.AutoGMScene.save", return_value="pk")
    scene = mock_autogm.run(mock_party, "Attack the bandits!")

    # Verify scene is created and saved
    assert scene is not None


def test_autogm_regenerate(mock_autogm, mock_party, mocker):
    # Mock gm.generate response
    mocker.patch(
        "autonomous.ai.jsonagent.JSONAgent.generate",
        return_value={"type": "exploration", "description": "Exploration scene."},
    )
    mocker.patch("models.autogm.AutoGM.update_refs", return_value=None)
    mocker.patch("models.autogm.AutoGM.parse_scene", return_value=MagicMock())
    mocker.patch("models.autogm.AutoGM.save", return_value="pk")
    mocker.patch("models.autogm.AutoGMScene.save", return_value="pk")
    mock_party.autogm_summary = [MagicMock()]
    scene = mock_autogm.regenerate(mock_party, "Explore the cave.")

    # Verify regenerated scene is created and saved
    assert scene is not None


def test_autogm_end(mock_autogm, mock_party, mocker):
    # Mock gm.generate response
    mocker.patch(
        "autonomous.ai.jsonagent.JSONAgent.generate",
        return_value={"type": "social", "description": "End scene."},
    )
    mocker.patch("models.autogm.AutoGM.update_refs", return_value=None)
    mocker.patch("models.autogm.AutoGM.parse_scene", return_value=MagicMock())
    mocker.patch("models.autogm.AutoGM.save", return_value="pk")
    mocker.patch("models.autogm.AutoGMScene.save", return_value="pk")
    scene = mock_autogm.end(mock_party, "The session concludes.")

    # Verify ending scene is created and saved
    assert scene is not None


@pytest.mark.skip(reason="Working, AI API call")
def test_autogm_scene_generate(mock_jsonagent, mocker):
    mocker.patch(
        "autonomous.ai.jsonagent.JSONAgent.save",
        return_value="pk",
    )
    mocker.patch(
        "autonomous.ai.models.openai.OpenAIModel.save",
        return_value="pk",
    )
    prompt = """You are an expert AI Game Master for a new Fantasy TableTop RPG campaign within the established world of TesterLand. Your job is to start the first session by describing the world, campaign setting, and a plot hook for the players in a vivid and captivating way. The first session should also explain what brought these characters together and what their initial goal is. The party consists of the following characters:

    PARTY MEMBER: Dan [123456ABC]
    Dan is a typical nice guy, but bad things seem to always happen to him. He's a bit of a klutz and has a tendency to get into trouble. He's always willing to help out, but sometimes his good intentions backfire.

    PARTY MEMBER: Jill [987654ZYX]
    Jill is unsure of herself, but incredibly smart. She's always the first to solve a puzzle or figure out a riddle. She's a bit of a bookworm and loves to read, but she's also a bit of a loner and doesn't have many friends.

    SCENARIO: The party has been summoned to the town of Testville by the mayor, who has a problem that needs solving. The town has been plagued by a series of mysterious disappearances, and the mayor believes that the party is the only one who can solve the mystery. The party must investigate the disappearances, find the missing people, and uncover the truth behind the mystery. The fate of the town and its people rests in their hands.

    IN-GAME DATE: 17 September, 1231
"""
    results = mock_jsonagent.generate(prompt, AutoGM._funcobj)
    assert results is not None
    assert results["type"]
    log(results, _print=True)


def test_autogm_parse_scene(mock_autogm, mock_party, mocker):
    # Mock gm.generate response
    mocker.patch(
        "autonomous.ai.jsonagent.JSONAgent.generate",
        return_value={"type": "social", "description": "Test scene."},
    )
    mocker.patch("models.autogm.AutoGM.update_refs", return_value=None)
    mocker.patch("models.autogm.AutoGM.save", return_value="pk")
    mocker.patch("models.autogm.AutoGMScene.save", return_value="pk")
    mocker.patch("models.autogm.AutoGMScene.generate_image", return_value=None)
    mocker.patch("models.autogm.AutoGMScene.generate_audio", return_value=None)
    mocker.patch("models.autogm.AutoGMScene.generate_npcs", return_value=None)
    mocker.patch("models.autogm.AutoGMScene.generate_combatants", return_value=None)
    mocker.patch("models.autogm.AutoGMScene.generate_loot", return_value=None)
    mocker.patch("models.autogm.AutoGMScene.generate_places", return_value=None)

    scene_data = {
        "type": "social",
        "description": "The GM's evocative and detailed description in MARKDOWN of a scene that drives the current scenario forward and includes any relevant information the GM thinks the players need to know",
        "image": {
            "description": "A detailed description of the scene that can be used to generate an image.",
            "imgtype": "scene",
        },
        "player": "Test Player",
        "npcs": [
            {
                "species": "testspecies",
                "name": "testname",
                "description": "testdescription",
                "backstory": "testbackstory",
            }
        ],
        "combatants": [
            {
                "combatant_type": "humanoid",
                "name": "testname",
                "description": "testdescription",
            }
        ],
        "loot": [
            {
                "rarity": "common",
                "name": "testname",
                "description": "testdescription",
                "attributes": ["testattribute"],
            }
        ],
        "places": [
            {
                "location_type": "region",
                "name": "testname",
                "backstory": "testbackstory",
                "description": "testdescription",
            },
            {
                "location_type": "city",
                "name": "testname",
                "backstory": "testbackstory",
                "description": "testdescription",
            },
            {
                "location_type": "district",
                "name": "testname",
                "backstory": "testbackstory",
                "description": "testdescription",
            },
            {
                "location_type": "location",
                "name": "testname",
                "backstory": "testbackstory",
                "description": "testdescription",
            },
        ],
        "requires_roll": {
            "roll_required": False,
            "type": "none",
            "attribute": "none",
            "description": "none",
        },
        "quest_log": [
            {
                "name": "testname",
                "type": "main quest",
                "description": "testdescription",
                "importance": "testimportance",
                "status": "active",
                "next_steps": "testnextsteps",
            }
        ],
    }

    # Verify scene is created and saved
    result = mock_autogm.parse_scene(mock_party, scene_data)

    assert result is not None
    assert result.type == "social"
    assert (
        "The GM's evocative and detailed description in MARKDOWN" in result.description
    )
    assert result.roll_required is not None
    assert result.quest_log[0].name == "testname"
    assert result.quest_log[0].type == "main quest"
    assert result.quest_log[0].status == "active"
    assert result.quest_log[0].next_steps == "testnextsteps"
    assert result.quest_log[0].importance == "testimportance"
    assert result.quest_log[0].description == "testdescription"


def test_autogm_scene_generate_npcs(mock_autogm, mock_party, mocker):
    mocker.patch("models.autogm.AutoGMScene.save", return_value="pk")
    mocker.patch("autonomous.model.automodel.AutoModel.save", return_value="pk")
    mocker.patch("autonomous.model.automodel.AutoModel.find", return_value=None)
    mocker.patch("requests.post", return_value="success")

    ags = AutoGMScene(party=mock_party)
    obj = {
        "species": "Test",
        "name": "Test",
        "description": "Test",
        "backstory": "Test",
    }
    ags.generate_npcs([obj])
    assert ags.npcs[0].race == "Test"


def test_autogm_scene_generate_combatants(mock_autogm, mock_party, mocker):
    mocker.patch("models.autogm.AutoGMScene.save", return_value="pk")
    mocker.patch("autonomous.model.automodel.AutoModel.save", return_value="pk")
    mocker.patch("autonomous.model.automodel.AutoModel.find", return_value=None)
    mocker.patch("requests.post", return_value="success")

    ags = AutoGMScene(party=mock_party)
    obj = {
        "combatant_type": "Test",
        "name": "Test",
        "description": "Test",
    }
    ags.generate_combatants([obj])
    assert ags.combatants[0].type == "Test"


def test_autogm_scene_generate_loot(mock_autogm, mock_party, mocker):
    mocker.patch("models.autogm.AutoGMScene.save", return_value="pk")
    mocker.patch("autonomous.model.automodel.AutoModel.save", return_value="pk")
    mocker.patch("autonomous.model.automodel.AutoModel.find", return_value=None)
    mocker.patch("requests.post", return_value="success")

    ags = AutoGMScene(party=mock_party)
    obj = {
        "rarity": "Test",
        "name": "Test",
        "description": "Test",
        "attributes": ["Test"],
    }
    ags.generate_loot([obj])
    assert ags.loot[0].rarity == "Test"


def test_autogm_scene_generate_places(mock_autogm, mock_party, mocker):
    mocker.patch("models.autogm.AutoGMScene.save", return_value="pk")
    mocker.patch("autonomous.model.automodel.AutoModel.save", return_value="pk")
    mocker.patch("autonomous.model.automodel.AutoModel.find", return_value=None)
    mocker.patch("requests.post", return_value="success")

    ags = AutoGMScene(party=mock_party)
    objs = [
        {
            "location_type": "region",
            "name": "TestRegion",
            "description": "TestRegionDescription",
            "backstory": "TestRegionBackstory",
        },
        {
            "location_type": "city",
            "name": "TestCity",
            "description": "TestCityDescription",
            "backstory": "TestCityBackstory",
        },
        {
            "location_type": "district",
            "name": "TestDistrict",
            "description": "TestDistrictDescription",
            "backstory": "TestDistrictBackstory",
        },
        {
            "location_type": "location",
            "name": "TestLocation",
            "description": "TestLocationDescription",
            "backstory": "TestLocationBackstory",
        },
    ]
    places = ags.generate_places(objs)
    assert len(places) == 4
    assert isinstance(ags.places[0], Region)
    assert isinstance(ags.places[1], City)
    assert isinstance(ags.places[2], District)
    assert isinstance(ags.places[3], Location)
