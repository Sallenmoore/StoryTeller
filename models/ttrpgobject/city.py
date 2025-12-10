import random

from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    IntAttr,
    StringAttr,
)

from autonomous import log
from models.base.place import Place


class City(Place):
    population = IntAttr(default=-1)
    culture = StringAttr(default="")
    religion = StringAttr(default="")
    government = StringAttr(default="")

    parent_list = ["Region"]

    _funcobj = {
        "name": "generate_city",
        "description": "completes City data object",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A unique and evocative name",
                },
                "status": {
                    "type": "string",
                    "description": "current, immediate situation the city is in, such as thriving, in decline, recovering from a disaster, etc.",
                },
                "population": {
                    "type": "integer",
                    "description": "The population between 50 and 500000, with more weight on smaller populations",
                },
                "backstory": {
                    "type": "string",
                    "description": "A short history in 750 words or less. Only include publicly known information about the city.",
                },
                "desc": {
                    "type": "string",
                    "description": "A short physical description that will be used to generate an image.",
                },
                "culture": {
                    "type": "string",
                    "description": "A brief description of the culture and its people. Only include publicly known information.",
                },
                "government": {
                    "type": "string",
                    "description": "A brief description of the government. Only include publicly known information.",
                },
                "religion": {
                    "type": "string",
                    "description": "A brief description of the religions and its people. Only include publicly known information.",
                },
                "sensory_details": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of sensory details, such as sight, sound, smell, and touch, that a GM can use to bring the city to life",
                },
                "recent_events": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A concise list of significant events that have recently occurred in this city, even if they aren't ongoing situations. Only include publicly known information.",
                },
            },
        },
    }

    ################### Class Methods #####################

    def generate(self):
        self._funcobj["name"] = f"generate_{self.title.lower()}"
        self._funcobj["description"] = f"completes the {self.title} data object"
        prompt = f"""Generate a fictional {self.genre} {self.title} within the {self.world.name} {self.world.title}. The {self.title} inhabitants are {self.traits}. Write a detailed description appropriate for a {self.title}, and incorporate and emblellish on the following details into the description:
{f"- BACKSTORY: {self.backstory}" if self.backstory else ""}
{f"- DESCRIPTION: {self.desc}" if self.desc else ""}
{f"- POPULATION: {self.population}"}
{f"- CULTURE: {self.parent.culture}" if self.parent and self.parent.culture else ""}
{f"- RELIGION: {self.parent.religion}" if self.parent and self.parent.religion else ""}
{f"- GOVERNMENT: {self.parent.government}" if self.parent and self.parent.government else ""}
"""
        obj_data = super().generate(prompt=prompt)
        self.save()
        return obj_data

    ################### INSTANCE PROPERTIES #####################

    @property
    def image_prompt(self):
        msg = f"""
        Create a full color, high resolution illustrated view of a {self.title} called {self.name} with the following details:
        - POPULATION: {self.population}
        - DESCRIPTION: {self.desc}
        """
        return msg

    @property
    def map_pois(self):
        return [a for a in self.children if a.model_name() in ["Location", "District"]]

    @property
    def ruler(self):
        return self.owner

    @property
    def size(self):
        log("TODO: this is deprecated, remove")
        return ""

    ####################### Instance Methods #######################

    def label(self, model):
        if not isinstance(model, str):
            model = model.__name__
        if model == "Character":
            return "Citizens"
        return super().label(model)

    def page_data(self):
        return super().page_data() | {
            "name": self.name,
            "desc": self.description,
            "backstory": self.backstory,
            "history": self.history,
            "population": self.population,
            "image": str(self.map.url()) if self.map else "",
            "culture": self.culture,
            "religion": self.religion,
            "government": self.government,
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
        if self.population < 0:
            pop_list = list(
                range(0, random.randint(512, 1000000), random.randint(23, 5713))
            )
            pop_weights = [i + 1 for i in range(len(pop_list), 0, -1)]
            self.population = random.choice(random.choices(pop_list, pop_weights))
