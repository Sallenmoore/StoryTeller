from autonomous import log
from autonomous.model.autoattr import (
    ReferenceAttr,
)
from models.base.place import Place
from models.ttrpgobject.faction import Faction


class Region(Place):
    ruling_faction = ReferenceAttr(choices=[Faction])

    parent_list = ["World"]
    _traits_list = [
        "coastal",
        "mountainous",
        "desert",
        "forest",
        "jungle",
        "plains",
        "swamp",
        "frozen",
        "underground",
    ]
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
                "desc": {
                    "type": "string",
                    "description": "A brief physical description that will be used to generate an image of the region",
                },
                "backstory": {
                    "type": "string",
                    "description": "A brief history of the region and its people. Only include publicly known information.",
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
    def map_prompt(self):
        prompt = (
            super().map_prompt
            + f"""
        With the following landmarks:
        - {self.get_title('City')}: {", ".join([c.name for c in self.cities])}
        - {self.get_title('Location')}: {", ".join([l.name for l in self.locations])}
        """
        )
        return prompt

    ################### Crud Methods #####################
    def generate(self):
        prompt = f"Generate a detailed information for a {self.genre} {self.title}. The {self.title} is primarily {self.traits}. The {self.title} should also contain a story thread for players to slowly uncover. The story thread should be connected to 1 or more additional elements in the existing world as described by the uploaded file."
        results = super().generate(prompt=prompt)
        return results

    ################### Instance Methods #####################

    def page_data(self):
        return {
            "pk": str(self.pk),
            "name": self.name,
            "desc": self.desc,
            "backstory": self.backstory,
            "history": self.history,
            "cities": [{"name": r.name, "pk": str(r.pk)} for r in self.cities],
            "locations": [{"name": r.name, "pk": str(r.pk)} for r in self.locations],
            "factions": [{"name": r.name, "pk": str(r.pk)} for r in self.factions],
        }

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

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)
        document.post_save_backstory()

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################
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
