from bs4 import BeautifulSoup

from autonomous.ai.audioagent import AudioAgent
from autonomous.model.autoattr import (
    BoolAttr,
    FileAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.ttrpgobject.character import Character


class AutoGMMessage(AutoModel):
    message = StringAttr()
    intent = StringAttr()
    emotion = StringAttr()
    scene = ReferenceAttr(choices=["AutoGMScene"])
    player = ReferenceAttr(choices=[Character])
    audio = FileAttr()
    ready = BoolAttr(default=False)

    def generate_audio(self):
        if not self.message or not self.scene:
            raise ValueError("Message and scene are required to generate audio")

        from models.world import World

        pc_message = BeautifulSoup(self.message, "html.parser").get_text()
        voice = self.player.voice if self.player else "echo"
        voiced_scene = AudioAgent().generate(pc_message, voice=voice)
        if self.audio:
            self.audio.delete()
            self.audio.replace(voiced_scene, content_type="audio/mpeg")
        else:
            self.audio.put(voiced_scene, content_type="audio/mpeg")
        self.save()
