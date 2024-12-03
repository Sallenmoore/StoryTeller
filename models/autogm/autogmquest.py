from autonomous.model.automodel import AutoModel
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)


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
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
