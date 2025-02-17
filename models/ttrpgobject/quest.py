import random

from autonomous import log
from autonomous.model.autoattr import ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.base.ttrpgbase import TTRPGBase


class Quest(AutoModel):
    name = StringAttr(default="")
    description = StringAttr(default="")
    summary = StringAttr(default="")
    rewards = StringAttr(default="")
    contact = ReferenceAttr(choices=["Character"])
    location = StringAttr(default="")
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    status = StringAttr(
        default="available", choices=["available", "active", "completed", "failed"]
    )
