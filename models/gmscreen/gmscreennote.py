from autonomous.model.autoattr import StringAttr
from .gmscreenarea import GMScreenArea


class GMScreenNote(GMScreenArea):
    _macro = "screen_note_area"
    name = StringAttr(default="Notes")

    @property
    def note(self):
        if not self._entries:
            self._entries = [""]
        return self._entries[0]

    @note.setter
    def note(self, val):
        self._entries = [val]
