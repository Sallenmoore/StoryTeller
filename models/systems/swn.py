from models.systems.scifi import SciFiSystem


class StarsWithoutNumber(SciFiSystem):
    # meta = {"collection": "SciFiSystem"}

    _skills = {
        "Administer": -1,
        "Connect": -1,
        "Exert": -1,
        "Fix": -1,
        "Heal": -1,
        "Know": -1,
        "Lead": -1,
        "Notice": -1,
        "Perform": -1,
        "Pilot": -1,
        "Program": -1,
        "Punch": -1,
        "Shoot": -1,
        "Sneak": -1,
        "Stab": -1,
        "Survive": -1,
        "Talk": -1,
        "Trade": -1,
        "Work": -1,
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
