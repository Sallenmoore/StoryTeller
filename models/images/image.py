import io
import random

import requests
from autonomous.ai.imageagent import ImageAgent
from autonomous.model.autoattr import (
    FileAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from bs4 import BeautifulSoup
from PIL import Image as ImageTools

from autonomous import log


class Image(AutoModel):
    # meta = {"collection": "Image"}
    data = FileAttr(default="")
    prompt = StringAttr(default="")
    tags = ListAttr(StringAttr(default=""))
    associations = ListAttr(
        ReferenceAttr(choices=["TTRPGBase", "Story", "Event", "Episode", "Encounter"])
    )

    ################### Class Variables #####################

    _sizes = {"thumbnail": 100, "small": 300, "medium": 600, "large": 1000}

    ################### Class Methods #####################

    @classmethod
    def generate(
        cls,
        prompt,
        tags=None,
        text=False,
        files=None,
        **kwargs,
    ):
        tags = tags or []
        files = files or []
        # Clean the prompt to remove any HTML tags
        prompt = BeautifulSoup(prompt, "html.parser").get_text()
        # log(f"=== generation prompt ===\n\n{prompt}", _print=True)
        temp_prompt = (
            f"""{prompt}
IMPORTANT: The image MUST NOT contain any TEXT.
"""
            if not text
            else prompt
        )
        try:
            if files := [f.to_file() for f in files if f]:
                random.shuffle(files)
            image = ImageAgent().generate(prompt=temp_prompt, files=files, **kwargs)
        except Exception as e:
            log(f"==== Error: Unable to create image ====\n\n{e}", _print=True)
            return None
        else:
            image_obj = cls(
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
                img = img.copy()
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="WEBP")
                image_obj = cls(
                    prompt=prompt,
                    tags=tags,
                )
                image_obj.data.put(img_byte_arr.getvalue(), content_type="image/webp")
                image_obj.save()
                return image_obj
        except (requests.exceptions.RequestException, ValueError, IOError) as e:
            log(f"==== Error: {e} ====")
        return None

    @classmethod
    def from_file(cls, file, prompt="", tags=None):
        tags = tags if tags else []
        try:
            with ImageTools.open(io.BytesIO(file)) as img:
                img = img.copy()
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="WEBP")
                image_obj = cls(
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
        if self.data:
            self.data.seek(0)
            return self.data.read()

    def to_file(self):
        if self.data:
            self.data.seek(0)
            return self.data.read()
        return None

    def delete(self):
        if self.data:
            self.data.delete()
        return super().delete()

    def remove_association(self, assoc):
        if assoc in self.associations:
            self.associations.remove(assoc)
            self.save()
        if len(self.associations) == 0:
            self.delete()

    ################### Instance Methods #####################

    def url(self, size="orig"):
        return f"/image/{self.pk}/{size}"

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
        if raw_data := self.read():
            img = ImageTools.open(io.BytesIO(raw_data))
            resized_img = img.copy()
            max_size = self._sizes.get(max_size) or int(max_size)
            if max_size <= 0:
                raise ValueError("Invalid max_size value. Must be a positive integer.")
            resized_img.thumbnail((max_size, max_size))
            img_byte_arr = io.BytesIO()
            resized_img.save(img_byte_arr, format="WEBP")
            return img_byte_arr.getvalue()

    def rotate(self, amount=-90):
        if raw_data := self.read():
            # Open the image
            rotated_img = ImageTools.open(io.BytesIO(raw_data))
            # Rotate the image
            rotated_img = rotated_img.rotate(amount, expand=True)
            rotated_img_byte_arr = io.BytesIO()
            rotated_img.save(rotated_img_byte_arr, format="WEBP")
            rotated_img_data = rotated_img_byte_arr.getvalue()
            self.data.delete()
            self.data.put(rotated_img_data, content_type="image/webp")
            self.save()
            self.data.seek(0)  # Reset the data stream position to the beginning

    def flip(self, horizontal=True, vertical=True):
        if raw_data := self.read():
            img = ImageTools.open(io.BytesIO(raw_data))
            if horizontal:
                img = img.transpose(ImageTools.FLIP_LEFT_RIGHT)
            if vertical:
                img = img.transpose(ImageTools.FLIP_TOP_BOTTOM)
            flipped_img_byte_arr = io.BytesIO()
            img.save(flipped_img_byte_arr, format="WEBP")
            self.data.delete()
            self.data.put(flipped_img_byte_arr.getvalue(), content_type="image/webp")
            self.data.seek(0)

    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################
    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_tags()
        document.pre_save_associations()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################
    def pre_save_tags(self):
        # log("=== Pre Save Tags ===", self.tags)
        self.tags = [t.lower() for t in self.tags if t]

    def pre_save_associations(self):
        # log("=== Pre Save Associations ===", self.associations)
        self.associations = list(set(self.associations))
