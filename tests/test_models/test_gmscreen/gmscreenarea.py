from flask import get_template_attribute

from autonomous import log
from autonomous.model.autoattr import BoolAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel


class GMScreenArea(AutoModel):
    meta = {
        "abstract": True,
        "allow_inheritance": True,
        "strict": False,
    }
    entries = ListAttr(StringAttr(default=""))
    screen = ReferenceAttr(choices=["GMScreen"])
    editable = BoolAttr(default=False)

    @property
    def macro(self):
        return self._macro

    def area(self, content=None, editable=False):
        content = content or get_template_attribute(
            "manage/_gmscreen.html", self.macro
        )(self, editable)
        return get_template_attribute("manage/_gmscreen.html", "screen_area")(
            self, content=content
        )
