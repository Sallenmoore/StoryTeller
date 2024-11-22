from models.systems.basesystem import BaseSystem


class PostApocalypticSystem(BaseSystem):
    # meta = {"collection": "PostApocalypticSystem"}
    _genre = "Post-Apocolyptic"

    _currency = {
        "trade": "val:",
    }

    _date = "15 April 2031"

    _titles = {
        "city": "Ruin",
        "creature": "Creature",
        "faction": "Faction",
        "region": "Territory",
        "world": "Region",
        "location": "Location",
        "poi": "POI",
        "item": "Item",
        "encounter": "Encounter",
        "character": "Character",
    }
