import json
import random

from autonomous import log
from autonomous.model.autoattr import (
    IntAttr,
    StringAttr,
)
from models.ttrpgobject.ttrpgobject import TTRPGObject

LOOT_MULTIPLIER = 3


class Encounter(TTRPGObject):
    difficulty_rating = IntAttr(default=0)
    enemy_type = StringAttr(default="")
    complications = StringAttr(default="")
    combat_scenario = StringAttr(default="")
    noncombat_scenario = StringAttr(default="")

    LOOT_MULTIPLIER = 3
    parent_list = ["Location"]
    _difficulty_list = [
        "trivial",
        "easy",
        "medium",
        "hard",
        "deadly",
    ]
    # {item_type} consistent with
    _items_types = [
        "junk item",
        "trinket or bauble",
        "form of currency",
        "valuable item of no utility, such as gems or art",
        "consumable item, such as food or drink",
        "utility item, such as tools or a map",
        "weapon",
        "armor",
        "unique artifact",
    ]

    _funcobj = {
        "name": "generate_encounter",
        "description": "Generate an Encounter object",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "An evocative title for the encounter",
                },
                "backstory": {
                    "type": "string",
                    "description": "The backstory of the encounter from the antagonists' perspective",
                },
                "desc": {
                    "type": "string",
                    "description": "A short physical description that will be used to generate an image of the scene the characters come upon to begin the encounter ",
                },
                "enemy_type": {
                    "type": "string",
                    "description": "The type of enemies the characters will encounter",
                },
                "complications": {
                    "type": "string",
                    "description": "Additional environmental effects, unforeseen circumstances, or unexpected events that complicate the encounter",
                },
                "combat_scenario": {
                    "type": "string",
                    "description": "The event or events that will cause unavoidable combat",
                },
                "noncombat_scenario": {
                    "type": "string",
                    "description": "The event or events that will allow players to avoid combat",
                },
                "notes": {
                    "type": "array",
                    "description": "3 short descriptions of potential side quests involving the outcome of this encounter",
                    "items": {"type": "string"},
                },
            },
        },
    }

    ################## Instance Properties ##################
    @property
    def actors(self):
        return [*self.characters, *self.creatures]

    # @property
    # def rewards(self):
    #     return GMScreenLootGenerator.generate()

    @property
    def difficulty(self):
        if not self.difficulty_rating:
            self.difficulty_rating = random.choice(range(len(self._difficulty_list)))
            self.save()
        return self._difficulty_list[self.difficulty_rating]

    @difficulty.setter
    def difficulty(self, value):
        if isinstance(value, str):
            if value not in self._difficulty_list:
                raise ValueError(
                    f"Encounter difficulty must be one of {self._difficulty_list}"
                )
            self.difficulty_rating = self._difficulty_list.index(value)
        elif isinstance(value, int) and 0 <= value < len(self._difficulty_list):
            self.difficulty_rating = value
        else:
            raise TypeError(
                f"Encounter difficulty must be one of {self._difficulty_list}"
            )

    @property
    def difficulty_list(self):
        return self._difficulty_list

    @property
    def items(self):
        items = [c for c in super().items if c.parent == self]
        for a in self.actors:
            items += [r for r in a.items if r.parent == a]
        return items

    @property
    def enemies(self):
        return [*self.creatures, *self.characters]

    @enemies.setter
    def enemies(self, val):
        for enemy in val:
            if enemy.model_name() == "Creature":
                self.creatures.append(enemy)
            elif enemy.model_name() == "Character":
                self.characters.append(enemy)

    @property
    def end_date_str(self):
        return "Ended" if self.end_date.get("year") else "Unknown"

    @property
    def start_date_str(self):
        return "Began" if self.start_date.get("year") else "Unknown"

    @property
    def history_prompt(self):
        return f"""
BEGAN
---
{self.start_date if self.start_date else "Unknown"}

HISTORY
---
{self.backstory_summary}

EVENTS
---
"""

    @property
    def image_prompt(self):
        enemies = [f"- {e.name} ({e.title}) : {e.desc}" for e in self.enemies]
        enemies_str = {"\n".join(enemies)}
        return f"""
        A full color illustrated image of the following encounter:
        {self.desc}
        with the following group preparing for battle:
        {enemies_str}
        """

    @property
    def map(self):
        return self.parent.map if self.parent else self.world.map

    ################## Crud Methods ##################
    @classmethod
    def _icon(cls, type="basic"):
        return {
            "basic": "game-icons:battle-gear",
            "start": "game-icons:battle-gear",
            "end": "mdi:shop-complete",
        }.get(type, "game-icons:battle-gear")

    def generate(self):
        enemy_type = self.enemy_type or random.choice(["humanoid", "monster", "animal"])
        if self.backstory_summary:
            backstory_summary = self.backstory_summary
        elif self.parent and self.parent.backstory_summary:
            backstory_summary = self.backstory_summary
        else:
            backstory_summary = "An unexpected, but highly relevant encounter related to one or more of the party members' backstory"

        players = "".join(
            [
                f"\n  -{p.name}: {p.backstory_summary}"
                for p in self.characters
                if p.is_player
            ]
        )
        desc = ""
        if self.desc:
            desc = self.desc
        elif self.parent and self.parent.desc:
            desc = self.parent.desc
        prompt = f"""Generate a {self.genre} TTRPG encounter scenario using the following guidelines:
{f"- LOCATION: {desc}" if desc else ""}
- SCENARIO: {backstory_summary}
- DIFFICULTY: {self.difficulty}
- ENEMY TYPE: {enemy_type}
- PARTY MEMBERS: {players}
"""
        log(prompt, _print=True)
        results = super().generate(prompt=prompt)
        self.save()
        return results

    ################## Instance Methods ##################
    def check_current(self, episode):
        if (
            episode.start_date
            and self.start_date
            and episode.start_date >= self.start_date
        ):
            return False
        if episode.end_date and self.end_date and episode.end_date <= self.end_date:
            return False
        return True

    def label(self, model):
        if not isinstance(model, str):
            model = model.__name__
        if model == "Item":
            return "Loot"
        return super().label(model)

    def page_data(self):
        return {
            "pk": str(self.pk),
            "name": self.name,
            "start_date": self.start_date.datestr() if self.start_date else "Unknown",
            "end_date": self.end_date.datestr() if self.end_date else "Unknown",
            "backstory": self.backstory,
            "difficulty": self.difficulty,
            "creatures": [{"name": r.name, "pk": str(r.pk)} for r in self.creatures],
            "characters": [{"name": r.name, "pk": str(r.pk)} for r in self.characters],
            "items": [{"name": r.name, "pk": str(r.pk)} for r in self.items],
        }

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################

    # def clean(self):
    #     if self.attrs:
    #         self.verify_attr()

    # ################### verify associations ##################
    # def verify_attr(self):
    #     pass
