import io
import os
import random
import urllib
from base64 import b64decode

import requests
from bs4 import BeautifulSoup
from PIL import Image as ImageTools

from autonomous import log
from autonomous.ai.imageagent import ImageAgent
from autonomous.model.autoattr import (
    FileAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel


class Image(AutoModel):
    # meta = {"collection": "Image"}
    data = FileAttr(default="")
    prompt = StringAttr(default="")
    tags = ListAttr(StringAttr(default=""))

    ################### Class Variables #####################
    _client = ImageAgent()

    _sizes = {"thumbnail": 100, "small": 300, "medium": 600, "large": 1000}

    ################### Class Methods #####################

    @classmethod
    def generate(
        cls,
        prompt: str,
        tags=[],
        img_quality="standard",
        img_size="1024x1024",
        text=False,
    ):
        prompt = BeautifulSoup(prompt, "html.parser").get_text()
        log(f"=== generation prompt ===\n\n{prompt}")
        temp_prompt = (
            f"""{prompt}
IMPORTANT: The image MUST NOT contain any TEXT.
"""
            or prompt
        )
        try:
            image = cls._client.generate(
                prompt=temp_prompt,
            )
        except Exception as e:
            log(f"==== Error: Unable to create image ====\n\n{e}")
            return None
        else:
            image_obj = Image(
                prompt=prompt,
                tags=tags,
            )
            image_obj.data.put(io.BytesIO(image), content_type="image/webp")
            image_obj.save()
        return image_obj

    @classmethod
    def get_image_list(cls, max=10, tags=None):
        image_list = cls.all()
        if tags:
            image_list = [i for i in image_list if all(tag in i.tags for tag in tags)]
        if image_list:
            image_list = random.sample(image_list, k=min(len(image_list), max))
        # [log(i) for i in image_list]
        return image_list

    @classmethod
    def from_url(cls, url, prompt="", tags=None):
        tags = tags if tags else []
        try:
            response = requests.get(url)
            response.raise_for_status()
            if not response.headers["Content-Type"].startswith("image/"):
                raise ValueError("URL does not point to a valid image.")
            with ImageTools.open(io.BytesIO(response.content)) as img:
                width, height = img.size
                if width != height:
                    max_size = min(width, height)
                    img = img.crop(
                        (
                            (width - max_size) / 2,
                            (height - max_size) / 2,
                            (width + max_size) / 2,
                            (height + max_size) / 2,
                        )
                    )
                img = img.copy()
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="WEBP")
                image_obj = Image(
                    prompt=prompt,
                    tags=tags,
                )
                image_obj.data.put(img_byte_arr.getvalue(), content_type="image/webp")
                image_obj.save()
                return image_obj
        except (requests.exceptions.RequestException, ValueError, IOError) as e:
            log(f"==== Error: {e} ====")
        return None

    ################### Dunder Methods #####################
    ################### Property Methods #####################
    ################### Crud Methods #####################
    def read(self):
        result = self.data.read()
        self.data.seek(0)
        return result

    def url(self, size="orig"):
        return f"/image/{self.pk}/{size}"

    # MARK: generate_image

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)
            self.save()

    def add_tags(self, tags):
        for tag in tags:
            self.add_tag(tag)

    def remove_tag(self, tag):
        try:
            self.tags.remove(tag)
            self.save()
        except ValueError:
            pass

    def resize(self, max_size=1024):
        """
        returns a dynamically resized image file
        """
        img = ImageTools.open(io.BytesIO(self.read()))
        resized_img = img.copy()
        max_size = self._sizes.get(max_size) or int(max_size)
        if max_size <= 0:
            raise ValueError("Invalid max_size value. Must be a positive integer.")
        resized_img.thumbnail((max_size, max_size))
        img_byte_arr = io.BytesIO()
        resized_img.save(img_byte_arr, format="WEBP")
        return img_byte_arr.getvalue()

    def rotate(self, amount=-90):
        if self.data:
            # Rotate the image 90 degrees
            rotated_img = ImageTools.open(io.BytesIO(self.read()))
            rotated_img_byte_arr = io.BytesIO()
            rotated_img.save(rotated_img_byte_arr, format="WEBP")
            rotated_img = rotated_img.rotate(amount, expand=True)
            self.data.replace(
                rotated_img_byte_arr.getvalue(), content_type="image/webp"
            )
            self.reload()
            self.save()

    def flip(self, horizontal=True, vertical=True):
        if self.data:
            img = ImageTools.open(io.BytesIO(self.read()))
            if horizontal:
                img = img.transpose(ImageTools.FLIP_LEFT_RIGHT)
            if vertical:
                img = img.transpose(ImageTools.FLIP_TOP_BOTTOM)
            flipped_img_byte_arr = io.BytesIO()
            img.save(flipped_img_byte_arr, format="WEBP")
            self.data.replace(
                flipped_img_byte_arr.getvalue(), content_type="image/webp"
            )
            self.save()

    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################
    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        document.pre_save_tags()
        super().auto_pre_save(sender, document, **kwargs)

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################
    def pre_save_tags(self):
        # log("=== Pre Save Tags ===", self.tags)
        self.tags = [t.lower() for t in self.tags if t]
