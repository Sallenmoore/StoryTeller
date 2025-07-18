import io

from autonomous import log
from autonomous.ai.audioagent import AudioAgent
from autonomous.model.autoattr import FileAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel


class GameMaster(AutoModel):
    party = ReferenceAttr(choices=["Faction"])
    history = StringAttr(default="")
    audio_ = FileAttr()
    audio_transcription = StringAttr(default="")
    images = ListAttr(ReferenceAttr(choices=["Image"]))
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))

    ################### Crud Methods #####################
    @property
    def audio(self):
        if self.audio_:
            self.audio_.seek(0)
            return self.audio_.read()
        else:
            log("No audio file found.", _print=True)
            return None

    @audio.setter
    def audio(self, value):
        if isinstance(value, bytes):
            log("Setting audio file:", type(value), _print=True)
            if self.audio_:
                self.audio_.delete()
            self.audio_.put(value, content_type="audio/mpeg")
            self.save()
        else:
            raise ValueError("Audio must be bytes.")

    def delete(self):
        if self.audio_:
            self.audio_.delete()
        return super().delete()

    ################### General Methods #####################

    def transcribe(self):
        if not self.audio:
            log("No audio file to transcribe.", _print=True)
            return
        agent = AudioAgent()
        try:
            audio = io.BytesIO(self.audio)
            audio.name = "audio_file.webm"  # Set a name for the BytesIO object
            self.audio_transcription = agent.generate_text(audio)
            log("Audio transcription completed successfully.", _print=True)
        except Exception as e:
            log(f"Error during audio transcription: {e}", _print=True)
            self.audio_transcription = "Transcription failed."
        finally:
            self.save()
