from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel


class AutoGMQuest(AutoModel):
    name = StringAttr()
    type = StringAttr(choices=["main quest", "side quest", "optional objective"])
    description = StringAttr()
    status = StringAttr(
        choices=["unknown", "rumored", "active", "completed", "failed", "abandoned"],
        default="unknown",
    )
    next_steps = StringAttr()
    importance = StringAttr()
    plot = StringAttr()
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
