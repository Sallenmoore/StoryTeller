import markdown

from autonomous import log
from autonomous.db import ValidationError
from models.images.image import Image


class GNMaker:
    @property
    def comic(self):
        if isinstance(self._comic, list):
            self._comic = self._comic[0] if self._comic else ""
        return self._comic

    @comic.setter
    def comic(self, value):
        if not isinstance(self._comic, str):
            raise ValueError(f"comic must be a string: {value}")
        self._comic = value

    @property
    def comic_prompt(self):
        if isinstance(self._comic_prompt, list):
            self._comic_prompt = self._comic_prompt[0] if self._comic_prompt else ""
        return self._comic_prompt

    @comic_prompt.setter
    def comic_prompt(self, value):
        if not isinstance(value, str):
            raise ValueError(f"comic must be a string: {type(value)} || {value}")
        self._comic_prompt = value.strip()

    def generate_scene(self):
        comic_prompt = """Using only the descriptions provided below, rewrite the following episode summary information as markdown into a description optimized for generating a 6 scene comic book panel using Dall-E. Use vivid, detailed, and consistent character and location descriptions for each scene.

        Provide a description for each of the following 6 panels: Top-Left, Top-Right, Mid-Left, Mid-Right, Bottom-Left, Bottom-Right

        """

        comic_prompt += """
        Character Descriptions:
        """
        for ass in self.characters:
            comic_prompt += f"""
                - {ass.name}: {ass.description}
                """

        comic_prompt += """
        Location Descriptions:
        """
        for ass in self.scenes:
            comic_prompt += f"""
            - {ass.name}: {ass.description}
            """

        comic_prompt += f"""
        Events:
        {self.summary or self.session_report}
        """
        scene_text = self.world.system.generate_text(
            comic_prompt,
            primer="As an expert AI assitant in writing detailed descriptions that are optimized for generating consistant characters using Dall-E, generate a vivid description for a 6 scene comic book panel",
        )

        result = markdown.markdown(scene_text.strip())
        self.comic_prompt = f"""
        A photogrid of an adventuring party consisting of {", ".join([f"a {c.gender} {c.race} named {c.name}" for c in self.characters])}

        {result}
        """
        self.save()

    def generate_comic(self):
        if self.comic:
            self.comic.delete()
        log("=========> prompt length", len(self.comic_prompt))
        if 80 < len(self.comic_prompt) < 3900:
            prompt = f"""
            Based on the following description of the events and elements of a TTRPG {self.campaign.world.genre} Session, generate a 6 panel photogrid in a comic book style using consistent character and location descriptions across each panel.

            {self.comic_prompt}
            """
            if panel := Image.generate(
                prompt,
                tags=["comic-panel", "episode"],
                text=True,
            ):
                panel.save()
                self.comic = panel
                self.save()
        return self.comic

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################

    def clean(self):
        if self.attrs:
            self.verify_attr()

    ################### verify associations ##################
    def verify_attr(self):
        pass
