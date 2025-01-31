import json

from autonomous import log
from autonomous.ai.jsonagent import JSONAgent
from autonomous.model.autoattr import StringAttr

from .gmscreenarea import GMScreenArea


class GMScreenTable(GMScreenArea):
    _macro = "screen_table_area"
    selected = StringAttr(default="")
    datafile = StringAttr(default="")
    name = StringAttr(default="Roll Table")

    _funcobj = {
        "name": "generate_items",
        "description": "creates a list of items for a RPG roll table",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": "Generate a list of 100 items that fit the given prompt's specifications.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "name",
                            "description",
                            "effects",
                            "rarity",
                            "duration",
                            "dice_roll",
                        ],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "A name for the item.",
                            },
                            "description": {
                                "type": "string",
                                "description": "A summary description of the item and how it is activated in MARKDOWN.",
                            },
                            "rarity": {
                                "type": "string",
                                "description": "The rarity of the item ranging, such as common, uncommon, rare, very rare, legendary, etc.",
                            },
                            "effects": {
                                "type": "string",
                                "description": "Description of the item's effects.",
                            },
                            "duration": {
                                "type": "string",
                                "description": "The duration of the item's effects.",
                            },
                            "dice_roll": {
                                "type": "string",
                                "description": "The dice roll mechanics for determining the success or failure of the item, if and only if required, else empty string.",
                            },
                        },
                    },
                },
            },
        },
    }

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

    def generate_table(self, prompt):
        from .gmscreen import GMScreen

        log(prompt, _print=True)
        response = JSONAgent(
            name=f"{self.screen.world.genre} TableTop RPG List Generator",
            instructions=f"As an expert AI in canon as well as homebrew elements of an {self.screen.world.genre.title()} Table Top RPG, Generate a list of various types of items fitting the following description:{prompt} ",
            description=f"Generate a list of at least 20 various types of items for a {self.screen.world.genre} RPG roll table",
        ).generate(prompt, function=self._funcobj)
        log(response, _print=True)
        for v in response["items"]:
            item = f"{v.get('name')} [{v.get('rarity')}]: {v.get('description')}"
            self.itemlist.append(item)
        self.save()
        return self.itemlist
