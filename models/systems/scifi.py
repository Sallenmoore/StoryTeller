from models.systems.basesystem import BaseSystem


class SciFiSystem(BaseSystem):
    # meta = {"collection": "SciFiSystem"}
    _genre = "Sci-Fi"

    _currency = {
        "credits": "cc",
    }

    _titles = {
        "city": "Planet",
        "creature": "Alien",
        "faction": "Faction",
        "region": "Star-System",
        "world": "Galactic-Sector",
        "location": "Location",
        "poi": "POI",
        "item": "Tech",
        "encounter": "Encounter",
        "character": "Character",
    }
