import random
import re

import markdown
from autonomous.ai.jsonagent import JSONAgent
from autonomous.ai.textagent import TextAgent
from autonomous.model.autoattr import (
    ReferenceAttr,
)
from autonomous.model.automodel import AutoModel
from bs4 import BeautifulSoup

from autonomous import log


class BaseSystem(AutoModel):
    meta = {
        "abstract": True,
        "allow_inheritance": True,
        "strict": False,
    }
    text_client = ReferenceAttr(choices=[TextAgent])
    json_client = ReferenceAttr(choices=[JSONAgent])
    world = ReferenceAttr(choices=["World"])

    _backgrounds = {
        "Acolyte": "You have spent your life in the service of a temple to a specific god or pantheon of gods. You act as an intermediary between the realm of the holy and the mortal world, performing sacred rites and offering sacrifices.",
        "Charlatan": "You have always had a way with people. You know what makes them tick, and you can tease out their hearts’ desires after a few minutes of conversation. You use this skill to your advantage in your line of work.",
        "Criminal": "You have a history of breaking the law. You have spent a lot of time among other criminals and still have contacts within the criminal underworld.",
        "Entertainer": "You thrive in front of an audience. You know how to entrance them, entertain them, and inspire them. Your poise, confidence, and theatrical flair make you a master of performance.",
        "Folk Hero": "You come from a humble social rank, but you are destined for so much more. The people of your home village regard you as their champion, and your destiny calls you to stand against the tyrants and monsters threatening the common folk everywhere.",
        "Guild Artisan": "You are a member of an artisan’s guild, skilled in a particular field and closely associated with other artisans. You are well established in the mercantile world, owning a shop and working with trade networks.",
        "Hermit": "You lived in seclusion—either in a sheltered community such as a monastery or entirely alone—for a formative part of your life. In your time apart from the clamor of society, you found quiet, solitude, and perhaps a bit of insanity.",
        "Noble": "You understand wealth, power, and privilege. You carry a noble title, and your family owns land, collects taxes, and wields significant political influence. You might be a pampered aristocrat or a disinherited scoundrel.",
        "Outlander": "You grew up in the wilds, far from civilization and the comforts of town and technology. You’ve witnessed the migration of herds larger than forests, survived weather more extreme than any city-dweller could comprehend, and enjoyed the solitude of being the only thinking creature for miles in any direction.",
        "Sage": "You spent years learning the lore of the multiverse. You scoured manuscripts, studied scrolls, and listened to the greatest experts on the subjects that interest you.",
        "Sailor": "You sailed on a seagoing vessel for years. In that time, you faced down mighty storms, monsters of the deep, and those who wanted to sink your craft to the bottomless depths.",
        "Soldier": "War has been your life for as long as you care to remember. You trained as a youth, studied the use of weapons and armor, learned survival strategies, and perhaps took part in a war.",
        "Urchin": "You grew up on the streets alone, orphaned, and poor. You had no one to watch over you or to provide for you, so you learned to provide for yourself. You fought fiercely over food and kept a constant watch out for other desperate souls who might take it from you.",
        "Merchant": "An experienced trader or businessperson, knowledgeable about commerce, negotiation, and finance.",
        "Politician": "Holds power and influence within a political system, skilled in manipulation and strategy.",
        "Peasant": "A background rooted in farming or rural labor, with practical survival and work skills.",
    }

    _classes = {
        "Artificer": [
            "TBD",
        ],
        "Barbarian": [
            "Path of the Berserker",
            "Path of the Totem Warrior",
            "Path of the Ancestral Guardian",
            "Path of the Battlerager",
            "Path of the Storm Herald",
            "Path of the Zealot",
            "Path of Wild Magic",
        ],
        "Bard": [
            "College of Lore",
            "College of Valor",
            "College of Glamour",
            "College of Swords",
            "College of Whispers",
            "College of Creation",
            "College of Eloquence",
        ],
        "Cleric": [
            "Arcana Domain",
            "Death Domain",
            "Forge Domain",
            "Grave Domain",
            "Knowledge Domain",
            "Life Domain",
            "Light Domain",
            "Nature Domain",
            "Order Domain",
            "Tempest Domain",
            "Trickery Domain",
            "War Domain",
        ],
        "Druid": [
            "Circle of Dreams",
            "Circle of the Land",
            "Circle of the Moon",
            "Circle of the Shepherd",
            "Circle of Spores",
            "Circle of Stars",
            "Circle of Wildfire",
        ],
        "Fighter": [
            "Arcane Archer",
            "Banneret",
            "Battle Master",
            "Cavalier",
            "Champion",
            "Echo Knight",
            "Eldritch Knight",
            "Psi Warrior",
            "Rune Knight",
            "Samurai",
        ],
        "Monk": [
            "Way of the Open Hand",
            "Way of Shadow",
            "Way of the Four Elements",
            "Way of the Drunken Master",
            "Way of the Kensei",
            "Way of the Sun Soul",
            "Way of Mercy",
            "Way of the Astral Self",
        ],
        "Paladin": [
            "Oath of Devotion",
            "Oath of the Ancients",
            "Oath of Vengeance",
            "Oath of the Crown",
            "Oath of Conquest",
            "Oath of Redemption",
            "Oath of Glory",
            "Oath of the Watchers",
        ],
        "Ranger": [
            "Beast Master Conclave",
            "Hunter Conclave",
            "Gloom Stalker Conclave",
            "Horizon Walker Conclave",
            "Monster Slayer Conclave",
            "Fey Wanderer",
            "Swarmkeeper",
        ],
        "Rogue": [
            "Arcane Trickster",
            "Assassin",
            "Inquisitive",
            "Mastermind",
            "Phantom",
            "Scout",
            "Soulknife",
            "Swashbuckler",
            "Thief",
        ],
        "Sorcerer": [
            "Divine Soul",
            "Draconic Bloodline",
            "Shadow Magic",
            "Storm Sorcery",
            "Wild Magic",
            "Aberrant Mind",
            "Clockwork Soul",
        ],
        "Warlock": [
            "The Archfey",
            "The Fiend",
            "The Great Old One",
            "The Celestial",
            "The Hexblade",
            "The Fathomless",
            "The Genie",
        ],
        "Wizard": [
            "School of Abjuration",
            "School of Conjuration",
            "School of Divination",
            "School of Enchantment",
            "School of Evocation",
            "School of Illusion",
            "School of Necromancy",
            "School of Transmutation",
            "Bladesinging",
            "Order of Scribes",
        ],
        "Merchant": [
            "Shopkeeper",
            "Innkeeper",
            "Travelling",
            "Black Market",
        ],
        "General": [
            "Peasant",
            "Aristocrat",
            "Adventurer",
        ],
    }

    _genre = "Mixed"
    MAX_TOKEN_LENGTH = 7500
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
        "character": "Character",
    }

    _stats = {
        "strength": "STR",
        "dexterity": "DEX",
        "constitution": "CON",
        "intelligence": "INT",
        "wisdom": "WIS",
        "charisma": "CHA",
        "hit_points": "HP",
        "armor_class": "AC",
    }

    _currency = {
        "money": "gold pieces",
    }

    _map_prompts = {
        "city": lambda obj: f"""Generate a top-down atlas style map of a {obj.title} suitable for a {obj.genre} tabletop RPG. The map should be a general overview of the {obj.title} that fills the entire image.<br>
- MAP TYPE: A top-down atlas of the {obj.title} <br>
- SCALE: 1 inch == 500 feet <br>
{"- DESCRIPTION: " + obj.desc if obj.desc else ""}
""",
        "region": lambda obj: f"""Generate a top-down atlas style map of a {obj.title} suitable for a {obj.genre} tabletop RPG. The map should be a general overview of the {obj.title}  that fills the entire image.<br>
- MAP TYPE: A top-down atlas of the {obj.title} <br>
- SCALE: 1 inch == 50 miles <br>
{"- DESCRIPTION: " + obj.desc if obj.desc else ""}
""",
        "world": lambda obj: f"""Generate a top-down atlas style map of a {obj.title} suitable for a {obj.genre} tabletop RPG. The map should be a general overview of the {obj.title} that fills the entire image.<br>
- MAP TYPE: A top-down atlas of the {obj.title} <br>
- SCALE: 1 inch == 500 miles <br>
{"- DESCRIPTION: " + obj.desc if obj.desc else ""}
""",
        "location": lambda obj: f"""Generate a top-down navigable Table Top RPG battle map suitable for a {obj.genre} encounter in a {obj.location_type}. The map should fill the entire image and be detailed enough for players to clearly understand how to navigate the environment.<br>
- MAP TYPE: directly overhead, top-down, no grid <br>
- SCALE: 1 inch == 5 feet <br>
{"- DESCRIPTION: " + obj.desc if obj.desc else ""}
""",
        "shop": lambda obj: f"""Generate a top-down navigable Table Top RPG battlemap of an establishment suitable for a {obj.genre} encounter at a {obj.title}. The map should fill the entire image and be detailed enough for players to clearly understand how to navigate the environment.<br>
- MAP TYPE: directly overhead, top-down, no grid <br>
- SCALE: 1 inch == 5 feet <br>
{"- DESCRIPTION: " + obj.desc if obj.desc else ""}
""",
        "district": lambda obj: f"""Generate a top-down navigable Table Top RPG battle map of a {obj.title} suitable for a {obj.genre} encounter in a {obj.title}. The map should fill the entire image and be detailed enough for players to clearly understand how to navigate the environment.<br>
- MAP TYPE: directly overhead, top-down, no grid <br>
- SCALE: 1 inch == 5 feet <br>
{"- DESCRIPTION: " + obj.desc if obj.desc else ""}
""",
        "vehicle": lambda obj: f"""Generate a top-down navigable {obj.genre} Table Top RPG battle map of the floor plan of a {obj.type}. The map should  fill the entire image and be detailed enough for players to clearly understand how to navigate the environment.<br>
- MAP TYPE: directly overhead, top-down, no grid <br>
- SCALE: 1 inch == 5 feet <br>
{"- DESCRIPTION: " + obj.desc if obj.desc else ""}
""",
    }

    _themes_list = {
        # -------------------------------------------------------------------------
        # Character Themes & Motifs
        # -------------------------------------------------------------------------
        "character": {
            "themes": [
                "The Coward's Guilt (Shame, Resentment, Cowardice)",
                "The Shadowed Heart (Secretly Evil, Cruel/Sadistic, Deceitfulness)",
                "The Open Door (Outgoing/Imaginative, Kind/Helpful, Hopefulness)",
                "The Iron Will (Determination, Proud/Self-Absorbed, Ambition)",
                "The Generous Hand (Charitable, Extremely Generous, Love of a Person)",
                "The Cautious Observer (Practical to a Fault, Paranoid, Unfriendly)",
                "The Reckless Fire (Dangerously Curious, Reckless, Courage)",
                "The Fading Light (Bitterness, Hatred, Nihilism, Pessimism)",
                "The Unbroken Vow (Devotion to a Cause, Filiality, Honesty)",
            ],
            "motifs": [
                "Hidden Scars, Flinching Eyes, Unfinished Work",
                "Velvet Gloves, False Smiles, A Locket Containing Nothing",
                "Bright Cloaks, A Hand-Drawn Map, Untroubled Laughter",
                "Worn Armor, Measured Steps, The Mark of an Oath",
                "Patched Clothes, Always Offering the Last Drink, A Shared Lullaby",
                "Sealed Windows, Detailed Ledgers, Trust Only the Numbers",
                "Singed Hair, A Broken Compass, A Challenge Accepted Instantly",
                "Rust, Hollow Bells, A Graveyard of Personal Failures",
                "Uniform Patches, Calloused Knees, The Same Prayer Repeated Daily",
            ],
        },
        # -------------------------------------------------------------------------
        # City, District, & Location Themes & Motifs
        # -------------------------------------------------------------------------
        "city": {
            "themes": [
                "The Gilded Cage (Aristocratic, Proud, Bureaucratic)",
                "The Freehold of Bone (Anarchic, Aggressive, Tribalist)",
                "The Sanctuary of the Word (Theocratic, Fanatical, Dogmatic)",
                "The Melting Pot (Bohemian, Outgoing, Egalitarian)",
                "The Walled Enclave (Distrustful, Insular, Isolationist)",
                "The Unruly Markets (Rude & Greedy, Mercenary, Lawless)",
            ],
            "motifs": [
                "Wrought-Iron Fences, Perfume and Rot, Monograms on Everything",
                "Barricades, Graffiti Scrawled on Statues, Fires That Burn Unchecked",
                "Stained Glass, Silent Bells, Books Chained to Pedestals",
                "Street Food Stalls, Vibrant Flags, Music Heard from Every Doorway",
                "Tall, Blank Walls, Locked Gates, Eyes Watching from Shadows",
                "Unlicensed Vendors, Loud Haggling, Currency Exchange Bypassed",
            ],
        },
        "district": {
            "themes": [
                "The Gilded Cage (Aristocratic, Proud, Bureaucratic)",
                "The Freehold of Bone (Anarchic, Aggressive, Tribalist)",
                "The Sanctuary of the Word (Theocratic, Fanatical, Dogmatic)",
                "The Melting Pot (Bohemian, Outgoing, Egalitarian)",
                "The Walled Enclave (Distrustful, Insular, Isolationist)",
                "The Unruly Markets (Rude & Greedy, Mercenary, Lawless)",
            ],
            "motifs": [
                "Wrought-Iron Fences, Perfume and Rot, Monograms on Everything",
                "Barricades, Graffiti Scrawled on Statues, Fires That Burn Unchecked",
                "Stained Glass, Silent Bells, Books Chained to Pedestals",
                "Street Food Stalls, Vibrant Flags, Music Heard from Every Doorway",
                "Tall, Blank Walls, Locked Gates, Eyes Watching from Shadows",
                "Unlicensed Vendors, Loud Haggling, Currency Exchange Bypassed",
            ],
        },
        "location": {
            "themes": [
                "The Gilded Cage (Aristocratic, Proud, Bureaucratic)",
                "The Freehold of Bone (Anarchic, Aggressive, Tribalist)",
                "The Sanctuary of the Word (Theocratic, Fanatical, Dogmatic)",
                "The Melting Pot (Bohemian, Outgoing, Egalitarian)",
                "The Walled Enclave (Distrustful, Insular, Isolationist)",
                "The Unruly Markets (Rude & Greedy, Mercenary, Lawless)",
            ],
            "motifs": [
                "Wrought-Iron Fences, Perfume and Rot, Monograms on Everything",
                "Barricades, Graffiti Scrawled on Statues, Fires That Burn Unchecked",
                "Stained Glass, Silent Bells, Books Chained to Pedestals",
                "Street Food Stalls, Vibrant Flags, Music Heard from Every Doorway",
                "Tall, Blank Walls, Locked Gates, Eyes Watching from Shadows",
                "Unlicensed Vendors, Loud Haggling, Currency Exchange Bypassed",
            ],
        },
        # -------------------------------------------------------------------------
        # World Themes & Motifs
        # -------------------------------------------------------------------------
        "world": {
            "themes": [
                "The Age of Dogma (Theocratic, Fanatical, Bureaucratic)",
                "The Age of Fiefdoms (Aristocratic, Tribalist, Proud)",
                "The Age of Dust and Iron (Aggressive, Distrustful, Rude)",
                "The Age of Discovery (Bohemian, Outgoing, Expansionist)",
                "The Age of Whispers (Sinister, Deceptive, Corrupt)",
            ],
            "motifs": [
                "Burnt Scrolls, Universal Curfew, Stone Tablets",
                "Heraldry, Vassalage Oaths, Contempt for Outsiders",
                "Scavenging, Rusty Weapons, Scars as Badges of Honor",
                "Unmapped Coastlines, Exotic Cargo, The Smell of Adventure",
                "Secret Societies, Hidden Traps, The Sound of a Footstep Behind You",
            ],
        },
        # -------------------------------------------------------------------------
        # Creature Themes & Motifs
        # -------------------------------------------------------------------------
        "creature": {
            "themes": [
                "Unthinking Rage (Savage, Vicious, Aggressive)",
                "Apex Predator Intellect (Intelligent, Cunning, Deceptive)",
                "Silent Hunter (Sneaky, Ambusher, Cowardly)",
                "Guardian Instinct (Loyal, Protective, Defensive)",
            ],
            "motifs": [
                "Broken Teeth, Mindless Attack Patterns, A Trail of Shredded Flesh",
                "Intricate Lairs, Traps Baited with Gold, Mimicking Human Speech",
                "Rustling Leaves, Tracks That Vanish, Attacking from the High Ground",
                "A Roar that Warns, A Barrier of Bone, Unwavering Gaze at the Protected Target",
            ],
        },
        # -------------------------------------------------------------------------
        # Faction Themes & Motifs
        # -------------------------------------------------------------------------
        "faction": {
            "themes": [
                "The Gospel of Power (Ideology: Cult, Fanatical, Sinister)",
                "The Golden Chain (Economic: Corrupt, Greedy, Imperialist)",
                "The Earthbound Promise (Political: Deep Rooted, Isolationist, Racist)",
                "The Open Hand (Economic: Charitable, Generous, Egalitarian)",
                "The Iron Hand (Methodology: Suspicious, Violent, Mercenary)",
                "The New Frontier (Political: Colonists, Ambitious, Expansionist)",
            ],
            "motifs": [
                "Single Eye Symbols, Shaved Heads, Whispered Prophecies",
                "Weighty Gold Coins, Debt Ledgers, Hidden Silk Pouches",
                "Ancient Trees, Ancestral Marks, Unbroken Lineage Scrolls",
                "Communal Baskets, Mended Tools, Simple Garb",
                "Blood Money, Sharpened Blades, Scorn for Diplomacy",
                "Fresh Paint, Claim Stakes, Seeds of New Crops",
            ],
        },
        # -------------------------------------------------------------------------
        # Region Themes & Motifs
        # -------------------------------------------------------------------------
        "region": {
            "themes": [
                "The Spires of Stone (Terrain: Mountainous, Underground)",
                "The Drowning Earth (Climate: Swamp, Coastal, Jungle)",
                "The Sun-Blasted Wastes (Climate: Desert, Plains, Frozen)",
                "The Emerald Shroud (Geography: Forest, Coastal)",
                "The Heartlands (Terrain: Plains, Settlements)",
            ],
            "motifs": [
                "Vertigo, Echoes, Deep Shadow, Stark Heights",
                "Mist, Sticky Mud, Strange Bird Calls, Mold on Wood",
                "Cracked Earth, White Snow, Silence, Relentless Horizon",
                "Filtered Light, Unseen Paths, The Smell of Pine and Salt",
                "Waving Wheat, Long, Flat Roads, Sense of Openness",
            ],
        },
        # -------------------------------------------------------------------------
        # Shop Themes & Motifs
        # -------------------------------------------------------------------------
        "shop": {
            "themes": [
                "The Cozy Chaos (Atmosphere: Bohemian, Outgoing, Generous)",
                "The Faint Hand of Law (Regulation: Anarchic, Distrustful)",
                "The Bureaucratic Quagmire (Regulation: Bureaucratic, Overly Serious)",
                "The Noble's Ledger (Governance: Aristocratic, Proud)",
            ],
            "motifs": [
                "Messy Counter, Bartering Encouraged, Strong Coffee Smell",
                "Back Room Deals, Barred Windows, No Visible Signage",
                "Stamped Forms, Waiting Lines, Multiple Copies of Receipts",
                "Velvet Ropes, High Prices, Only Deals in Silver",
            ],
        },
        # -------------------------------------------------------------------------
        # Vehicle Themes & Motifs
        # -------------------------------------------------------------------------
        "vehicle": {
            "themes": [
                "The Silent Phantom (Performance: Stealthy, Fast, Lightly Armored)",
                "The Mobile Fortress (Defense: Heavily Armored, Heavily Armed, Slow)",
                "The Tinkerer's Dream (Quality: Well Designed, Well Maintained, Reliable)",
                "The Rust Bucket (Quality: Poorly Designed, Poorly Maintained, Loud)",
            ],
            "motifs": [
                "Dampening Fields, Sleek Black Hull, Invisible Wake",
                "Rivets and Welds, Smoking Exhaust, Turret Guns",
                "Polished Brass, Soft Suspension, Always Starts on the First Try",
                "Squeaking Axles, Wire Repairs, Blue Smoke",
            ],
        },
        # -------------------------------------------------------------------------
        # Item Themes & Motifs
        # -------------------------------------------------------------------------
        "item": {
            "themes": [
                "Echoes of Legend (Rarity: Legendary, Artifacts, Unique)",
                "The Maddening Touch (Magic: Cursed, Sentient, Magical)",
                "Simple Necessity (Value: Common, Mundane, Reliable)",
                "The Collector's Prize (Rarity: Rare, Very Rare, Valuable)",
            ],
            "motifs": [
                "Faint Humming, Runes That Shift, Warm to the Touch",
                "Unwanted Whispers, A Shadow That Lingers, Causes Strange Dreams",
                "Worn Leather, Consistent Function, No Stories Attached",
                "Display Case, Security Wards, Written Appraisal",
            ],
        },
        # -------------------------------------------------------------------------
        # Encounter Themes & Motifs
        # -------------------------------------------------------------------------
        "encounter": {
            "themes": [
                "The Trial of Skill (Difficulty: Difficult, Deadly, Scenario: Combat)",
                "The Fading Footprints (Conflict: Investigation, Scenario: Exploration, Mystery)",
                "The Diplomatic Knot (Scenario: Social, Conflict: Ambush, Stealth)",
                "The Test of Wits (Conflict: Puzzle, Trap, Difficulty: Easy/Difficult)",
                "The Sudden Strike (Conflict: Ambush, Stealth, Scenario: Combat)",
            ],
            "motifs": [
                "Bloodstains, Broken Weapons, The Ring of Steel",
                "Old Maps, A Locked Journal, Dust Settling on a Desk",
                "Cloaks and Daggers, A Poisoned Chalice, The Silence Before the Offer",
                "Glyphs, Pressure Plates, A Riddle Engraved on a Door",
                "Silence Followed by Chaos, Arrows from the Dark, Cries of Surprise",
            ],
        },
    }
    ############# Class Methods #############

    @classmethod
    def sanitize(cls, data):
        if isinstance(data, str):
            data = BeautifulSoup(data, "html.parser").get_text()
        return data

    @classmethod
    def htmlize(cls, text):
        if isinstance(text, str):
            text = (
                markdown.markdown(text.replace("```markdown", "").replace("```", ""))
                .replace("h1>", "h3>")
                .replace("h2>", "h4>")
                .replace("h3>", "h5>")
                .replace("h4>", "h6>")
            )
        if len(text) < 100:
            text = cls.sanitize(text)
        return text

    @classmethod
    def map_prompt(cls, obj):
        return f"""{cls._map_prompts[obj.model_name().lower()](obj)}

    !!IMPORTANT!!: DIRECTLY OVERHEAD TOP DOWN 2D VIEW, NO 3D perspective, NO isometric view, NO TEXT, NO CREATURES, NO CHARACTERS, NO GRID, NO UI, NO ICONS, NO SYMBOLS, NO SCALE BAR, NO LEGEND, NO WATERMARK, NO BORDER, IMAGE EDGE TO EDGE, NO TITLE, NO COMPASS ROSE, HIGH DETAIL LEVEL, VIVID COLORS, HIGH CONTRAST, DETAILED TEXTURE AND SHADING
    """

    ############# Property Methods #############

    @property
    def text_agent(self):
        if not self.text_client:
            log("Creating new text agent...")
            self.text_client = TextAgent(
                name=f"{self._genre} TableTop RPG Worldbuiding Content Agent",
                instructions=self.instructions,
                description=self.description,
            )
            self.text_client.save()
            self.save()
            log(f"Created new text agent with id: {self.text_client.get_agent_id()}")
        return self.text_client

    @property
    def json_agent(self):
        if not self.json_client:
            log("Creating new json agent...")
            self.json_client = JSONAgent(
                name=f"{self._genre} TableTop RPG Worldbuiding JSON Agent",
                instructions=self.instructions,
                description=self.description,
            )
            self.json_client.save()
            self.save()
        return self.json_client

    @property
    def instructions(self):
        return f"""You are highly skilled and creative AI trained to assist completing the object data for a {self._genre} Table Top RPG. The existing data is provided as structured JSON data describing the schema for characters, creatures, items, locations, encounters, and storylines. You should rephrase and expand on the object's existing data where appropriate, but not ignore it.

        While the new enitity should be unique, there should also be appropriate connections to one or more existing elements in the world as described."""

    @property
    def description(self):
        return f"A helpful AI assistant trained to return structured JSON data for help in world-building a consistent, mysterious, and dangerous universe as the setting for a series of {self._genre} TTRPG Sandbox campaigns."

    @property
    def classes(self):
        return self._classes

    @property
    def backgrounds(self):
        return self._backgrounds

    ############# CRUD Methods #############

    def foundry_export(self, obj):
        return obj.page_data()

    def get_title(self, model):
        return self._titles.get(model, "Object")

    def get_skills(self, actor=None):
        if actor:
            # log(actor.dexterity, (actor.dexterity - 10) // 2)
            result = {
                "Acrobatics": (int(actor.dexterity) - 10) // 2,
                "Animal Handling": (int(actor.charisma) - 10) // 2,
                "Arcana": (int(actor.intelligence) - 10) // 2,
                "Athletics": (int(actor.dexterity) - 10) // 2,
                "Deception": (int(actor.charisma) - 10) // 2,
                "History": (int(actor.intelligence) - 10) // 2,
                "Insight": (int(actor.wisdom) - 10) // 2,
                "Intimidation": (int(actor.charisma) - 10) // 2,
                "Investigation": (int(actor.intelligence) - 10) // 2,
                "Medicine": (int(actor.intelligence) - 10) // 2,
                "Nature": (int(actor.intelligence) - 10) // 2,
                "Perception": (int(actor.wisdom) - 10) // 2,
                "Performance": (int(actor.charisma) - 10) // 2,
                "Persuasion": (int(actor.charisma) - 10) // 2,
                "Religion": (int(actor.wisdom) - 10) // 2,
                "Sleight of Hand": (int(actor.dexterity) - 10) // 2,
                "Stealth": (int(actor.dexterity) - 10) // 2,
                "Survival": (int(actor.wisdom) - 10) // 2,
            }
        else:
            result = {
                "Acrobatics": random.randint(-2, 5),
                "Animal Handling": random.randint(-2, 5),
                "Arcana": random.randint(-2, 5),
                "Athletics": random.randint(-2, 5),
                "Deception": random.randint(-2, 5),
                "History": random.randint(-2, 5),
                "Insight": random.randint(-2, 5),
                "Intimidation": random.randint(-2, 5),
                "Investigation": random.randint(-2, 5),
                "Medicine": random.randint(-2, 5),
                "Nature": random.randint(-2, 5),
                "Perception": random.randint(-2, 5),
                "Performance": random.randint(-2, 5),
                "Persuasion": random.randint(-2, 5),
                "Religion": random.randint(-2, 5),
                "Sleight of Hand": random.randint(-2, 5),
                "Stealth": random.randint(-2, 5),
                "Survival": random.randint(-2, 5),
            }
        # log(result)
        return result

    def delete(self):
        if self.text_client:
            self.text_client.delete()
        if self.json_client:
            self.json_client.delete()

    ############# Generation Methods #############

    def generate(self, obj, prompt, funcobj):
        additional = f"\n\nIMPORTANT: The generated data must be new, unique, consistent with, and connected to the world data described. If existing data is present in the object, expand on the {obj.title} data by adding greater specificity where possible, while ensuring the original concept remains unchanged. The result must be in VALID JSON format."
        prompt = self.sanitize(prompt)
        log(f"=== generation prompt ===\n\n{prompt}", _print=True)
        log(f"=== generation function ===\n\n{funcobj}", _print=True)
        response = self.json_agent.generate(
            prompt, function=funcobj, additional_instructions=additional
        )
        log(f"=== generation response ===\n\n{response}", _print=True)

        return response

    def generate_text(self, prompt, primer=""):
        prompt = self.sanitize(prompt)
        return self.text_agent.generate(prompt, additional_instructions=primer)

    def generate_json(self, prompt, primer, funcobj):
        prompt = self.sanitize(prompt)
        response = self.json_agent.generate(
            prompt, function=funcobj, additional_instructions=primer
        )
        return response

    def generate_summary(self, prompt, primer=""):
        prompt = self.sanitize(prompt)
        updated_prompt_list = []
        # Find all words in the prompt
        words = re.findall(r"\w+", prompt)

        # Split the words into chunks
        for i in range(0, len(words), self.MAX_TOKEN_LENGTH):
            # Join a chunk of words and add to the list
            updated_prompt_list.append(" ".join(words[i : i + self.MAX_TOKEN_LENGTH]))

        summary = ""
        for p in updated_prompt_list:
            summary += f"{self.text_agent.summarize_text(summary + p, primer=primer)}"

        return summary
