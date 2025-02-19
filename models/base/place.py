import markdown
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
    owner = ReferenceAttr(choices=["Character", "Creature", "Faction"])
    map = ReferenceAttr(choices=["Image"])
    maps = ReferenceAttr(choices=["Image"])
    map_prompt = StringAttr(default="")
    dungeon = StringAttr(default="")

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
    def jobs(self):
        jobs = []
        for c in self.characters:
            jobs += c.quests
        for a in self.associations:
            for c in a.characters:
                jobs += c.quests
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

    def generate_dungeon(self):
        primer = f"""As an expert AI tabletop rpg GM assistant, you will assist in creating a encounters, traps, and puzzles in a dungeon for a {self.genre.title()} rpg game in MARKDOWN. You will be given a description of the dungeon, as well as a backstory. You will then generate a list of at least 10 possible enemy encounters, traps, and puzzles that player characters will encounter in the dungeon. Each item should have an explanantion of the encounter, trap, or puzzle, how it can be solved, as well as the outcome if the players fail or succeed.
"""
        prompt = f"""Generate a list of 10 possible enemy encounters, traps, and puzzles in MARKDOWN that player characters will encounter in the dungeon described below and is appropriate to a {self.genre.title()} setting. Each item should have an explanantion of the encounter, trap, or puzzle, how it can be solved, as well as the outcome if the players fail or succeed. The list should be in a bullet list format with the following structure:
---
- Encounter/Trap/Puzzle Name
  - Explanation:
  - Solution:
  - Outcome on Failure:
  - Rewards on Success:
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
