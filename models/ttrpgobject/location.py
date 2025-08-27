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
                "sensory_details": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of short sensory details, such as sight, sound, smell, and touch, that a GM can use to bring the location to life",
                },
                "recent_events": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A concise list of significant events that have recently occurred in this location, even if they aren't ongoing situations. Only include publicly known information.",
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
        "Vehicle",
    ]

    def generate(self, prompt=""):
        # log(f"Generating data with AI for {self.name} ({self})...", _print=True)
        prompt = (
            prompt
            or f"Generate a {self.genre} TTRPG {self.location_type} {f'with the following description: {self.backstory}' if self.backstory else ''}. Add a backstory containing a {self.traits} history for players to discover."
        )
        if self.owner:
            prompt += f" The {self.title} is owned by {self.owner.name}. {self.owner.backstory_summary}"
        results = super().generate(prompt=prompt)
        return results

    def page_data(self):
        result = super().page_data()
        if self.districts:
            result |= {
                "districts": [
                    {"name": r.name, "pk": str(r.pk)} for r in self.districts
                ],
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
