from models.systems.basesystem import BaseSystem


class HorrorSystem(BaseSystem):
    # meta = {"collection": "HorrorSystem"}
    _genre = "Horror"

    _currency = {
        "dollars": "$",
        "cents": "p",
    }

    _titles = {
        "city": "Neighborhood",
        "creature": "Creature",
        "faction": "Faction",
        "region": "Town",
        "world": "Area",
        "location": "Room",
        "district": "Building",
        "item": "Item",
        "encounter": "Encounter",
        "character": "Character",
    }

    _music_lists = {
        "social": ["themesong.mp3"],
        "combat": [
            "battle2.mp3",
            "battle4.mp3",
            "battle3.mp3",
            "battle5.mp3",
            "skirmish4.mp3",
            "skirmish3.mp3",
            "skirmish2.mp3",
            "skirmish1.mp3",
        ],
        "exploration": ["relaxed1.mp3", "creepy1.mp3", "creepy2.mp3", "creepy3.mp3"],
        "stealth": [
            "suspense1.mp3",
            "suspense2.mp3",
            "suspense3.mp3",
            "suspense4.mp3",
            "suspense5.mp3",
            "suspense6.mp3",
            "suspense7.mp3",
        ],
    }

    _map_prompts = BaseSystem._map_prompts | {
        "city": lambda obj: f"""Generate a top-down navigable indoor map of a {obj.title} suitable for a {obj.genre} tabletop RPG. The map should be detailed and include the following elements:
            - MAP TYPE: indoor layout map
            - SCALE: 1 inch == 5 feet
            {"- CONTEXT: " + obj.backstory_summary if obj.backstory_summary else ""}
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            {"- ROOMS: " + ",".join([poi.name for poi in obj.pois if poi.name]) if [poi.name for poi in obj.pois if poi.name] else ""}
            """,
        "region": lambda obj: f"""Generate a top-down navigable map of a {obj.title} suitable for a tabletop RPG. The map should be detailed and include the following elements:
            - MAP TYPE: top-down with key locations marked
            - SCALE: 1 inch == 1 mile
            {"- CONTEXT: " + obj.backstory_summary if obj.backstory_summary else ""}
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            """,
        "world": lambda obj: f"""Generate a top-down navigable map of a {obj.title} suitable for a tabletop RPG. The map should be detailed and include the following elements:
            - MAP TYPE: An top-down atlas style map of the {obj.title}
            - SCALE: 1 inch == 5 miles
            {"- CONTEXT: " + obj.backstory_summary if obj.backstory_summary else ""}
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            """,
        "location": lambda obj: f"""Generate a top-down navigable map of a {obj.title} suitable for a tabletop RPG. The map should be detailed and include the following elements:
            - MAP TYPE: top-down navigable {obj.title} map
            - SCALE: 1 inch == 1 foot
            {"- CONTEXT: " + obj.backstory_summary if obj.backstory_summary else ""}
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            """,
        "poi": lambda obj: f"""Generate a top-down navigable map of a {obj.title} suitable for a tabletop RPG. The map should be detailed and include the following elements:
            - MAP TYPE: top-down navigable {obj.title} map
            - SCALE: 1 inch == 1 foot
            {"- CONTEXT: " + obj.backstory_summary if obj.backstory_summary else ""}
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            """,
    }
