from bs4 import BeautifulSoup

from autonomous import log
from autonomous.model.autoattr import (
    FileAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.images.image import Image
from models.mixins.audio import AudioMixin


class SceneNote(AutoModel, AudioMixin):
    name = StringAttr(default="New Scene")
    num = IntAttr(default=0)
    act = IntAttr()
    scene = IntAttr()
    type = StringAttr(
        choices=[
            "social",
            "encounter",
            "combat",
            "investigation",
            "exploration",
            "stealth",
            "puzzle",
        ]
    )
    next_scenes = ListAttr(ReferenceAttr(choices=["SceneNote"]))
    parent_scene = ReferenceAttr(choices=["SceneNote"])

    notes = StringAttr(default="")
    description = StringAttr(default="")
    scenario = StringAttr(default="")

    setting = ListAttr(ReferenceAttr(choices=["Place"]))
    encounters = ListAttr(ReferenceAttr(choices=["Encounter"]))
    factions = ListAttr(ReferenceAttr(choices=["Faction"]))
    vehicles = ListAttr(ReferenceAttr(choices=["Vehicle"]))
    actors = ListAttr(ReferenceAttr(choices=["Actor"]))
    loot = ListAttr(ReferenceAttr(choices=["Item"]))

    initiative = ListAttr(StringAttr(default=""))

    image = ReferenceAttr(choices=["Image"])
    music = StringAttr(default="")
    audio = FileAttr()

    @property
    def associations(self):
        return [*self.setting, *self.encounters, *self.actors]

    @property
    def audio_text(self):
        return self.description

    @property
    def genre(self):
        if self.actors:
            return self.actors[0].genre
        elif self.setting:
            return self.setting[0].genre
        elif self.encounters:
            return self.encounters[0].genre
        return "Fictional"

    ##################### INSTANCE METHODS ####################
    def delete(self):
        all(e.delete() for e in self.next_scenes)
        return super().delete()

    def add_setting(self, obj):
        if obj not in self.setting:
            self.setting += [obj]
            self.save()
        return obj

    def remove_setting(self, obj):
        self.setting = [s for s in self.setting if s.pk != obj.pk]
        self.save()

    def add_encounter(self, obj):
        if obj not in self.encounters:
            self.encounters += [obj]
            self.save()
        return obj

    def remove_encounter(self, obj):
        self.encounters = [e for e in self.encounters if e.pk != obj.pk]
        self.save()

    def add_loot(self, obj):
        if obj not in self.loot:
            self.loot += [obj]
            self.save()
        return obj

    def remove_loot(self, obj):
        self.loot = [e for e in self.loot if e.pk != obj.pk]
        self.save()

    def add_faction(self, obj):
        if obj not in self.factions:
            self.factions += [obj]
            self.save()
        return obj

    def remove_faction(self, obj):
        self.factions = [e for e in self.factions if e.pk != obj.pk]
        self.save()

    def add_actor(self, obj):
        if obj not in self.actors:
            self.actors += [obj]
            self.save()
        return obj

    def remove_actor(self, obj):
        self.actors = [e for e in self.actors if e.pk != obj.pk]
        self.save()

    def add_vehicle(self, obj):
        if obj not in self.vehicles:
            self.vehicles += [obj]
            self.save()
        return obj

    def remove_vehicle(self, obj):
        self.vehicles = [e for e in self.vehicles if e.pk != obj.pk]
        self.save()

    def generate_image(self):
        if self.image:
            self.image.delete()

        prompt = f"Generate a single comic panel for the following {self.genre} TableTop RPG session scene."

        prompt += "\nDESCRIPTION OF CHARACTERS\n"
        for actor in self.actors:
            prompt += f"""{actor.name} Looks Like: {actor.lookalike}\n
"""

        prompt += """ART STYLE
- In the art style of Jim Lee, with a focus on an active scene composition.
"""

        prompt += f"\nSCENE DESCRIPTION\n\nCreate an image of a scene that consists of {BeautifulSoup(self.description, 'html.parser').get_text()}\n"

        log(prompt, _print=True)
        self.image = Image.generate(prompt=prompt)
        self.image.save()
        self.save()
