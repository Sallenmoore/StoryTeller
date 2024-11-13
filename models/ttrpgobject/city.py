import random

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    IntAttr,
    ListAttr,
    ReferenceAttr,
)
from models.base.place import Place


class City(Place):
    population = IntAttr(default=100)
    districts = ListAttr(ReferenceAttr(choices=["District"]))

    parent_list = ["Region"]
    _traits_list = [
        "bohemian",
        "rude",
        "aggressive",
        "proud",
        "distrustful",
        "anarchic",
        "aristocratic",
        "bureaucratic",
        "theocratic",
        "tribalist",
    ]
    _funcobj = {
        "name": "generate_city",
        "description": "completes City data object",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A unique and evocative name for the city",
                },
                "population": {
                    "type": "integer",
                    "description": "The city's population between 50 and 50000, with more weight on smaller populations",
                },
                "backstory": {
                    "type": "string",
                    "description": "A short history of the city in 750 words or less. Only include publicly known information about the city.",
                },
                "desc": {
                    "type": "string",
                    "description": "A short physical description that will be used to generate an image of the city.",
                },
                "districts": {
                    "type": "array",
                    "description": "The names of at least 3 districts in the city, named consistent with the city's theme.",
                    "items": {"type": "string"},
                },
            },
        },
    }

    ################### Class Methods #####################

    def generate(self):
        prompt = f"Generate a fictional {self.genre} {self.title} within the {self.world.name} {self.world.title}. The {self.title} inhabitants are {self.traits}. Write a detailed description appropriate for a {self.title} with a residence of {self.population}."
        obj_data = super().generate(prompt=prompt)
        self.save()
        return obj_data

    ################### INSTANCE PROPERTIES #####################

    @property
    def image_prompt(self):
        msg = f"""
        Create a full color, high resolution illustrated view of a {self.title} called {self.name} of with the following details:
        - POPULATION: {self.population}
        - DESCRIPTION: {self.desc}
        """
        return msg

    @property
    def ruler(self):
        return self.owner

    @property
    def size(self):
        if self.population < 100:
            return "settlement"
        elif self.population < 1000:
            return "village"
        elif self.population < 10000:
            return "town"
        else:
            return "city"

    ####################### Instance Methods #######################

    def label(self, model):
        if not isinstance(model, str):
            model = model.__name__
        if model == "Character":
            return "Citizens"
        return super().label(model)

    def page_data(self):
        return super().page_data() | {
            "population": self.population,
            "districts": self.districts,
            "pois": [{"name": r.name, "pk": str(r.pk)} for r in self.pois],
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

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_population()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################

    def pre_save_population(self):
        if not self.population:
            pop_list = list(range(20, 20000, 23))
            pop_weights = [i + 1 for i in range(len(pop_list), 0, -1)]
            self.population = random.choices(pop_list, pop_weights)[0]
