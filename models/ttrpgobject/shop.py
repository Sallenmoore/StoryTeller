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
                "status": {
                    "type": "string",
                    "description": "current, immediate situation the shop is in, such as thriving, in decline, out of stock, etc.",
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
        return self.inventory_ + [f"{i.name}: {i.description}" for i in self.items]

    @inventory.setter
    def inventory(self, value):
        self.inventory_ = value

    def generate(self, prompt=""):
        # log(f"Generating data with AI for {self.name} ({self})...", _print=True)
        prompt = f"""
{f"INVENTORY: {self.inventory}" if self.inventory else ""}
"""
        results = super().generate(prompt=prompt)
        return results

    def page_data(self):
        return {
            "pk": str(self.pk),
            "image": str(self.map.url()) if self.map else None,
            "name": self.name,
            "desc": self.description,
            "backstory": self.backstory,
            "history": self.history,
            "inventory": self.inventory,
        }

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
