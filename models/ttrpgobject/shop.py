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
                    "description": "The type of location",
                },
                "backstory": {
                    "type": "string",
                    "description": "A description of the history of the location. Only include what would be publicly known information.",
                },
                "desc": {
                    "type": "string",
                    "description": "A short physical description that will be used to generate an evocative image of the location",
                },
            },
        },
    }

    categories = sorted(
        [
            "shop",
            "tavern",
            "market",
        ]
    )

    parent_list = [
        "Location",
        "District",
        "City",
    ]

    @property
    def inventory(self):
        return self.inventory_ + self.items

    def generate(self, prompt=""):
        # log(f"Generating data with AI for {self.name} ({self})...", _print=True)
        prompt = (
            prompt
            or f"Generate a {self.genre} TTRPG establishment, such as a shop or tavern, {f'with the following description: {self.backstory}' if self.backstory else ''}. Add a backstory containing a {self.traits} history for players to discover."
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
                "inventory": self.inventory_,
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
