import validators

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    ReferenceAttr,
    StringAttr,
)
from models.images.image import Image
from models.ttrpgobject.ttrpgobject import TTRPGObject


class Place(TTRPGObject):
    meta = {"abstract": True, "allow_inheritance": True, "strict": False}
    owner = ReferenceAttr(choices=["Character", "Creature"])
    map = ReferenceAttr(choices=["Image"])
    maps = ReferenceAttr(choices=["Image"])
    map_prompt = StringAttr(default="")

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

    ################### Instance Methods #####################

    # MARK: generate_map
    def generate_map(self):
        # log(f"Generating Map with AI for {self.name} ({self})...", _print=True)
        if self.backstory and self.backstory_summary:
            map_prompt = self.map_prompt or self.system.map_prompt(self)
            # log(map_prompt)
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
                # log(img)
                images.append(img)
        return images

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
                # log(self.map, type(self.map))
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
        # log(self.map)
