import random

from models.systems.scifi import SciFiSystem


class StarsWithoutNumber(SciFiSystem):
    # meta = {"collection": "SciFiSystem"}

    _genre = "Stars Without Number"

    _skills = {
        "Administer": random.randint(-1, 2),
        "Connect": random.randint(-1, 2),
        "Exert": random.randint(-1, 2),
        "Fix": random.randint(-1, 2),
        "Heal": random.randint(-1, 2),
        "Know": random.randint(-1, 2),
        "Lead": random.randint(-1, 2),
        "Notice": random.randint(-1, 2),
        "Perform": random.randint(-1, 2),
        "Pilot": random.randint(-1, 2),
        "Program": random.randint(-1, 2),
        "Punch": random.randint(-1, 2),
        "Shoot": random.randint(-1, 2),
        "Sneak": random.randint(-1, 2),
        "Stab": random.randint(-1, 2),
        "Survive": random.randint(-1, 2),
        "Talk": random.randint(-1, 2),
        "Trade": random.randint(-1, 2),
        "Work": random.randint(-1, 2),
    }

    _classes = {
        "Warrior": ["Soldier", "Mercenary", "Gladiator", "Bodyguard", "Martial Artist"],
        "Expert": ["Engineer", "Scout", "Spy", "Trader", "Technician"],
        "Psychic": ["Telepath", "Precog", "Biopsionicist", "Metapsion", "Telekinetic"],
        "Adventurer": [
            "Jack-of-All-Trades",
            "Explorer",
            "Bounty Hunter",
            "Smuggler",
            "Duelist",
        ],
    }

    _backgrounds = {
        "Academic": "A character with a scholarly or research-focused background, skilled in knowledge and analysis.",
        "Artist": "A creative individual, such as a painter, musician, or writer, with talents in expression and performance.",
        "Criminal": "Someone with a history in illegal activities, adept at deception, sneaking, and underworld connections.",
        "Entertainer": "A performer skilled at captivating audiences, whether through acting, music, or other talents.",
        "Merchant": "An experienced trader or businessperson, knowledgeable about commerce, negotiation, and finance.",
        "Noble": "A character from a wealthy or influential family, skilled in leadership and navigating social hierarchies.",
        "Peasant": "A background rooted in farming or rural labor, with practical survival and work skills.",
        "Pilot": "An expert in operating and navigating vehicles, particularly starships and other advanced machinery.",
        "Professional": "A trained individual in a specific field, such as law, medicine, or engineering.",
        "Soldier": "A veteran of military service, skilled in combat and tactics.",
        "Spacer": "Someone experienced in life aboard starships, adept at maintenance, zero-gravity operations, and space travel.",
        "Technician": "A hands-on specialist in repairing and maintaining machinery or systems.",
        "Thug": "A brute or enforcer, accustomed to physical confrontations and intimidation.",
        "Traveler": "An individual with experience exploring new places and adapting to various environments.",
        "Worker": "A laborer familiar with physical or industrial tasks, with expertise in practical trades.",
    }

    templates = {
        "city": [
            [],
            [],
        ],
        "creature": [
            [],
            [],
        ],
        "faction": [
            [],
            [],
        ],
        "region": [
            [],
            [],
        ],
        "world": [
            [],
            [],
        ],
        "location": [
            [],
            [],
        ],
        "shop": [
            [],
            [],
        ],
        "vehicle": [
            [],
            [],
        ],
        "district": [
            [],
            [],
        ],
        "item": [
            [],
            [],
        ],
        "encounter": [
            [],
            [],
        ],
        "character": [
            [
                "The local underclass or poorest natives",
                "Common laborer or cube worker"
                "Aspiring bourgeoise or upper class"
                "The elite of this society"
                "Minority or foreigner"
                "Offworlders or exotic",
            ],
            [
                "Criminal, thug, thief, swindler",
                "Menial, cleaner, retail worker, servant",
                "Unskilled heavy labor, porter, construction",
                "Skilled trade, electrician, mechanic, pilot",
                "Idea worker, programmer, writer",
                "Merchant, business owner, trader, banker",
                "Official, bureaucrat, courtier, clerk",
                "Military, soldier, enforcer, law officer",
            ],
            [
                "They have significant debt or money woes",
                "A loved one is in trouble",
                "Romantic failure with a desired person",
                "Drug or behavioral addiction",
                "Their superior dislikes or resents them",
                "They have a persistent sickness",
                "They hate their job or life situation",
                "Someone dangerous is targeting them",
                "They’re pursuing a disastrous purpose",
                "They have no problems worth mentioning",
            ],
            [
                "Unusually young or old for their role"
                "Young adult"
                "Mature prime"
                "Middle-aged or elderly"
            ],
            [
                "They want a particular romantic partner",
                "They want money for them or a loved one",
                "They want a promotion in their job",
                "They want answers about a past trauma",
                "They want revenge on an enemy",
                "They want to help a beleaguered friend",
                "They want an entirely different job",
                "They want protection from an enemy",
                "They want to leave their current life",
                "They want fame and glory",
                "They want power over those around them",
                "They have everything they want from life",
            ],
        ],
    }
