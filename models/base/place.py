import markdown
import validators
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)

from autonomous import log
from models.dungeon.dungeon import Dungeon
from models.images.image import Image
from models.images.map import Map
from models.ttrpgobject.ttrpgobject import TTRPGObject


class Place(TTRPGObject):
    meta = {"abstract": True, "allow_inheritance": True, "strict": False}
    owner = ReferenceAttr(choices=["Character", "Creature", "Faction"])
    map = ReferenceAttr(choices=["Map"])
    map_prompt = StringAttr(default="")
    recent_events = ListAttr(StringAttr(default=""))
    encounters = ListAttr(ReferenceAttr(choices=["Encounter"]))
    location_type = StringAttr(default="")

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

        if self.backstory and self.backstory_summary:
            if not self.map_prompt:
                self.map_prompt = self.system.map_prompt(self)
            # log(map_prompt)
            prompt = f"""{self.map_prompt}

The map has the following features:
- {"\n- ".join(f"{loc.name}:{loc.location_type}" for loc in self.locations if loc in self.children)}

The map should be in a {self.world.map_style} style.
"""
            log(prompt, _print=True)
            map = Map.generate(
                prompt=prompt,
                tags=["map", *self.image_tags],
                aspect_ratio="16:9",
                image_size="4K",
            )
            if self.map and map:
                self.map.delete()
                self.map = map
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

    ################### Crud Methods #####################

    def generate(self, prompt=""):
        # log(f"Generating data with AI for {self.name} ({self})...", _print=True)
        prompt = (
            prompt
            or f"Generate a {self.genre} TTRPG {self.title} with a backstory containing a {self.traits} history for players to slowly unravel."
        )
        if self.owner:
            prompt += f"\n\nThe {self.title} is owned by {self.owner.name}. {self.owner.backstory_summary}"
        if self.location_type:
            prompt += f"\n\nThe {self.title} is a {self.location_type}."
        results = super().generate(prompt=prompt)
        return results

    def delete(self):
        if self.map:
            self.map.delete()
        for encounter in self.encounters:
            encounter.delete()
        return super().delete()

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
        document.pre_save_owner()
        document.pre_save_encounters()

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

        # log(self.map)

    def pre_save_encounters(self):
        for encounter in self.encounters:
            if encounter.parent != self:
                encounter.parent = self
                encounter.save()

    def pre_save_owner(self):
        if isinstance(self.owner, str):
            for a in self.associations:
                if self.owner == str(a.pk):
                    self.owner = a
                    break
