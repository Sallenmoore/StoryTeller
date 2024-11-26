from models.systems.basesystem import BaseSystem


class WesternSystem(BaseSystem):
    # meta = {"collection": "WesternSystem"}
    _genre = "Western"

    _currency = {
        "dollars": "$",
        "cents": "p",
    }

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

    _titles = {
        "city": "Town",
        "creature": "Outlaw",
        "faction": "Gang",
        "region": "Territory",
        "world": "Region",
        "location": "Location",
        "district": "District",
        "item": "Item",
        "encounter": "Encounter",
        "character": "Character",
    }
