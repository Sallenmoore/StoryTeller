import random

from autonomous import log
from autonomous.model.autoattr import StringAttr, ReferenceAttr
from autonomous.model.automodel import AutoModel


class Quest(AutoModel):
    name = StringAttr(default="")
    description = StringAttr(default="")
    rewards = StringAttr(default="")
    contact = ReferenceAttr(choices=["Character"])
    location = StringAttr(default="")
    status = StringAttr(
        default="available", choices=["available", "active", "completed", "failed"]
    )
