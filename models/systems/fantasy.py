from models.systems.basesystem import BaseSystem


class FantasySystem(BaseSystem):
    meta = {
        "allow_inheritance": True,
        "strict": False,
    }

    _genre = "Fantasy"

    _currency = {
        "copper": "CP",
        "silver": "SP",
        "gold": "GP",
        "platinum": "PP",
    }

    _titles = {
        "city": "City",
        "creature": "Creature",
        "faction": "Faction",
        "region": "Region",
        "world": "World",
        "location": "Location",
        "shop": "Shop",
        "vehicle": "Vehicle",
        "district": "District",
        "item": "Item",
        "encounter": "Encounter",
        "character": "Character",
    }
