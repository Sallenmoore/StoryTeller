import io
import random

import requests
from autonomous.ai.audioagent import AudioAgent
from autonomous.model.autoattr import (
    FileAttr,
)
from autonomous.model.automodel import AutoModel
from bs4 import BeautifulSoup

from autonomous import log


class Audio(AutoModel):
    data = FileAttr()

    @classmethod
    def from_file(cls, file):
        try:
            fobj = io.BytesIO(file)
            audio = cls()
            audio.data.put(fobj.getvalue(), content_type="audio/mpeg")
            audio.save()
            return audio
        except (requests.exceptions.RequestException, ValueError, IOError) as e:
            log(f"==== Error: {e} ====")
        return None

    @classmethod
    def generate(cls, audio_text, voice="Algieba", pre_text="", post_text=""):
        log(f"WARNING -- DEPRECATED: Audio.generate\tUse Audio.tts instead.")
        return cls.tts(
            audio_text=audio_text, voice=voice, pre_text=pre_text, post_text=post_text
        )

    @classmethod
    def tts(cls, audio_text, voice="Algieba", pre_text="", post_text=""):
        from models.world import World

        message = f"""
{pre_text}{audio_text}{post_text}
"""
        message = BeautifulSoup(message, "html.parser").get_text()
        voiced_scene = AudioAgent().generate(message, voice=voice)
        obj = cls()
        obj.data.put(voiced_scene, content_type="audio/mpeg")
        obj.save()
        return obj

    @classmethod
    def transcribe(
        cls, audio_file, prompt="Transcribe the following audio accurately.", **kwargs
    ):
        from models.world import World

        if not isinstance(audio_file, cls):
            raise ValueError("audio_file must be an instance of Audio class.")
        transcription = AudioAgent().transcribe(
            audio_file.to_file(), prompt=prompt, **kwargs
        )
        return transcription

    @classmethod
    def get_voice(cls, filters=[]):
        from models.world import World

        if voices := AudioAgent.available_voices(filters=filters):
            return random.choice(voices)
        return ""

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

    def add_to_file(self, file):
        if self.data:
            current_data = self.data.read()
            new_data = current_data + file
            log(self.data.size)
            self.data.replace(new_data, content_type="audio/mpeg")
            log(self.data.size)
        else:
            self.data.put(file, content_type="audio/mpeg")
        self.save()
        return self

    def delete(self):
        if self.data:
            self.data.delete()
        return super().delete()

    def url(self):
        return f"/audio/{self.pk}"
