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
