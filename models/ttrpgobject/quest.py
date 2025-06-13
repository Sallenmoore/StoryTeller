import random

from autonomous import log
from autonomous.model.autoattr import DictAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.base.ttrpgbase import TTRPGBase


class Quest(AutoModel):
    name = StringAttr(default="")
    description = StringAttr(default="")
    scenes = ListAttr(DictAttr(default=""))
    summary = StringAttr(default="")
    rewards = StringAttr(default="")
    contact = ReferenceAttr(choices=["Character"])
    locations = ListAttr(StringAttr(default=""))
    antagonist = StringAttr(default="")
    hook = StringAttr(default="")
    dramatic_crisis = StringAttr(default="")
    climax = StringAttr(default="")
    plot_twists = ListAttr(StringAttr(default=""))
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    status = StringAttr(
        default="available", choices=["available", "active", "completed", "failed"]
    )
