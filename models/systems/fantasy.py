from models.systems.basesystem import BaseSystem


class FantasySystem(BaseSystem):
    # meta = {"collection": "FantasySystem"}

    _genre = "Fantasy"

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
        "poi": "POI",
        "item": "Item",
        "encounter": "Encounter",
        "character": "Character",
    }
