import json

import dmtoolkit
from flask import get_template_attribute

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.gmscreen.gmscreenarea import GMScreenArea
from models.gmscreen.gmscreendnd5e import GMScreenDnD5E
from models.gmscreen.gmscreenlink import GMScreenLink
from models.gmscreen.gmscreennoncanon import GMScreenNonCanon
from models.gmscreen.gmscreennote import GMScreenNote
from models.gmscreen.gmscreentable import GMScreenTable


class GMScreen(AutoModel):
    # meta = {"collection": "GMScreen"}
    name = StringAttr(default="New Screen")
    world = ReferenceAttr(choices=["World"], required=True)
    user = ReferenceAttr(choices=["User"], required=True)
    areas = ListAttr(ReferenceAttr(choices=["GMScreenArea"]))

    area_types = {
        "note": GMScreenNote,
        "table": GMScreenTable,
        "link": GMScreenLink,
        "wildmagic": GMScreenTable,
        "noncanon": GMScreenNonCanon,
        "dnd5e": GMScreenDnD5E,
    }

    def add_area(self, area_type, name=""):
        params = {"name": name or area_type}
        if AreaModel := self.area_types.get(area_type):
            if area_type in ["wildmagic"]:
                params["datafile"] = f"static/gmscreendata/{area_type}.json"
            area = AreaModel(**params)
        else:
            raise ValueError("Invalid area type")
        area.screen = self
        area.save()
        self.areas.append(area)
        self.save()

    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################

    def clean(self):
        super().clean()
        self.verify_areas()

    ################### verify associations ##################
    def verify_areas(self):
        if self.areas and not all(isinstance(v, GMScreenArea) for v in self.areas):
            raise ValidationError("Entries must be GMScreenArea objects")
