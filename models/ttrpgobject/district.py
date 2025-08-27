import random

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from models.base.place import Place


class District(Place):
    parent_list = ["City", "Region"]
    _funcobj = {
        "name": "generate_district",
        "description": "completes District data object",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A unique and evocative name for the district",
                },
                "backstory": {
                    "type": "string",
                    "description": "A short history of the district in 750 words or less. Only include publicly known information about the district.",
                },
                "desc": {
                    "type": "string",
                    "description": "A short physical description that will be used to generate an image of the district.",
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

    ################### Class Methods #####################

    def generate(self):
        parent_str = (
            f" located in the {self.parent.title}, {self.parent.name}"
            if self.parent
            else ""
        )
        prompt = f"Generate a fictional {self.genre} {self.title} within the {self.world.name} {self.world.title} universe. Write a detailed description appropriate for a {self.title}{parent_str}. The {self.title} should contain up to 3 {random.choice(['mysterious', 'sinister', 'boring'])} secrets hidden within the {self.title} for the players to discover."
        obj_data = super().generate(prompt=prompt)
        self.save()
        return obj_data

    ################### INSTANCE PROPERTIES #####################

    @property
    def image_prompt(self):
        msg = f"""
        Create a full color, high resolution illustrated view of a {self.genre} {self.title} called {self.name} with the following details:
        - DESCRIPTION: {self.description}
        """
        return msg

    @property
    def map_pois(self):
        return [
            a for a in self.associations if a.model_name() in ["Encounter", "Location"]
        ]

    @property
    def ruler(self):
        return self.owner

    ####################### Instance Methods #######################

    def page_data(self):
        return super().page_data() | {
            "locations": [{"name": r.name, "pk": str(r.pk)} for r in self.locations],
            "encounters": [{"name": r.name, "pk": str(r.pk)} for r in self.encounters],
            "factions": [{"name": r.name, "pk": str(r.pk)} for r in self.factions],
        }

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    # @classmethod
    # def auto_pre_save(cls, sender, document, **kwargs):
    #     super().auto_pre_save(sender, document, **kwargs)

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################
