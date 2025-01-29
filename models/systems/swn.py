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
