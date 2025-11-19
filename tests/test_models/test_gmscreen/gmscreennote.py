import markdown

from autonomous import log
from autonomous.model.autoattr import StringAttr

from .gmscreenarea import GMScreenArea

# This file defines the GMScreenNote class, which is a specific type of GMScreenArea
# that is used to store notes on a GM screen. It inherits from GMScreenArea and
# provides a specific implementation for handling notes.


class GMScreenNote(GMScreenArea):
    _macro = "screen_note_area"
    name = StringAttr(default="Notes")
    text_type = StringAttr(default="rich", choices=["rich", "markdown"])

    @property
    def note(self):
        if not self.entries:
            self.entries = [""]
        note = self.entries[0]
        return note

    @note.setter
    def note(self, val):
        self.entries = [val]

    def display_note(self):
        log(self.note, self.text_type)
        if self.text_type == "markdown":
            result = markdown.markdown(self.note, extensions=["tables"])
            log(result)
            return result
        return self.note
