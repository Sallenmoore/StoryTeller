import io
import random

import requests
from bs4 import BeautifulSoup
from PIL import Image as ImageTools

from autonomous import log
from autonomous.ai.imageagent import ImageAgent
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel

from .image import Image


class Coordinates(AutoModel):
    x = StringAttr(default="")
    y = StringAttr(default="")
    obj = ReferenceAttr(choices=["TTRPGObject"])


class Map(Image):
    coordinates = ListAttr(ReferenceAttr(choices=[Coordinates]))

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
        coord = Coordinates(
            x=-1,
            y=-1,
            obj=poi,
        )
        coord.save()
        self.coordinates += [coord]
        self.save()
