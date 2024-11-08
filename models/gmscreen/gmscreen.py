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


class GMScreenArea(AutoModel):
    meta = {
        "abstract": True,
        "allow_inheritance": True,
        "strict": False,
    }
    entries = ListAttr(StringAttr(default=""))
    screen = ReferenceAttr(choices=["GMScreen"])

    @property
    def macro(self):
        return self._macro

    def area(self, content=None):
        content = content or get_template_attribute(
            "manage/_gmscreen.html", self.macro
        )(self)
        return get_template_attribute("manage/_gmscreen.html", "screen_area")(
            self, content=content
        )


class GMScreenNote(GMScreenArea):
    _macro = "screen_note_area"
    name = StringAttr(default="Notes")

    @property
    def note(self):
        if not self._entries:
            self._entries = [""]
        return self._entries[0]

    @note.setter
    def note(self, val):
        self._entries = [val]


class GMScreenTable(GMScreenArea):
    _macro = "screen_table_area"
    selected = StringAttr(default="")
    datafile = StringAttr(default="")
    name = StringAttr(default="Roll Table")

    @property
    def itemlist(self):
        if not self.entries and self.datafile:
            datafile = (
                self.datafile
                if "gmscreendata" in self.datafile
                else f"static/gmscreendata/{self.datafile}"
            )
            with open(datafile) as fptr:
                self.entries = json.load(fptr)
                self.save()
        return self.entries

    @itemlist.setter
    def itemlist(self, val):
        self.entries = val


class GMScreenLink(GMScreenArea):
    _macro = "screen_link_area"
    name = StringAttr(default="Links")
    objs = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))


class GMScreenDnD5E(GMScreenArea):
    _macro = "dnd5e_area"
    name = StringAttr(default="D&D5e Reference")

    def area(self):
        snippet = get_template_attribute("manage/_gmscreen.html", self.macro)(self)
        return super().area(content=snippet)


class GMScreen(AutoModel):
    # meta = {"collection": "GMScreen"}
    name = StringAttr(default="New Screen")
    world = ReferenceAttr(choices=["World"], required=True)
    user = ReferenceAttr(choices=["User"], required=True)
    areas = ListAttr(ReferenceAttr(choices=[GMScreenArea]))

    area_types = {
        "note": GMScreenNote,
        "table": GMScreenTable,
        "link": GMScreenLink,
        "wildmagic": GMScreenTable,
        "loot": GMScreenTable,
        "dnd5e": GMScreenDnD5E,
    }

    def add_area(self, area_type, name=""):
        params = {"name": name or area_type}
        if AreaModel := self.area_types.get(area_type):
            if area_type in ["wildmagic", "loot"]:
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
