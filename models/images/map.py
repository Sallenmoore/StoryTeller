import io
import random

import requests
from autonomous.ai.imageagent import ImageAgent
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from bs4 import BeautifulSoup
from PIL import Image as ImageTools

from autonomous import log

from .image import Image


class Coordinates(AutoModel):
    x = StringAttr(default="")
    y = StringAttr(default="")
    obj = ReferenceAttr(choices=["TTRPGObject"])


class Map(Image):
    coordinates = ListAttr(ReferenceAttr(choices=[Coordinates]))
    associations = ListAttr(
        ReferenceAttr(
            choices=[
                "TTRPGBase",
                "Story",
                "Event",
                "Episode",
                "Encounter",
                "DungeonRoom",
            ]
        )
    )

    @classmethod
    def generate(cls, prompt, **kwargs):
        return super().generate(prompt, **kwargs)

    @classmethod
    def from_image(self, image):
        """
        Takes an image and generates a map from it.
        """
        # Check if the image is a map
        if type(image) is not Image:
            raise ValueError("Image must be an instance of Image class.")
        # Check if the image is a map
        # Generate a map from the image
        map_obj = Map(
            prompt=image.prompt,
            tags=image.tags,
            associations=image.associations,
        )
        map_obj.data.put(image.data.read(), content_type="image/webp")
        return map_obj

    def add_poi(self, poi):
        """
        Adds a point of interest to the map.
        """
        if not any(c for c in self.coordinates if c.obj == poi):
            coord = Coordinates(
                x="-1",
                y="-1",
                obj=poi,
            )
            coord.save()
            self.coordinates += [coord]
            self.save()

    def update_poi(self, poi, lat, lng):
        """
        Adds a point of interest to the map.
        """
        for coord in self.coordinates:
            if coord.obj == poi:
                coord.x = str(lat)
                coord.y = str(lng)
                coord.save()
                break

    def in_coordinates(self, poi):
        """
        Returns the coordinates of a point of interest.
        """
        for coord in self.coordinates:
            if coord.obj == poi:
                return True
        return False
