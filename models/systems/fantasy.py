import os
import re

from autonomous import log
from models.systems.basesystem import BaseSystem


class FantasySystem(BaseSystem):
    meta = {
        "allow_inheritance": True,
        "strict": False,
    }

    _genre = "Fantasy"

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
        "shop": "Shop",
        "vehicle": "Vehicle",
        "district": "District",
        "item": "Item",
        "encounter": "Encounter",
        "character": "Character",
    }

    SKILL_MAP_ABBREV = {
        "Acrobatics": "acr",
        "Animal Handling": "ani",
        "Arcana": "arc",
        "Athletics": "ath",
        "Deception": "dec",
        "History": "his",
        "Insight": "ins",
        "Intimidation": "itm",
        "Investigation": "inv",
        "Medicine": "med",
        "Nature": "nat",
        "Perception": "prc",  # Note: Foundry D&D 5e often uses 'prc' for Perception
        "Performance": "prf",
        "Persuasion": "per",
        "Religion": "rel",
        "Sleight of Hand": "slt",
        "Stealth": "ste",
        "Survival": "sur",
    }

    def foundry_export(self, obj):
        data = obj.page_data()
        if obj.model_name() in ["Character", "Creature"]:
            return self.foundry_actor_export(data)
        elif obj.model_name() == "Vehicle":
            return self.foundry_vehicle_export(data)
        elif obj.model_name() == "Item":
            return self.foundry_item_export(data)
        elif obj.model_name() in [
            "City",
            "Region",
            "World",
            "Location",
            "District",
            "Shop",
            "DungeonRoom",
        ]:
            return self.foundry_place_export(data)

        return data

    def foundry_actor_export(self, source_data):
        # --- 1. Map Abilities (Attributes) ---
        foundry_abilities = {}
        for name, value in source_data["attributes"].items():
            # D&D 5e uses str, dex, con, int, wis, cha.
            # Assuming your source keys are correct:
            code = name[:3].lower()  # Simple mapping (str, dex, con...)
            foundry_abilities[code] = {
                "value": value,
                "proficient": 0,  # Assume no proficiency here, based on source data
                "check": {},
                "save": {},
                "bonuses": {},
            }

        # --- 3. Build the Core System Payload ---
        foundry_payload = {
            # --- Root Level ---
            "name": source_data["name"],
            "type": "npc" if source_data.get("type", False) else "character",
            "system": {
                "abilities": foundry_abilities,
                "attributes": {
                    "hp": {
                        "value": source_data["hitpoints"],
                        "max": source_data["hitpoints"],
                        "temp": None,
                        "tempmax": None,
                    },
                    "movement": {
                        "walk": source_data["speed"],
                        "units": source_data["speed_units"].lower()
                        if source_data.get("speed_units")
                        else "ft",
                    },
                    "ac": {
                        "value": source_data["ac"],
                    },  # Placeholder AC, calculated by D&D 5e system
                },
                "details": {
                    "race": source_data.get("species", ""),
                    "level": 1,  # Default level for character sync
                    "occupation": source_data.get("archetype", ""),
                    "biography": {
                        "value": source_data[
                            "history"
                        ],  # Detailed history/backstory HTML
                        "public": f"<h1>{source_data['archetype']}</h1>",
                    },
                    "appearance": source_data.get("desc", ""),
                },
            },
            ##--- Token Prototype Data ---
            "prototypeToken": {
                "name": source_data["name"],
                "actorLink": True,
                "bar1": {"attribute": "attributes.hp"},
                "displayBars": 0,
                "displayName": 0,
                "disposition": 1,  # Neutral disposition (Hostile= -1, Friendly= 1)
                "texture": {"src": ""},
                "sight": {
                    "enabled": True,
                    "range": 5,
                    "angle": 360,
                    "visionMode": "basic",
                },
            },
        }
        log(foundry_payload)
        return foundry_payload

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
            "padding": 0,
            "initial": {"x": None, "y": None, "scale": None},
            "backgroundColor": "#292828",
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
                "exploration": True,
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
            "width": 1344 * 1.5,
            "height": 768 * 1.5,
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

        # 3. Combine description fields into a Note document
        desc_text = source_data.get("desc", "")
        history_html = source_data.get("history", "")

        # Combine all narratives into a single HTML block
        combined_notes_content = f"""
            <h2>Description</h2>
            <p>{desc_text}</p>
            <h2>History</h2>
            {history_html}

        """

        # Create the embedded Note document structure
        embedded_note = {
            "name": f"{source_data.get('name', 'New Scene').strip()} Description",
            "text": combined_notes_content.strip(),
            "fontFamily": None,
            "fontSize": 48,
            "textAnchor": 1,
            "textColor": None,
            "x": 25,  # Placeholder coordinates
            "y": 25,  # Placeholder coordinates
            "visibility": 1,  # Visible to GM
            "flags": {},
        }

        # Add the note to the scene's notes array
        target_schema["notes"].append(embedded_note)
        return target_schema
