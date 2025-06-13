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

    gm_screen_table_presets = [
        "swn_items_100_detailed.json",
        "swn_consumables_100_detailed.json",
    ]

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
                            "duration",
                            "dice_roll",
                        ],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "A name.",
                            },
                            "description": {
                                "type": "string",
                                "description": "A summary description and how it is activated in MARKDOWN.",
                            },
                            "effects": {
                                "type": "string",
                                "description": "Description of the effects.",
                            },
                            "duration": {
                                "type": "string",
                                "description": "The duration of the effects.",
                            },
                            "dice_roll": {
                                "type": "string",
                                "description": "The dice roll mechanics for determining the success or failure, if and only if required, else empty string.",
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
                self.entries = [
                    f"{o['name']}:{o['description']}" for o in json.load(fptr)
                ]
                log(self.entries, _print=True)
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
            instructions=f"As an expert AI in canon as well as homebrew elements of an {self.screen.world.genre.title()} Table Top RPG, Generate a roll table fitting the following description:{prompt} ",
            description=f"Generate a roll table for a {self.screen.world.genre} TTRPG",
        ).generate(prompt, function=self._funcobj)
        log(response, _print=True)
        self.itemlist = []
        for v in response["items"]:
            item = f"{v.get('name')}: {v.get('description')}. {v.get('effects')}. {v.get('duration')}. {v.get('dice_roll')}"
            self.itemlist.append(item)
        self.save()
        return self.itemlist
