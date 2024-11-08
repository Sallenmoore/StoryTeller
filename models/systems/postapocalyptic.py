from models.systems.basesystem import BaseSystem


class PostApocalypticSystem(BaseSystem):
    # meta = {"collection": "PostApocalypticSystem"}
    _genre = "Post-Apocolyptic"

    _currency = {
        "trade": "val:",
    }

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
