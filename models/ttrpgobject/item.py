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
    artifact = BoolAttr(default=False)
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
                "artifact": {
                    "type": "boolean",
                    "description": "Whether the item is a one-of-a-kind or a mass-produced item",
                },
                "type": {
                    "type": "string",
                    "description": "The general category of the item, such as weapon, armor, tool, consumable, magical, technological, etc.",
                },
                "consumable": {
                    "type": "boolean",
                    "description": "Whether the item is consumed upon use",
                },
                "status": {
                    "type": "string",
                    "description": "current, immediate situation the item is in, such as being used, in storage, destroyed, etc.",
                },
                "desc": {
                    "type": "string",
                    "description": "A brief physical description that will be used to generate an image of the item",
                },
                "backstory": {
                    "type": "string",
                    "description": "The history of the item",
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
                "sensory_details": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of sensory details, such as sight, sound, smell, and touch, that a GM can use to bring the item to life",
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
        ability = Ability(
            world=self.world,
        )
        ability.generate(self)

        return results

    @property
    def abilities(self):
        return self.features

    @abilities.setter
    def abilities(self, value):
        self.features = value

    @property
    def image_prompt(self):
        return f"A full color image of an item called a {self.name} and described as follows on display: {self.desc}."

    @property
    def map(self):
        return self.parent.map if self.parent else None

    @property
    def title(self):
        return super().title + f" <small>({self.rarity})</small>"

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

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################
    @classmethod
    def auto_post_init(cls, sender, document, **kwargs):
        super().auto_post_init(sender, document, **kwargs)
        if not document.artifact:
            document.parent_list = []

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
        if self.rarity == "artifact":
            self.artifact = True
        if not self.artifact:
            self.parent = None

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
