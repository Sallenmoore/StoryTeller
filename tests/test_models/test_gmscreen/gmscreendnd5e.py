from flask import get_template_attribute
from autonomous.model.autoattr import StringAttr
from .gmscreenarea import GMScreenArea


class GMScreenDnD5E(GMScreenArea):
    _macro = "dnd5e_area"
    name = StringAttr(default="D&D5e Reference")

    def area(self):
        snippet = get_template_attribute("manage/_gmscreen.html", self.macro)(self)
        return super().area(content=snippet)
