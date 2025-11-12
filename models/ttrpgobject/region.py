from autonomous.model.autoattr import (
    StringAttr,
)

from autonomous import log
from models.base.place import Place
from models.ttrpgobject.faction import Faction


class Region(Place):
    culture = StringAttr(default="")
    religion = StringAttr(default="")
    government = StringAttr(default="")

    parent_list = ["World"]

    _funcobj = {
        "name": "generate_region",
        "description": "creates Region data object",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A unique and evocative name for the region",
                },
                "status": {
                    "type": "string",
                    "description": "current, immediate situation the region is in, such as thriving, in decline, recovering from a disaster, etc.",
                },
                "desc": {
                    "type": "string",
                    "description": "A brief physical description that will be used to generate an image of the region",
                },
                "backstory": {
                    "type": "string",
                    "description": "A brief history of the region and its people. Only include publicly known information.",
                },
                "culture": {
                    "type": "string",
                    "description": "A brief description of the culture of the region and its people. Only include publicly known information.",
                },
                "government": {
                    "type": "string",
                    "description": "A brief description of the government of the region. Only include publicly known information.",
                },
                "religion": {
                    "type": "string",
                    "description": "A brief description of the religions of the region and its people. Only include publicly known information.",
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

    ################### Property Methods #####################

    @property
    def image_prompt(self):
        prompt = f"An aerial top-down map illustration of the {self.name} {self.title}. A {self.traits} {self.title} with the following description: {self.desc}."
        if self.cities:
            cities = "\n- ".join([c.name for c in self.cities])
            prompt += f"The region contains the following cities: {cities}."
        return prompt

    @property
    def map_pois(self):
        return [
            a
            for a in self.associations
            if a.model_name() in ["Location", "City", "District"]
        ]

    @property
    def ruling_faction(self):
        return self.owner

    @ruling_faction.setter
    def ruling_faction(self, value):
        self.owner = value

    ################### Crud Methods #####################
    def generate(self):
        prompt = f"Generate a detailed information for a {self.genre} {self.title}. The {self.title} is primarily {self.traits}. The {self.title} should also contain a story thread for players to slowly uncover. The story thread should be connected to 1 or more additional elements in the existing world as described by the uploaded file."
        results = super().generate(prompt=prompt)
        return results

    ################### Instance Methods #####################

    def page_data(self):
        return {
            "pk": str(self.pk),
            "image": str(self.map.url()) if self.map else None,
            "name": self.name,
            "desc": self.description,
            "backstory": self.backstory,
            "history": self.history,
            "culture": self.culture,
            "government": self.government,
            "religion": self.religion,
        }

    # def foundry_export(self):
    #     source_data = self.page_data()

    #     return source_data

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
        document.pre_save_owner()

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)
        document.post_save_backstory()

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################

    def pre_save_owner(self):
        if isinstance(self.owner, str):
            if faction := Faction.get(self.owner):
                self.owner = faction
            else:
                raise ValueError(f"Faction {self.owner} not found")

    def post_save_backstory(self):
        if not self.backstory:
            story = ""
            for a in [*self.cities, *self.locations]:
                if a.backstory:
                    story += f"""
                    <h3>{a.name}</h3>
                    <div> {a.history or a.backstory} </div>
                    """
            self.backstory = (
                f"The {self.title} is home to the following: \n\n {story}"
                if story
                else ""
            )
