import random

from autonomous import log
from autonomous.model.autoattr import BoolAttr, ListAttr, StringAttr
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
    features = ListAttr(StringAttr(default=""))

    _rarity_list = ["common", "uncommon", "rare", "very rare", "legendary", "artifact"]
    parent_list = ["Creature", "Character", "Location", "District", "Encounter"]
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
                    "description": "A list of stats and special features of the item, if any.",
                    "items": {"type": "string"},
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
    def image_prompt(self):
        return f"A full color image of an item on display called a {self.name} and described as follows: {self.desc}."

    @property
    def map(self):
        return self.parent.map if self.parent else self.world.map

    ################### Instance Methods #####################

    def page_data(self):
        return {
            "pk": str(self.pk),
            "name": self.name,
            "rarity": self.rarity if self.rarity else "Unknown",
            "history": self.history if self.history else "Unknown",
            "cost": self.cost if self.cost else "Unknown",
            "duration": self.duration if self.duration else "Unknown",
            "weight": self.weight if self.weight else "Unknown",
            "features": self.features,
        }

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
