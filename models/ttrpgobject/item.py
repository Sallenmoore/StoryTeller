import random
import re

import markdown
from autonomous.model.autoattr import BoolAttr, ListAttr, ReferenceAttr, StringAttr

from autonomous import log
from models.ttrpgobject.ability import Ability
from models.ttrpgobject.ttrpgobject import TTRPGObject


class Item(TTRPGObject):
    rarity = StringAttr(
        choices=["common", "uncommon", "rare", "very rare", "legendary", "artifact"],
        default="common",
    )
    consumable = BoolAttr(default=False)
    cost = StringAttr(default="")
    duration = StringAttr(default="")
    weight = StringAttr(default="")
    type = StringAttr(default="mundane")
    features = ListAttr(ReferenceAttr(choices=["Ability"]))

    start_date_label = "Created"
    end_date_label = "Destroyed"

    _rarity_list = ["common", "uncommon", "rare", "very rare", "legendary", "artifact"]
    parent_list = [
        "Creature",
        "Location",
        "Vehicle",
        "District",
        "City",
        "Region",
        "Character",
        "Encounter",
    ]
    _funcobj = {
        "name": "generate_item",
        "description": "creates Item data object",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "An descriptive, but unique name",
                },
                "desc": {
                    "type": "string",
                    "description": "A brief physical description that will be used to generate an image of the item",
                },
                "backstory": {
                    "type": "string",
                    "description": "The history of the item",
                },
                "features": {
                    "type": "array",
                    "description": "Generate at least 3 combat abilities AND 3 special ability objects for the array. Each object in the array should have attributes for the ability name, detailed description in MARKDOWN, effects, duration, and the dice roll mechanics involved in using the ability.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "name",
                            "action",
                            "description",
                            "effects",
                            "duration",
                            "dice_roll",
                        ],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Unique name for the Feature.",
                            },
                            "action": {
                                "type": "string",
                                "enum": [
                                    "main action",
                                    "bonus action",
                                    "reaction",
                                    "free action",
                                    "passive",
                                ],
                                "description": "Type of action required.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of the feature and how it is activated in MARKDOWN.",
                            },
                            "effects": {
                                "type": "string",
                                "description": "Description of the features's effects.",
                            },
                            "duration": {
                                "type": "string",
                                "description": "The duration of the features's effects.",
                            },
                            "dice_roll": {
                                "type": "string",
                                "description": "The dice roll mechanics for determining the success or failure of the feature.",
                            },
                        },
                    },
                },
                "weight": {
                    "type": "string",
                    "description": "The weight of the item",
                },
                "rarity": {
                    "type": "string",
                    "description": "How rare is the item from one of the following: [common, uncommon, rare, very rare, legendary, artifact]",
                },
                "cost": {
                    "type": "string",
                    "description": "How much does the item cost in local currency",
                },
                "duration": {
                    "type": "string",
                    "description": "How long will the item last before it breaks or is used up",
                },
            },
        },
    }

    ################### Dunder Methods #####################

    ################### Crud Methods #####################
    def generate(self):
        prompt = f"Generate a {self.genre} loot item for a {self.genre} TTRPG with detailed stats and a backstory containing {random.choices(('a common', 'a long hidden', 'a mysterious', 'a sinister and dangerous'), (10, 5, 2, 1))} origin. There is a 20% chance the item has a secret special feature or ability."
        for i in ["rarity", "cost", "duration", "weight", "features"]:
            if getattr(self, i):
                prompt += f"""
        {i}: {getattr(self, i)}
        """
        results = super().generate(
            prompt=prompt,
        )

        return results

    @property
    def abilities(self):
        return self.features

    @abilities.setter
    def abilities(self, value):
        self.features = value

    @property
    def image_prompt(self):
        return f"A full color image of an item on display called a {self.name} and described as follows: {self.desc}."

    @property
    def map(self):
        return self.parent.map if self.parent else None

    ################### Instance Methods #####################

    def page_data(self):
        if not self.history:
            self.resummarize()
        return {
            "pk": str(self.pk),
            "image": str(self.image.url()) if self.image else "",
            "name": self.name,
            "rarity": self.rarity if self.rarity else "Unknown",
            "history": self.history if self.history else "Unknown",
            "cost": self.cost if self.cost else "Unknown",
            "duration": self.duration if self.duration else "Unknown",
            "weight": self.weight if self.weight else "Unknown",
            "consumbale": self.consumable,
            "type": self.type if self.type else "Unknown",
            "features": [str(a) for a in self.features],
        }

    def foundry_export(self):
        source_data = self.page_data()
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

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_rarity()
        document.pre_save_feature()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################

    def pre_save_rarity(self):
        self.rarity = self.rarity.strip()
        if self.rarity not in self._rarity_list:
            self.rarity = self._rarity_list[-1]

    def pre_save_feature(self):
        # log(self.features, _print=True)
        for idx, feature in enumerate(self.features):
            # log(feature)
            if isinstance(feature, str):
                a = Ability(description=feature)
                a.save()
                self.features[idx] = a
            elif isinstance(feature, dict):
                a = Ability(**feature)
                a.save()
                self.features[idx] = a
            else:
                feature.description = (
                    markdown.markdown(feature.description.replace("```markdown", ""))
                    .replace("h1>", "h3>")
                    .replace("h2>", "h3>")
                )

        self.features = [a for a in self.features if a.name]

        # log(self.features, _print=True)
