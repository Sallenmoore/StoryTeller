from bs4 import BeautifulSoup

from autonomous.ai.audioagent import AudioAgent


class AudioMixin:
    """
    Mixin class for handling audio data. Audio file must be called 'audio' and content 'audio_text' (it can be a @property wrapper).
    """

    def generate_audio(self, pre_text="", post_text=""):
        from models.world import World

        message = f"""
{pre_text}{self.audio_text}{post_text}
"""
        pc_message = BeautifulSoup(message, "html.parser").get_text()
        voice = self.voice if hasattr(self, "voice") else "onyx"
        voiced_scene = AudioAgent().generate(pc_message, voice=voice)
        if self.audio:
            self.audio.delete()
            self.audio.replace(voiced_scene, content_type="audio/mpeg")
        else:
            self.audio.put(voiced_scene, content_type="audio/mpeg")
        self.save()
