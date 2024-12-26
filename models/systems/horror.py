from models.systems.basesystem import BaseSystem


class HorrorSystem(BaseSystem):
    # meta = {"collection": "HorrorSystem"}
    _genre = "Horror"

    _currency = {
        "dollars": "$",
        "cents": "p",
    }

    _titles = {
        "city": "Building",
        "creature": "Creature",
        "faction": "Faction",
        "region": "Town",
        "world": "Area",
        "location": "Room",
        "district": "Floor",
        "item": "Item",
        "encounter": "Encounter",
        "character": "Character",
    }

    _map_prompts = BaseSystem._map_prompts | {
        "city": lambda obj: f"""Generate a top-down navigable indoor map of a {obj.title} suitable for a {obj.genre} tabletop RPG. The map should be detailed and include the following elements:
            - MAP TYPE: indoor layout map
            - SCALE: 1 inch == 5 feet
            {"- CONTEXT: " + obj.backstory_summary if obj.backstory_summary else ""}
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            {"- ROOMS: " + ",".join([poi.name for poi in obj.districts if poi.name]) if [poi.name for poi in obj.districts if poi.name] else ""}
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
