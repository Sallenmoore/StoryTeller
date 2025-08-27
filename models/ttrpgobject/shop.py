import random

from autonomous.model.autoattr import ListAttr, StringAttr
from models.base.place import Place


class Shop(Place):
    inventory_ = ListAttr(StringAttr(default=""))

    _funcobj = {
        "name": "generate_location",
        "description": "builds a Location model object",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "An intriguing, suggestive, and unique name",
                },
                "location_type": {
                    "type": "string",
                    "description": "The type of shop",
                },
                "backstory": {
                    "type": "string",
                    "description": "A description of the history of the shop. Only include what would be publicly known information.",
                },
                "inventory": {
                    "type": "array",
                    "description": "A list of inventory items in the shop.",
                    "items": {
                        "type": "string",
                        "description": "The name, short description, and cost of an item that can be found in the shop. There should be more mundane items than specialty items.",
                    },
                },
                "desc": {
                    "type": "string",
                    "description": "A short physical description that will be used to generate an evocative image of the shop",
                },
                "sensory_details": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of sensory details, such as sight, sound, smell, and touch, that a GM can use to bring the location to life",
                },
                "recent_events": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A concise list of significant events that have recently occurred in this location, even if they aren't ongoing situations. Only include publicly known information.",
                },
            },
        },
    }

    categories = [
        "market",
        "shop",
        "tavern",
    ]

    parent_list = [
        "Location",
        "District",
        "City",
    ]

    @property
    def inventory(self):
        return self.inventory_ + [i.name for i in self.items]

    @inventory.setter
    def inventory(self, value):
        self.inventory_ = value

    def generate(self, prompt=""):
        # log(f"Generating data with AI for {self.name} ({self})...", _print=True)
        prompt = (
            prompt
            or f"Generate a {self.genre} TTRPG {random.choice(self.categories)} establishment, {f'with the following description: {self.backstory}' if self.backstory else f'Add a backstory containing a {self.traits} history for players to discover'}."
        )
        if self.owner:
            prompt += f" The {self.title} is owned by {self.owner.name}. {self.owner.backstory_summary}"
        results = super().generate(prompt=prompt)
        return results

    def page_data(self):
        result = super().page_data()
        if self.inventory_:
            result |= {
                "items": [{"name": r.name, "pk": str(r.pk)} for r in self.items],
                "inventory": self.inventory,
            }
        return result

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOIOKS                    ##
    ###############################################################

    # def clean(self):
    #     if self.attrs:
    #         self.verify_attr()

    # ################### verify methods ###################
    # def verify_attr(self):
    #     pass
