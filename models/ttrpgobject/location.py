from autonomous.model.autoattr import (
    ReferenceAttr,
    StringAttr,
)

from autonomous import log
from models.base.place import Place
from models.ttrpgobject.character import Character


class Location(Place):
    location_type = StringAttr(default="")
    dungeon = ReferenceAttr(choices=["Dungeon"])

    parent_list = [
        "Location",
        "District",
        "City",
        "Region",
        "Vehicle",
    ]

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
                    "description": "current, immediate situation the location is in, such as thriving, in decline, recovering from a disaster, etc.",
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

    def generate(self, prompt=""):
        # log(f"Generating data with AI for {self.name} ({self})...", _print=True)
        prompt = f"Generate a {self.genre} TTRPG {self.location_type} {f'with the following description: {self.backstory}' if self.backstory else f'Generate a backstory containing a history for players to discover that follow the theme: {self.traits}'}. {prompt}"

        if self.parent and self.parent.model_name() in [
            "City",
            "Region",
        ]:
            prompt += f"""
{f"- CULTURE: {self.parent.culture}" if self.parent and self.parent.culture else ""}
{f"- RELIGION: {self.parent.religion}" if self.parent and self.parent.religion else ""}
{f"- GOVERNMENT: {self.parent.government}" if self.parent and self.parent.government else ""}
"""

        if self.owner:
            prompt += (
                f" The {self.title} is owned by {self.owner.name}. {self.owner.history}"
            )
        results = super().generate(prompt=prompt)
        return results

    def delete(self):
        if self.dungeon and not isinstance(self.dungeon, str):
            self.dungeon.delete()
        return super().delete()

    def page_data(self):
        return {
            "pk": str(self.pk),
            "image": str(self.map.url()) if self.map else None,
            "name": self.name,
            "desc": self.description,
            "type": self.location_type,
            "backstory": self.backstory,
            "history": self.history,
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
        ##### MIGRATION: old dungeon str to reference #####
        log(document.dungeon)
        if isinstance(document.dungeon, str):
            document.dungeon = None

        super().auto_pre_save(sender, document, **kwargs)

        document.pre_save_owner()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################

    def pre_save_owner(self):
        if self.owner and not isinstance(self.owner, Character):
            self.owner = Character.get(self.owner)

        # log(self.features, _print=True)
