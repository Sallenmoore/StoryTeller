import random
import re

from models.systems.scifi import SciFiSystem


class StarsWithoutNumber(SciFiSystem):
    # meta = {"collection": "SciFiSystem"}

    _system_name = "Stars Without Number"

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

    _backgrounds = {
        "Academic": "A character with a scholarly or research-focused background, skilled in knowledge and analysis.",
        "Artist": "A creative individual, such as a painter, musician, or writer, with talents in expression and performance.",
        "Criminal": "Someone with a history in illegal activities, adept at deception, sneaking, and underworld connections.",
        "Entertainer": "A performer skilled at captivating audiences, whether through acting, music, or other talents.",
        "Merchant": "An experienced trader or businessperson, knowledgeable about commerce, negotiation, and finance.",
        "Noble": "A character from a wealthy or influential family, skilled in leadership and navigating social hierarchies.",
        "Peasant": "A background rooted in farming or rural labor, with practical survival and work skills.",
        "Pilot": "An expert in operating and navigating vehicles, particularly starships and other advanced machinery.",
        "Politician": "A background rooted in political maneuvering and influence, skilled in negotiation, leadership, and subterfuge.",
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

    def get_skills(self, actor=None):
        # 2. Define Skills and their Associated Governing Attribute
        skill_attributes = {
            "Administer": "intelligence",
            "Connect": "charisma",
            "Exert": "strength",
            "Fix": "intelligence",
            "Heal": "wisdom",
            "Know": "intelligence",
            "Lead": "charisma",
            "Notice": "wisdom",
            "Perform": "charisma",
            "Pilot": "dexterity",
            "Program": "intelligence",
            "Punch": "strength",
            "Shoot": "dexterity",
            "Sneak": "dexterity",
            "Stab": "dexterity",
            "Survive": "constitution",
            "Talk": "charisma",
            "Trade": "charisma",
            "Work": "strength",
        }

        # 3. Calculate Final Weighted Skill Results
        weighted_skill_results = {}
        for skill, attr in skill_attributes.items():
            # Base Skill Level (your random.randint(-1, 2) component)
            base_level = random.randint(-1, 2)
            # Attribute Bonus (The weight/modifier based on the attribute)
            if actor and getattr(actor, attr):
                attr_bonus = random.randint(
                    -2, max([(int(getattr(actor, attr)) - 10) // 2, -1])
                )
            else:
                attr_bonus = 0
            # Final Weighted Skill Result
            final_result = base_level + attr_bonus

            weighted_skill_results[skill] = final_result
        return weighted_skill_results

    def foundry_export(self, obj):
        data = obj.page_data()
        if obj.model_name() == "Character":
            return self.foundry_character_export(data)
        if obj.model_name() == "Creature":
            return self.foundry_creature_export(data)
        elif obj.model_name() == "Vehicle":
            return self.foundry_vehicle_export(data)
        elif obj.model_name() == "Item":
            return self.foundry_item_export(data)
        elif obj.model_name() in [
            "Faction",
            "City",
            "Region",
            "World",
            "Location",
            "District",
            "Shop",
            "DungeonRoom",
        ]:
            return self.foundry_place_export(data)
        else:
            raise Exception("Unsupported model for SWN foundry export")

        return data

    def foundry_creature_export(self, source_data):
        """
        Transforms a generic 'mech' (or similar NPC) JSON object into the specific
        Systems Without Number (SWN) "character" Actor document schema.
        """
        # 1. Define the target schema structure with required defaults
        target_schema = {
            "name": "Character",
            "type": "character",
            "img": "icons/svg/mystery-man.svg",
            "system": {
                "health": {"value": 10, "max": 10},
                "biography": "",
                "species": "",
                "access": {"value": 1, "max": 1},
                "traumaTarget": 6,
                "baseAc": 10,
                "meleeAc": 10,
                "ab": 1,
                "meleeAb": 1,
                "systemStrain": {"value": 0, "permanent": 0},
                "pools": {},
                "effortCommitments": {},
                "speed": 10,
                "cyberdecks": [],
                "health_max_modified": 0,
                "stats": {
                    "str": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "dex": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "con": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "int": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "wis": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "cha": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                },
                "hitDie": "d6",
                "level": {"value": 1, "exp": 0, "expToLevel": 3},
                "goals": "",
                "class": "",
                "homeworld": "",
                "background": "",
                "employer": "",
                "languages": [],
                "credits": {"debt": 0, "balance": 0, "owed": 0},
                "unspentSkillPoints": 0,
                "unspentPsySkillPoints": 0,
                "extra": {"value": 0, "max": 10},
                "tweak": {
                    "advInit": False,
                    "showResourceList": False,
                    "showCyberware": True,
                    "showPsychic": True,
                    "showArts": False,
                    "showSpells": False,
                    "showAdept": False,
                    "showMutation": False,
                    "showPoolsInHeader": False,
                    "showPoolsInPowers": True,
                    "showPoolsInCombat": True,
                    "resourceList": [],
                    "debtDisplay": "Debt",
                    "owedDisplay": "Owed",
                    "balanceDisplay": "Balance",
                    "initiative": {},
                },
            },
            "prototypeToken": {
                "name": "Character",
                "displayName": 0,
                "actorLink": False,
                "width": 1,
                "height": 1,
                "texture": {"src": "icons/svg/mystery-man.svg"},
                "bar1": {"attribute": "health"},
                "bar2": {"attribute": "power"},
            },
            "items": [],
            "effects": [],
            "flags": {},
            "ownership": {"default": 0},
            "_stats": {},
        }

        # Helper function to safely get attribute base score
        def get_attr_score(attr_key, default=9):
            # Source uses 'dexerity', target uses 'dex'
            key_map = {"dexerity": "dex"}
            final_key = key_map.get(attr_key, attr_key)

            # We assume the source attribute scores are the Base scores
            return int(
                source_data.get("attributes", {}).get(
                    final_key, source_data.get("attributes", {}).get(attr_key, default)
                )
            )

        # 2. Map Core Fields (Name, Image, Health, AC, Speed)
        char_name = source_data.get("name", "Unknown Character").strip()
        target_schema["name"] = char_name
        target_schema["prototypeToken"]["name"] = char_name

        if url := source_data.get("image", "").strip():
            target_schema["img"] = f"https://storyteller.stevenamoore.dev{url}"

        # Health (Hit Points)
        hp = int(source_data.get("hit points", 10))
        target_schema["system"]["health"]["value"] = hp
        target_schema["system"]["health"]["max"] = hp

        # AC
        target_schema["system"]["baseAc"] = int(source_data.get("ac", 10))
        target_schema["system"]["meleeAc"] = int(source_data.get("ac", 10))

        # Speed
        target_schema["system"]["speed"] = int(source_data.get("speed", 10))

        # Archetype -> Class and Species
        target_schema["system"]["class"] = source_data.get("archetype", "").strip()
        target_schema["system"]["species"] = source_data.get("species", "").strip()

        # Level
        target_schema["system"]["level"]["value"] = int(source_data.get("level", 1))

        # 3. Map Attributes (Stats)
        for stat_key in target_schema["system"]["stats"].keys():
            score = get_attr_score(stat_key)
            target_schema["system"]["stats"][stat_key]["base"] = score

        # 4. Map Narrative Fields (Biography and Goals)
        skills_list = [
            f"<li><strong>{k}:</strong> {v}</li>"
            for k, v in source_data.get("skills", {}).items()
            if v
        ]

        # Combine description fields into biography
        combined_biography = f"""
            <h2>Physical Description & Archetype</h2>
            <p><strong>Archetype:</strong> {source_data.get("archetype", "N/A")}</p>
            <p><strong>Species:</strong> {source_data.get("species", "N/A")}</p>
            <p>{source_data.get("desc", "No physical description provided.")}</p>

            <h2>History</h2>
            {source_data.get("history", "")}

            <h2>Skills (Reference Only)</h2>
            <ul>{"".join(skills_list) if skills_list else "<li>No non-default skill values provided.</li>"}</ul>
        """
        target_schema["system"]["biography"] = combined_biography.strip()
        target_schema["system"]["goals"] = source_data.get("goal", "").strip()

        return target_schema

    def foundry_character_export(self, source_data):
        """
        Transforms a generic 'mech' or 'human' JSON object into the specific
        Systems Without Number (SWN) "character" Actor document schema.
        """
        # 1. Define the target schema structure with required defaults
        target_schema = {
            "name": "Character",
            "type": "character",
            "img": "icons/svg/mystery-man.svg",
            "system": {
                "health": {"value": 10, "max": 10},
                "biography": "",
                "species": "",
                "access": {"value": 1, "max": 1},
                "traumaTarget": 6,
                "baseAc": 10,
                "meleeAc": 10,
                "ab": 1,
                "meleeAb": 1,
                "systemStrain": {"value": 0, "permanent": 0},
                "pools": {},
                "effortCommitments": {},
                "speed": 10,
                "cyberdecks": [],
                "health_max_modified": 0,
                "stats": {
                    "str": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "dex": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "con": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "int": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "wis": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                    "cha": {"base": 9, "bonus": 0, "boost": 0, "temp": 0},
                },
                "hitDie": "d6",
                "level": {"value": 1, "exp": 0, "expToLevel": 3},
                "goals": "",
                "class": "",
                "homeworld": "",
                "background": "",
                "employer": "",
                "languages": [],
                "credits": {"debt": 0, "balance": 0, "owed": 0},
                "unspentSkillPoints": 0,
                "unspentPsySkillPoints": 0,
                "extra": {"value": 0, "max": 10},
                "tweak": {
                    "advInit": False,
                    "showResourceList": False,
                    "showCyberware": True,
                    "showPsychic": True,
                    "showArts": False,
                    "showSpells": False,
                    "showAdept": False,
                    "showMutation": False,
                    "showPoolsInHeader": False,
                    "showPoolsInPowers": True,
                    "showPoolsInCombat": True,
                    "resourceList": [],
                    "debtDisplay": "Debt",
                    "owedDisplay": "Owed",
                    "balanceDisplay": "Balance",
                    "initiative": {},
                },
            },
            "prototypeToken": {
                "name": "Character",
                "displayName": 0,
                "actorLink": False,
                "width": 1,
                "height": 1,
                "texture": {"src": "icons/svg/mystery-man.svg"},
                "bar1": {"attribute": "health"},
                "bar2": {"attribute": "power"},
            },
            "items": [],
            "effects": [],
            "flags": {},
            "ownership": {"default": 0},
            "_stats": {},
        }

        # Helper function to safely get attribute base score
        def get_attr_score(attr_key, default=9):
            # Source uses 'dexerity', target uses 'dex'
            key_map = {
                "dex": "dexerity",
                "int": "intelligence",
                "con": "constitution",
                "wis": "wisdom",
                "cha": "charisma",
                "str": "strength",
            }
            final_key = key_map.get(attr_key)
            # We assume the source attribute scores are the Base scores
            # log(final_key, attr_key, source_data.get("attributes", {}))
            result = int(source_data.get("attributes", {}).get(final_key, 9))
            # log(result)
            return result

        # 2. Map Core Fields (Name, Image, Health, AC, Speed)
        char_name = source_data.get("name", "Unknown Character").strip()
        target_schema["name"] = char_name
        target_schema["prototypeToken"]["name"] = char_name

        if url := source_data.get("image", "").strip():
            target_schema["img"] = f"https://storyteller.stevenamoore.dev{url}"

        # Health (Hit Points)
        hp = int(source_data.get("hitpoints", 10))
        target_schema["system"]["health"]["value"] = hp
        target_schema["system"]["health"]["max"] = hp

        # AC
        target_schema["system"]["baseAc"] = int(source_data.get("ac", 10))
        target_schema["system"]["meleeAc"] = int(source_data.get("ac", 10))

        # Speed
        target_schema["system"]["speed"] = int(source_data.get("speed", 10))

        # Occupation -> Class and Species
        target_schema["system"]["class"] = source_data.get("occupation", "").strip()
        target_schema["system"]["species"] = source_data.get("species", "").strip()

        # Level (default to 1 since source JSON doesn't provide it)
        target_schema["system"]["level"]["value"] = int(source_data.get("level", 1))

        # 3. Map Attributes (Stats)
        # log(target_schema["system"]["stats"].keys())
        for stat_key in target_schema["system"]["stats"].keys():
            score = get_attr_score(stat_key)
            target_schema["system"]["stats"][stat_key]["base"] = score

        skill_items = []
        SKILL_TYPES = ["combat", "noncombat", "psychic"]
        for k, v in source_data.get("skills", {}).items():
            # Determine the type. SWN system uses 'noncombat' for standard skills.
            skill_type = "noncombat"

            # The core requirement: A new Item document object for each skill.
            skill_item = {
                "name": k,
                "type": "skill",  # Important: this must match the Item Type for SWN skills
                "img": f"icons/svg/{skill_type}.svg",  # Default icon based on type
                "system": {
                    # SWN stores the score/level under 'level.value'
                    "level": {
                        "value": int(v)
                        or 0,  # Convert string score ("-1", "0") to integer
                        "max": 5,
                    },
                    # Other required fields for a minimal skill Item
                    "description": "",
                    "favorite": False,
                },
            }
            skill_items += [skill_item]
        target_schema["items"] = skill_items

        # Combine description fields into biography
        combined_biography = f"""
            <h2>Character Details</h2>
            <p><strong>Species:</strong> {source_data.get("species", "N/A")}</p>
            <p><strong>Class/Occupation:</strong> {source_data.get("occupation", "N/A")}</p>
            <p><strong>Gender:</strong> {source_data.get("gender", "Unknown")}</p>
            <p><strong>Age:</strong> {source_data.get("age", "Unknown")}</p>
            <hr/>

            <h2>Physical Description</h2>
            <p>{source_data.get("desc", "No physical description provided.")}</p>

            <h2>Backstory Snippets</h2>
            {source_data.get("backstory", "")}

            <h2>Detailed History</h2>
            {source_data.get("history", "")}
        """
        target_schema["system"]["biography"] = combined_biography.strip()
        target_schema["system"]["goals"] = source_data.get("goal", "").strip()

        return target_schema

    def foundry_vehicle_export(self, source_data):
        """
        Transforms a generic starship JSON object into the specific Systems Without Number (SWN)
        "ship" Actor document schema.
        """
        target_schema = {
            "name": source_data.get("name"),
            "type": source_data.get("type"),
            "make": source_data.get("make"),
            "img": "systems/swnr/assets/icons/spaceship.png",
            "system": {
                "health": {"value": 10, "max": 10},
                "cost": 0,
                "ac": 10,
                "traumaTarget": 6,
                "armor": {"value": 1, "max": 1},
                "speed": 1,
                "crew": {"min": 1, "current": 1, "max": 1},
                "crewMembers": [],
                "tl": 5,
                "description": "",
                "mods": "",
                "power": {"value": 1, "max": 1},
                "mass": {"value": 1, "max": 1},
                "hardpoints": {"value": 1, "max": 1},
                "lifeSupportDays": {"value": 1, "max": 1},
                "fuel": {"value": 1, "max": 1},
                "cargo": {"value": 1, "max": 1},
                "spikeDrive": {"value": 1, "max": 1},
                "shipClass": "fighter",
                "shipHullType": "freeMerchant",
                "operatingCost": 1,
                "maintenanceCost": 1,
                "amountOwed": 0,
                "paymentAmount": 0,
                "paymentMonths": 0,
                "maintenanceMonths": 0,
                "creditPool": 0,
                "lastMaintenance": {"year": 0, "month": 0, "day": 0},
                "lastPayment": {"year": 0, "month": 0, "day": 0},
                "roles": {
                    "captain": None,
                    "bridge": None,
                    "engineering": None,
                    "gunner": None,
                    "comms": None,
                },
                "cargoCarried": [],
                "commandPoints": 0,
                "npcCommandPoints": 0,
                "crewSkillBonus": 0,
                "actionsTaken": [],
                "supportingDept": "",
                "roleOrder": [],
            },
            "prototypeToken": {
                # Only essential token fields are included for brevity; most can remain defaults
                "name": "Ship",
                "displayName": 0,
                "actorLink": False,
                "width": 1,
                "height": 1,
                "texture": {"src": "systems/swnr/assets/icons/spaceship.png"},
                "bar1": {"attribute": "health"},
                "bar2": {"attribute": "power"},
                # NOTE: Other prototypeToken fields are omitted here as they match the defaults
                # in your target schema (e.g., light, sight, detectionModes)
            },
            "items": [],
            "effects": [],
            "flags": {},
            "ownership": {"default": 0},
            "_stats": {},  # Leaving empty to be populated by Foundry
        }

        # 2. Map and clean core fields
        # Clean the name and apply it to both document and token prototype
        ship_name = source_data.get("name", "Unknown Ship").strip()
        target_schema["name"] = ship_name
        target_schema["prototypeToken"]["name"] = ship_name

        if url := source_data.get("image", "").strip():
            target_schema["img"] = f"https://storyteller.stevenamoore.dev{url}"

        # HP mapping
        hp = int(source_data.get("hitpoints", 10))
        target_schema["system"]["health"]["value"] = hp
        target_schema["system"]["health"]["max"] = hp

        # AC mapping
        target_schema["system"]["ac"] = int(source_data.get("ac", 10))

        # Armor mapping
        armor = int(source_data.get("armor", 1))
        target_schema["system"]["armor"]["value"] = armor
        target_schema["system"]["armor"]["max"] = armor

        # Speed mapping (extract first number)
        speed_text = source_data.get("speed", "50")
        speed_match = re.search(r"\d+", speed_text)
        target_schema["system"]["speed"] = (
            int(speed_match.group(0)) if speed_match else 1
        )

        # Cargo/Mass mapping (using capacity for Cargo Max)
        capacity = int(source_data.get("capacity", 1))
        target_schema["system"]["cargo"]["max"] = capacity

        # 3. Concatenate and clean description fields
        desc_text = source_data.get("desc", "")
        history_html = source_data.get("history", "")

        # Combine description fields, preserving a separation
        combined_desc = f"""
            <h2>Physical Description</h2>
            <p>{desc_text}</p>

            <h2>Detailed History</h2>
            {history_html}
        """

        # Store the combined HTML string in the system description field
        # (Foundry VTT expects HTML for this field)
        target_schema["system"]["description"] = combined_desc.strip()

        return target_schema

    def foundry_item_export(self, source_data):
        """
        Transforms a generic item JSON object into the specific Systems Without Number (SWN)
        "item" Item document schema.
        """
        # 1. Define the target schema structure with required defaults
        target_schema = {
            "name": "Item",
            "type": "item",
            "img": "icons/svg/item-bag.svg",
            "system": {
                "description": "",
                "favorite": False,
                "quantity": 1,
                "bundle": {"bundled": False},
                "encumbrance": 1,
                "cost": 0,
                "tl": None,
                "location": "stowed",
                "quality": "stock",
                "noEncReadied": False,
                "container": {
                    "isContainer": False,
                    "isOpen": True,
                    "capacity": {"max": 0, "value": 0},
                },
                "roll": {"diceNum": 1, "diceSize": "d20", "diceBonus": "+0"},
                "uses": {
                    "max": 1,
                    "value": 1,
                    "emptyQuantity": 0,
                    "consumable": "none",
                    "ammo": "none",
                    "keepEmpty": True,
                },
            },
            "effects": [],
            "flags": {},
            "_stats": {},
            "ownership": {"default": 0},
        }

        # 2. Map Core Fields
        item_name = source_data.get("name", "Unknown Item").strip()
        target_schema["name"] = item_name

        # Use 'image' for image path
        if url := source_data.get("image", "").strip():
            target_schema["img"] = f"https://storyteller.stevenamoore.dev{url}"

        # Extract Encumbrance (Weight)
        weight_text = source_data.get("weight", "1 lbs")
        weight_match = re.search(r"(\d+)", weight_text)
        target_schema["system"]["encumbrance"] = (
            int(weight_match.group(1)) if weight_match else 1
        )

        # Extract Cost (extract first number if possible, default to 0)
        cost_text = source_data.get("cost", "0 credits")
        cost_match = re.search(
            r"(\d+)", cost_text.replace(",", "")
        )  # Remove commas for large numbers
        target_schema["system"]["cost"] = int(cost_match.group(1)) if cost_match else 0

        # Rarity (map to quality)
        quality_translation = {
            "common": "jury-rigged",
            "uncommon": "stock",
            "rare": "stock",
            "very rare": "mastercrafted",
            "legendary": "mastercrafted",
            "artifact": "mastercrafted",
        }
        target_schema["system"]["quality"] = quality_translation.get(
            source_data.get("rarity").lower(), "stock"
        )

        # Consumable flag
        if source_data.get("consumbale", False):
            target_schema["system"]["uses"]["consumable"] = "single"

        # 3. Concatenate and map description fields
        history_html = source_data.get("history", "")
        features_list = source_data.get("features", [])

        # Format Features as a list of detailed descriptions
        formatted_features = ""
        if features_list:
            formatted_features += "<h2>Key Features and Actions</h2>"
            for feature in features_list:
                # Extract the name (before the first ':') and the description
                parts = feature.split(":", 1)
                feature_name = parts[0].strip()
                feature_desc = parts[1].strip() if len(parts) > 1 else ""

                # Use regex to extract action type if present (e.g., [main action])
                action_match = re.search(r"\[(.*?)\]", feature_name)
                action_type = (
                    f" ({action_match.group(1).title()})" if action_match else ""
                )
                feature_name_clean = re.sub(r"\[.*?\]", "", feature_name).strip()

                formatted_features += f"""
                <h3>{feature_name_clean}{action_type}</h3>
                {feature_desc}
                """

        # Combine history and features into the description field
        combined_desc = f"""
            {formatted_features.strip()}

            <h2>History and Lore</h2>
            {history_html}

            <p><strong>Rarity:</strong> {source_data.get("rarity", "Common").title()}</p>
            <p><strong>Cost:</strong> {source_data.get("cost", "0 credits")}</p>
            <p><strong>Duration:</strong> {source_data.get("duration", "Indefinite")}</p>
        """

        target_schema["system"]["description"] = combined_desc.strip()

        # 4. Attempt to parse roll data if needed (optional for general item)
        # The Asteroid Miner's Spike feature contains: DICE ROLL: Roll a D20 + Strength modifier to attack. On success, roll an additional D6 for extra damage.
        # We will not parse this complex roll, but leave roll fields as default for the user to configure.

        return target_schema

    def foundry_place_export(self, source_data):
        """
        Transforms a generic location JSON object into the standard Foundry VTT Scene document schema.

        The descriptive fields are combined into a single JournalEntryPage/Note document,
        as Foundry Scenes do not have a dedicated 'description' field.
        """
        # 1. Define the target schema structure (using a known SWN base template)
        target_schema = {
            "name": source_data.get("name", "New Scene").strip(),
            "navigation": False,
            "navOrder": 0,
            "background": {
                "src": "",
                "anchorX": 0,
                "anchorY": 0,
                "offsetX": 0,
                "offsetY": 0,
                "fit": "fill",
                "scaleX": 1.5,
                "scaleY": 1.5,
                "rotation": 0,
                "tint": "#ffffff",
                "alphaThreshold": 0,
            },
            "foreground": None,
            "foregroundElevation": None,
            "thumb": None,
            "width": 1344 * 1.5,
            "height": 768 * 1.5,
            "padding": 0,
            "initial": {"x": None, "y": None, "scale": None},
            "backgroundColor": "#000000",
            "grid": {
                "type": 2,
                "size": 50,
                "style": "solidLines",
                "thickness": 1,
                "color": "#000000",
                "alpha": 0.3,
                "distance": 5,
                "units": "ft",
            },
            "tokenVision": True,
            "fog": {
                "exploration": False,
                "overlay": None,
                "colors": {"explored": None, "unexplored": None},
            },
            "environment": {
                "darknessLevel": 0,
                "darknessLock": False,
                "globalLight": {
                    "enabled": True,
                    "alpha": 0.5,
                    "bright": False,
                    "color": None,
                    "coloration": 1,
                    "luminosity": 0,
                    "saturation": 0,
                    "contrast": 0,
                    "shadows": 0,
                    "darkness": {"min": 0, "max": 1},
                },
                "cycle": True,
                "base": {
                    "hue": 0,
                    "intensity": 0,
                    "luminosity": 0,
                    "saturation": 0,
                    "shadows": 0,
                },
                "dark": {
                    "hue": 0.7138888888888889,
                    "intensity": 0,
                    "luminosity": -0.25,
                    "saturation": 0,
                    "shadows": 0,
                },
            },
            "drawings": [],
            "tokens": [],
            "lights": [],
            "notes": [],
            "sounds": [],
            "regions": [],
            "templates": [],
            "tiles": [],
            "walls": [],
            "playlist": None,
            "playlistSound": None,
            "journal": None,
            "journalEntryPage": None,
            "weather": "",
            "folder": None,
            "flags": {},
            "_stats": {},
            "ownership": {"default": 0},
        }

        # 2. Map Core Fields
        scene_name = source_data.get("name", "Unknown Scene").strip()
        target_schema["name"] = scene_name

        # Scene Background Image (maps to background.src)
        # The source is null, so we explicitly set it to null or a default path if needed.
        # Use 'image' for image path
        if url := source_data.get("image", "").strip():
            target_schema["background"]["src"] = (
                f"https://storyteller.stevenamoore.dev{url}"
            )
        return target_schema
