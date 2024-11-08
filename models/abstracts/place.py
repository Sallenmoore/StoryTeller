import validators

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from models.abstracts.ttrpgobject import TTRPGObject
from models.images.image import Image


class Place(TTRPGObject):
    meta = {"abstract": True, "allow_inheritance": True, "strict": False}
    owner = ReferenceAttr(choices=["Character", "Creature"])
    map = ReferenceAttr(choices=["Image"])

    _no_copy = TTRPGObject._no_copy | {
        "owner": None,
    }
    _possible_events = [
        "Established",
        *TTRPGObject._possible_events,
        "Abandoned",
    ]
    _traits_list = [
        "long hidden",
        "mysterious",
        "sinister",
        "underground",
        "frozen",
        "jungle",
        "dangerous",
        "boring",
        "mundane",
        "opulent",
        "decaying",
        "haunted",
        "enchanted",
        "cursed",
    ]

    ################### Property Methods #####################
    @property
    def actors(self):
        return [*self.characters, *self.creatures]

    @property
    def map_thumbnail(self):
        return self.map.image.url(100)

    @property
    def map_prompt(self):
        return self.system.map_prompt(self)

    ################### Instance Methods #####################

    # MARK: generate_map
    def generate_map(self):
        log(f"Generating Map with AI for {self.name} ({self})...", _print=True)
        if self.backstory and self.backstory_summary:
            map_prompt = self.map_prompt
            log(map_prompt)
            self.map = Image.generate(
                prompt=map_prompt,
                tags=["map", *self.image_tags],
                img_quality="hd",
                img_size="1792x1024",
            )
            self.map.save()
            self.save()
        else:
            raise AttributeError(
                "Object must have a backstory and description to generate a map"
            )
        return self.map

    def get_map_list(self):
        images = []
        for img in Image.all():
            # log(img.asset_id)
            if all(t in img.tags for t in ["map", self.genre]):
                log(img)
                images.append(img)
        return images

    ################### Crud Methods #####################

    def generate(self, prompt=""):
        log(f"Generating data with AI for {self.name} ({self})...", _print=True)
        prompt = (
            prompt
            or f"Generate a {self.genre} TTRPG {self.title} with a backstory containing a {self.traits} history for players to slowly unravel."
        )
        if self.owner:
            prompt += f" The {self.title} is owned by {self.owner.name}. {self.owner.backstory_summary}"
        results = super().generate(prompt=prompt)
        return results

    def page_data(self):
        return {
            "pk": str(self.pk),
            "name": self.name,
            "start_date": self.start_date.datestr() if self.start_date else "Unknown",
            "end_date": self.end_date.datestr() if self.end_date else "Unknown",
            "backstory": self.backstory,
            "history": self.history,
            "owner": {"name": self.owner.name, "pk": str(self.owner.pk)}
            if self.owner
            else "Unknown",
            "encounters": [{"name": r.name, "pk": str(r.pk)} for r in self.encounters],
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
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_map()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################

    def pre_save_map(self):
        log(self.map)
        if isinstance(self.map, str):
            if not self.map:
                self.map = None
            elif validators.url(self.map):
                self.map = Image.from_url(
                    self.map, prompt=self.map_prompt, tags=["map", *self.image_tags]
                )
                self.map.save()
            elif map := Image.get(self.map):
                self.map = map
            else:
                log(self.map, type(self.map))
                raise ValidationError(
                    f"Map must be an Image object, url, or Image pk, not {self.map}"
                )
        elif not self.map:
            for a in self.geneology:
                if a.map:
                    self.map = a.map
        elif not self.map.tags:
            self.map.tags = ["map", *self.image_tags]
            self.map.save()
        log(self.map)


class Scene(Place):
    meta = {"abstract": True, "allow_inheritance": True, "strict": False}
    location_type = StringAttr()
    scenes = ListAttr(ReferenceAttr(choices=["Location", "POI"]))
    grid = StringAttr()
    grid_color = StringAttr()
    grid_size = IntAttr()
    fow = StringAttr()
    current_encounter = ReferenceAttr(choices=["Encounter"])
    current_actor = ReferenceAttr(choices=["Actor"])
    current_item = ReferenceAttr(choices=["Item"])
    music = StringAttr()

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
                "notes": {
                    "type": "array",
                    "description": "At least 5 short descriptions of potential items that can be found in the location, ranging from mundane to wonderous, as well as what is required to find them.",
                    "items": {"type": "string"},
                },
            },
        },
    }

    ################### Property Methods #####################
    @property
    def image_tags(self):
        return super().image_tags + [self.location_type]

    @property
    def image_prompt(self):
        return f"A full color hi-res image of a point of interest or landmark in a {self.genre} TTRPG with the following description: {self.desc}"

    ################ Instance Methods ####################

    def has_scene(self, obj):
        return any(d.pk == obj.pk for d in self.scenes)

    def add_scene(self, connect_obj):
        if not any(d.pk == connect_obj.pk for d in self.scenes):
            # log(f"Connecting scene: {self.name} -> {connect_obj.name}")
            self.scenes.append(connect_obj)
            self.save()
        if not any(d.pk == self.pk for d in connect_obj.scenes):
            # log(f"Connecting scene: {connect_obj.name} -> {self.name}")
            connect_obj.scenes.append(self)
            connect_obj.save()

    def update_scene(self, grid=None, show=None, music=None, fow=None):
        self.grid = self.grid if grid is None else grid
        self.show = self.show if show is None else show
        self.music = self.music if music is None else music
        self.fow = self.fow if fow is None else fow
        self.save()

    def get_scene_events(self):
        if self.start_date and self.start_date not in self.events:
            self.events += [self.start_date]
        if self.end_date and self.end_date not in self.events:
            self.events += [self.end_date]
        events = self.events[:]
        subevents = [
            *self.encounters,
            *self.characters,
            *self.creatures,
            *self.items,
            *self.factions,
        ]
        for o in subevents:
            events += o.events
        events.sort()
        return events

    def remove_scene(self, scene):
        try:
            self.scenes.remove(scene)
            self.save()
        except Exception as e:
            log(f"Error Removing Scene: {scene.pk} -- {e}")
        return self

    def label(self, model):
        if not isinstance(model, str):
            model = model.__name__
        if model == "Character":
            return "Residents"
        if model == "Item":
            return "Inventory"
        return super().label(model)

    def page_data(self):
        return super().page_data() | {
            "location_type": self.location_type,
        }

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################
    @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     super().auto_post_init(sender, document, **kwargs)
    # document.post_init_map()

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_current_encounter()
        document.pre_save_current_actor()
        document.pre_save_current_item()
        document.pre_save_music()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################

    def post_init_map(self):
        if not self.map and self.parent and self.parent.map:
            self.map = self.parent.map
        else:
            self.map = self.world.map

    def pre_save_current_encounter(self):
        if not self.current_encounter and self.encounters:
            self.current_encounter = self.encounters[0]

    def pre_save_music(self):
        if not self.music:
            self.music = "/static/sounds/music/themesong.mp3"

    def pre_save_current_actor(self):
        if not self.current_actor and self.actors:
            self.current_actor = self.actors[0]

    def pre_save_current_item(self):
        if not self.current_item and self.items:
            self.current_item = self.items[0]
