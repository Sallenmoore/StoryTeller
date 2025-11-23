import random

import markdown
from autonomous.model.autoattr import ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel

from autonomous import log
from tests.test_models.test_ttrpgobject import ability


class Ability(AutoModel):
    world = ReferenceAttr(choices=["World"])
    name = StringAttr(default="")
    description = StringAttr(default="")
    action = StringAttr(
        choices=["main action", "bonus action", "reaction", "free action", "passive"]
    )
    category = StringAttr(
        choices=[
            "offensive",
            "defensive",
            "social",
            "support",
            "control",
            "movement",
            "utility",
        ],
        default="offensive",
    )
    effects = StringAttr(default="")
    duration = StringAttr(default="")
    dice_roll = StringAttr(default="")
    mechanics = StringAttr(default="")

    _funcobj = {
        "name": "generate_ability",
        "description": "Generates a new Ability for a TTRPG Character.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Unique name for the Ability.",
                },
                "action": {
                    "type": "string",
                    "enum": [
                        "main action",
                        "bonus action",
                        "reaction",
                        "free action",
                        "passive",
                    ],
                    "description": "type of action required.",
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "offensive",
                        "defensive",
                        "social",
                        "support",
                        "control",
                        "movement",
                        "utility",
                    ],
                    "description": "category of the ability.",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the ability and how the Character aquired the ability in MARKDOWN.",
                },
                "effects": {
                    "type": "string",
                    "description": "Description of the ability's effects.",
                },
                "duration": {
                    "type": "string",
                    "description": "The duration of the ability's effects.",
                },
                "dice_roll": {
                    "type": "string",
                    "description": "The dice roll mechanics for determining the success or failure of the ability.",
                },
                "mechanics": {
                    "type": "string",
                    "description": "Any additional mechanics or rules associated with the ability.",
                },
            },
        },
    }

    def __str__(self):
        return f"{f'NAME: {self.name}' if self.name else ''} [{f'{self.action}' if self.action else ''}]: {f'CATEGORY: {self.category}' if self.category else ''} {f'; DESCRIPTION: {self.description}' if self.description else ''} {f'; EFFECTS: {self.effects}' if self.effects else ''} {f'; DURATION: {self.duration}' if self.duration else ''}{f'; DICE ROLL: {self.dice_roll}' if self.dice_roll else ''}{f'; MECHANICS: {self.mechanics}' if self.mechanics else ''}"

    @property
    def genre(self):
        if self.world:
            return self.world.genre
        return "generic"

    @property
    def system(self):
        if self.world:
            return self.world.system
        return None

    @property
    def path(self):
        if self.world:
            return f"world/{self.world.pk}"
        return None

    def generate(self, obj=None):
        obj = (obj or self.world) or (
            lambda: (_ for _ in ()).throw(
                ValueError(
                    "World or parent object must be provided to generate Ability."
                )
            )
        )()
        response = self.system.generate_json(
            f"Generate a unique {obj.genre} TTRPG ability for the following {obj.title} named {obj.name}. Ensure conistency with the {obj.title}'s tone: {obj.backstory} {f'Use the following notes as a guideline: {self}' if str(self) else ''}",
            f"Given a description of an element in a {obj.genre} TTRPG world, generate a new ability that is consistent with the description {f' and follows these guidelines: {self}' if str(self) else ''}.\nProvide the ability in the given JSON format.",
            Ability._funcobj,
        )

        def process_markdown_field(field_name):
            return (
                markdown.markdown(
                    response.get(field_name, getattr(self, field_name))
                    .replace("```markdown", "")
                    .replace("```", "")
                )
                .replace("h1>", "h3>")
                .replace("h2>", "h3>")
            )

        if response:
            self.world = obj.world
            self.name = self.name or response.get("name", "")
            self.action = response.get("action", self.action)
            self.category = response.get("category", self.category)
            for field in [
                "description",
                "effects",
                "duration",
                "dice_roll",
                "mechanics",
            ]:
                setattr(self, field, process_markdown_field(field))
            self.save()
        log(f"Generating ability for {obj.name}")
        if hasattr(obj, "abilities") and self not in obj.abilities:
            obj.abilities += [self]
            obj.save()
