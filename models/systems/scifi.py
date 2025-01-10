from models.systems.basesystem import BaseSystem


class SciFiSystem(BaseSystem):
    # meta = {"collection": "SciFiSystem"}
    _genre = "Sci-Fi"

    _currency = {
        "credits": "cc",
    }

    _music_lists = BaseSystem._music_lists | {
        "social": ["scifithemesong.mp3"],
        "encounter": ["scifipursuit.mp3"],
        "combat": [
            "scifibattle.mp3",
        ],
        "exploration": ["scificreepy.mp3", "scifisuspense.mp3"],
        "stealth": [
            "scifisuspense.mp3",
        ],
    }

    _titles = {
        "city": "Planet",
        "creature": "Alien",
        "faction": "Faction",
        "region": "Star-System",
        "world": "Galactic-Sector",
        "location": "Location",
        "shop": "Shop",
        "vehicle": "Vehicle",
        "district": "Outpost",
        "item": "Tech",
        "encounter": "Encounter",
        "character": "Character",
    }
