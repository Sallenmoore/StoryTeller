from autonomous.model.autoattr import StringAttr, ListAttr, ReferenceAttr
from .gmscreenarea import GMScreenArea


class GMScreenLink(GMScreenArea):
    _macro = "screen_link_area"
    name = StringAttr(default="Links")
    objs = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
