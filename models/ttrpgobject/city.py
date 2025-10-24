import random

from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    IntAttr,
    StringAttr,
)

from autonomous import log
from models.base.place import Place


class City(Place):
    population = IntAttr(default=100)
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
        self._funcobj["name"] = f"generate_{self.title.lower()}"
        self._funcobj["description"] = f"completes {self.title} data object"
        prompt = f"Generate a fictional {self.genre} {self.title} within the {self.world.name} {self.world.title}. The {self.title} inhabitants are {self.traits}. Write a detailed description appropriate for a {self.title} with a residence of {self.population}."
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
        return [
            a
            for a in self.associations
            if a.model_name() in ["Encounter", "Location", "District"]
        ]

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

    def foundry_export(self):
        source_data = self.page_data()
        """
        Transforms a generic location JSON object into the standard Foundry VTT Scene document schema.

        The descriptive fields are combined into a single JournalEntryPage/Note document,
        as Foundry Scenes do not have a dedicated 'description' field.
        """
        # 1. Define the target schema structure (using a known SWN base template)
        target_schema = {
            "name": "Scene",
            "navigation": True,
            "navOrder": 0,
            "background": {
                "src": None,
                "anchorX": 0,
                "anchorY": 0,
                "offsetX": 0,
                "offsetY": 0,
                "fit": "fill",
                "scaleX": 1,
                "scaleY": 1,
                "rotation": 0,
                "tint": "#ffffff",
                "alphaThreshold": 0,
            },
            "foreground": None,
            "foregroundElevation": None,
            "thumb": None,
            "width": 1792,
            "height": 1792,
            "padding": 0.25,
            "initial": {"x": None, "y": None, "scale": None},
            "backgroundColor": "#999999",
            "grid": {
                "type": 1,
                "size": 100,
                "style": "solidLines",
                "thickness": 1,
                "color": "#000000",
                "alpha": 0.2,
                "distance": 5,
                "units": "ft",
            },
            "tokenVision": True,
            "fog": {
                "exploration": True,
                "overlay": None,
                "colors": {"explored": None, "unexplored": None},
            },
            "environment": {
                "darknessLevel": 0,
                "darknessLock": False,
                "globalLight": {
                    "enabled": False,
                    "alpha": 0.5,
                    "bright": False,
                    "color": None,
                    "coloration": 1,
                    "luminosity": 0,
                    "saturation": 0,
                    "contrast": 0,
                    "shadows": 0,
                    "darkness": {"min": 0, "max": 1},
                },
                "cycle": True,
                "base": {
                    "hue": 0,
                    "intensity": 0,
                    "luminosity": 0,
                    "saturation": 0,
                    "shadows": 0,
                },
                "dark": {
                    "hue": 0.7138888888888889,
                    "intensity": 0,
                    "luminosity": -0.25,
                    "saturation": 0,
                    "shadows": 0,
                },
            },
            "drawings": [],
            "tokens": [],
            "lights": [],
            "notes": [],
            "sounds": [],
            "regions": [],
            "templates": [],
            "tiles": [],
            "walls": [],
            "playlist": None,
            "playlistSound": None,
            "journal": None,
            "journalEntryPage": None,
            "weather": "",
            "folder": None,
            "flags": {},
            "_stats": {},
            "ownership": {"default": 0},
        }

        # 2. Map Core Fields
        scene_name = source_data.get("name", "Unknown Scene").strip()
        target_schema["name"] = scene_name

        # Scene Background Image (maps to background.src)
        # The source is null, so we explicitly set it to null or a default path if needed.
        # Use 'image' for image path
        if url := source_data.get("image", "").strip():
            target_schema["background"]["src"] = (
                f"https://storyteller.stevenamoore.dev{url}"
            )

        # 3. Combine description fields into a Note document
        desc_text = source_data.get("desc", "")
        history_html = source_data.get("history", "")

        # Combine all narratives into a single HTML block
        combined_notes_content = f"""
            <h2>Description</h2>
            <p>{desc_text}</p>
            <h2>History</h2>
            {history_html}
        """

        # Create the embedded Note document structure
        embedded_note = {
            "name": f"{scene_name} Description",
            "text": combined_notes_content.strip(),
            "fontFamily": None,
            "fontSize": 48,
            "textAnchor": 1,
            "textColor": None,
            "x": 0,  # Placeholder coordinates
            "y": 0,  # Placeholder coordinates
            "visibility": 1,  # Visible to GM
            "flags": {},
        }

        # Add the note to the scene's notes array
        target_schema["notes"].append(embedded_note)
        return target_schema

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
