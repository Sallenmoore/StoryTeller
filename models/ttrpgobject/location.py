from autonomous.model.autoattr import (
    StringAttr,
)
from models.base.place import Place


class Location(Place):
    district = StringAttr(default="")
    location_type = StringAttr()

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
            "forest",
            "swamp",
            "mountain",
            "lair",
            "stronghold",
            "tower",
            "palace",
            "temple",
            "fortress",
            "cave",
            "ruins",
            "shop",
            "tavern",
            "sewer",
            "graveyard",
            "shrine",
            "library",
            "academy",
            "workshop",
            "arena",
            "market",
        ]
    )

    parent_list = [
        "Location",
        "District",
        "City",
        "Region",
    ]

    def page_data(self):
        result = super().page_data()
        if self.districts:
            result |= {
                "district": self.districts,
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
