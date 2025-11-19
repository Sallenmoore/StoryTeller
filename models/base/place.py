import markdown
import validators
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)

from autonomous import log
from models.images.image import Image
from models.images.map import Map
from models.ttrpgobject.ttrpgobject import TTRPGObject


class Place(TTRPGObject):
    meta = {"abstract": True, "allow_inheritance": True, "strict": False}
    owner = ReferenceAttr(choices=["Character", "Creature", "Faction"])
    map = ReferenceAttr(choices=["Image"])
    map_prompt = StringAttr(default="")
    dungeon = StringAttr(default="")
    sensory_details = ListAttr(StringAttr(default=""))
    recent_events = ListAttr(StringAttr(default=""))
    encounters = ListAttr(ReferenceAttr(choices=["Encounter"]))

    ################### Property Methods #####################
    @property
    def actors(self):
        return [*self.characters, *self.creatures]

    @property
    def jobs(self):
        jobs = []
        associations = self.associations[:]
        for a in associations:
            if a.model_name() == "Character":
                jobs += a.quests
            for c in a.associations:
                if c not in associations and c.parent == a.parent:
                    associations += [c]
        jobs = list(set(jobs))
        return jobs

    @property
    def map_thumbnail(self):
        return self.map.image.url(100)

    ################### Instance Methods #####################

    # MARK: generate_map
    def generate_map(self):
        # log(f"Generating Map with AI for {self.name} ({self})...", _print=True)
        if self.map and self in self.map.associations:
            if len(self.map.associations) <= 1:
                self.map.delete()
            else:
                self.map.associations.remove(self)
                self.map.save()
        if self.backstory and self.backstory_summary:
            if not self.map_prompt:
                self.map_prompt = self.system.map_prompt(self)
            # log(map_prompt)
            self.map = Map.generate(
                prompt=self.map_prompt,
                tags=["map", *self.image_tags],
                aspect_ratio="16:9",
                image_size="4K",
            )
            self.map.save()
            self.save()
        else:
            raise AttributeError(
                "Object must have a backstory and description to generate a map"
            )
        return self.map

    def get_map_list(self):
        maps = []
        for img in Map.all():
            # log(img.asset_id)
            if all(
                t in img.tags for t in ["map", self.model_name().lower(), self.genre]
            ):
                maps.append(img)
        return maps

    def generate_dungeon(self):
        primer = f"""As an expert AI tabletop RPG GM assistant, you will assist in creating a encounters, traps, and puzzles in a location for a {self.genre.title()} rpg game in MARKDOWN. You will be given a description of the location, as well as a backstory. You will then generate a list of at least 10 possible enemy encounters, traps, or puzzles that player characters will encounter in the location. Each item should have an explanation of the encounter, trap, or puzzle, any associated mechanics, as well as the outcome if the players fail or succeed.
"""
        prompt = f"""Generate a list of 10 possible enemy encounters, traps, or puzzles in MARKDOWN that player characters will encounter in the location described below and is appropriate to a {self.genre.title()} setting. Each item should have a detailed explanation of the scenario, specific game mechanics for how to interact with the scenario, as well as the specific details of the outcome if the players fail or succeed. The list should use the following structure:
---
### Encounter/Trap/Puzzle Name
- Explanation:
- Mechanics:
- on Failure:
- on Success:
---

DUNGEON DESCRIPTION

{self.description}

DUNGEON BACKSTORY

{self.backstory}
"""
        self.dungeon = self.system.generate_text(prompt, primer)
        self.dungeon = self.dungeon.replace("```markdown", "").replace("```", "")
        self.dungeon = (
            markdown.markdown(self.dungeon).replace("h1>", "h3>").replace("h2>", "h3>")
        )
        self.save()

    ################### Crud Methods #####################

    def generate(self, prompt=""):
        # log(f"Generating data with AI for {self.name} ({self})...", _print=True)
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
            "image_pk": str(self.image.pk) if self.image else None,
            "map_pk": str(self.map.pk) if self.map else None,
            "name": self.name,
            "backstory": self.backstory,
            "history": self.history,
            "owner": {"name": self.owner.name, "pk": str(self.owner.pk)}
            if self.owner
            else "Unknown",
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
        document.pre_save_enconters()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################

    def pre_save_map(self):
        # log(self.map)
        if not self.map_prompt:
            self.map_prompt = self.system.map_prompt(self)

        if isinstance(self.map, str):
            if validators.url(self.map):
                self.map = Map.from_url(
                    self.map,
                    prompt=self.map_prompt,
                    tags=["map", *self.image_tags],
                )
                self.map.save()
            elif image := Map.get(self.map):
                self.map = image
            elif image := Image.get(self.map):
                self.map = Map.from_image(image)
                self.map.save()
            else:
                raise ValidationError(
                    f"Image must be an Image object, url, or Map pk, not {self.map}"
                )
        elif type(self.map) is not Map and type(self.map) is Image:
            log("converting to map...", self.map, _print=True)
            self.map = Map.from_image(self.map)
            self.map.save()
            log("converted to map", self.map, _print=True)

        if self.map and not self.map.tags:
            self.map.tags = [*self.image_tags, "map"]
            self.map.save()

        if self.map and self not in self.map.associations:
            self.map.associations += [self]
            self.map.save()

        # log(self.map)

    def pre_save_enconters(self):
        self.encounters = list(set(self.encounters))
        for encounter in set(self.encounters):
            if not encounter.parent:
                encounter.parent = self.parent
            elif encounter.parent != self.parent and encounter in self.encounters:
                self.encounters.remove(encounter)
