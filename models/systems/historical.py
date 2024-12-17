from models.systems.basesystem import BaseSystem


class HistoricalSystem(BaseSystem):
    # meta = {"collection": "HistoricalSystem"}
    _genre = "Historical"

    _currency = {
        "dollars": "$",
        "cents": "p",
    }

    _titles = {
        "city": "City",
        "creature": "Rival",
        "faction": "Faction",
        "region": "Region",
        "world": "Country",
        "location": "Location",
        "vehicle": "Vehicle",
        "district": "District",
        "item": "Item",
        "encounter": "Encounter",
        "character": "Character",
    }
