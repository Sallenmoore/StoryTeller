import os
import random
import urllib
from base64 import b64decode

import requests
from bs4 import BeautifulSoup
from openai import OpenAI

from autonomous import log
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from autonomous.storage.imagestorage import ImageStorage

IMAGES_BASE_PATH = os.environ.get("IMAGE_BASE_PATH", "static/images/tabletop")


class Image(AutoModel):
    # meta = {"collection": "Image"}
    asset_id = StringAttr(default="")
    prompt = StringAttr(default="")
    tags = ListAttr(StringAttr(default=""))
    worlds = ListAttr(ReferenceAttr(choices=["World"]))

    _storage = ImageStorage(IMAGES_BASE_PATH)
    _client = OpenAI(api_key=os.environ.get("OPENAI_KEY"))

    ################### Class Methods #####################
    @classmethod
    def storage_scan(cls):
        for img in cls.all():
            if not img.asset_id or not os.path.exists(
                f"{IMAGES_BASE_PATH}/{img.asset_id}"
            ):
                img.delete()
        for img_path in cls._storage.scan_storage():
            asset_id = img_path.split("/")[-2]
            if img := cls.find(_asset_id=asset_id):
                continue
            img = cls(_asset_id=asset_id)
            img.save()

    @classmethod
    def generate(
        cls,
        prompt: str,
        tags=[],
        img_quality="standard",
        img_size="1024x1024",
        text=False,
    ):
        if not text:
            prompt = f"""{prompt}
            IMPORTANT: The image MUST NOT contain any TEXT.
            """
        prompt = BeautifulSoup(prompt, "html.parser").get_text()
        log(f"=== generation prompt ===\n\n{prompt}")
        try:
            response = cls._client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                quality=img_quality,
                response_format="b64_json",
                size=img_size,
            )
            image_dict = response.data[0]
            image = b64decode(image_dict.b64_json)
        except Exception as e:
            log(f"==== Error: Unable to create image ====\n\n{e}")
            return None
        else:
            image_data = Image(
                prompt=prompt,
                tags=tags,
            )
            image_data.asset_id = cls._storage.save(image)
            image_data.save()
        return image_data

    @classmethod
    def get_image_list(cls, max=10, tags=[]):
        image_list = [i for i in cls.all() if all(tag in i.tags for tag in tags)]
        if image_list:
            image_list = random.sample(image_list, k=min(len(image_list), max))
        [log(i) for i in image_list]
        return image_list

    @classmethod
    def from_url(cls, url, prompt="", tags=[]):
        response = requests.get(url)
        if response.status_code == 200 and response.headers["Content-Type"].startswith(
            "image/"
        ):
            image_data = Image(
                prompt=prompt,
                tags=tags,
                asset_id=cls._storage.save(response.content, crop=True),
            )
            image_data.save()
            return image_data
        log("==== Error: Unable to save image ====")
        return None

    ################### Dunder Methods #####################
    ################### Property Methods #####################
    ################### Crud Methods #####################
    def url(self, size="orig"):
        try:
            # log(self.asset_id)
            result = self._storage.get_url(self.asset_id, size=size)
        except Exception as e:
            log(e)
            result = None

        if not result:
            prompt_param = urllib.parse.urlencode(
                {
                    "text": self.prompt.split(".")[0]
                    if "." in self.prompt
                    else self.prompt
                }
            )
            result = f"https://placehold.co/600x400?{prompt_param}"
        return result

    def remove_img_file(self):
        if self.asset_id:
            try:
                return self._storage.remove(self.asset_id)
            except Exception as e:
                log(e)

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

    def rotate(self, amount=-90):
        self._storage.rotate(self.asset_id, amount)

    def flip(self, horizontal=True, vertical=True):
        self._storage.flip(self.asset_id, flipx=horizontal, flipy=vertical)

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
