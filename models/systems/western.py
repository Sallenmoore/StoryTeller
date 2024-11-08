from models.systems.basesystem import BaseSystem


class WesternSystem(BaseSystem):
    # meta = {"collection": "WesternSystem"}
    _genre = "Western"

    _currency = {
        "dollars": "$",
        "cents": "p",
    }

    _titles = {
        "city": "Town",
        "creature": "Outlaw",
        "faction": "Gang",
        "region": "Territory",
        "world": "Region",
        "location": "Location",
        "poi": "POI",
        "item": "Item",
        "encounter": "Encounter",
        "character": "Character",
    }
