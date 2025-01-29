import json
from autonomous.model.autoattr import StringAttr
from .gmscreenarea import GMScreenArea


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
