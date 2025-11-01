from autonomous.model.autoattr import (
    StringAttr,
)

from models.base.place import Place


class Location(Place):
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
            prompt += (
                f" The {self.title} is owned by {self.owner.name}. {self.owner.history}"
            )
        results = super().generate(prompt=prompt)
        return results

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
            <h2>Description and Backstory</h2>
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
    ##                    VERIFICATION HOIOKS                    ##
    ###############################################################

    # def clean(self):
    #     if self.attrs:
    #         self.verify_attr()

    # ################### verify methods ###################
    # def verify_attr(self):
    #     pass
