import io

from autonomous.ai.imageagent import ImageAgent
from autonomous.model.autoattr import (
    StringAttr,
)

from autonomous import log
from models.utility import parse_attributes, tasks

from .image import Image


class Graphic(Image):
    @classmethod
    def generate(cls, prompt, **kwargs):
        graphic_obj = cls(prompt=prompt, tags=["graphic", *kwargs.get("tags", [])])
        description = tasks.generate_text(
            prompt,
            primer="Provide a vivid and detailed description of a paneled graphic novel page for an AI-generated image that captures the essence of the prompt, including key visual elements, setting, and significant characters.",
        )

        description = f"{parse_attributes.sanitize(description)}\n\nArt Style: Comic Book, Graphic Novel, Illustrated, Vibrant Colors, Dynamic Composition"
        graphic_obj.description = description
        graphic_obj.save()
        if kwargs.get("files"):
            kwargs["files"] = {
                fn: f.to_file() for fn, f in kwargs.get("files").items() if f
            }
        try:
            image = ImageAgent().generate(prompt=prompt, **kwargs)
        except Exception as e:
            log(f"==== Error: Unable to create image ====\n\n{e}", _print=True)
            return None
        else:
            graphic_obj.data.put(io.BytesIO(image), content_type="image/webp")
            graphic_obj.save()
        return graphic_obj

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
        graphic_obj = Graphic(prompt=image.prompt, tags=image.tags)
        graphic_obj.data.put(image.data.read(), content_type="image/webp")
        return graphic_obj

    @property
    def description(self):
        return self.prompt

    @description.setter
    def description(self, value):
        self.prompt = value
