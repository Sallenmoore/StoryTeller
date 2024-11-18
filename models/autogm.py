import json
import os

import markdown
import requests

from autonomous import log
from autonomous.ai.jsonagent import JSONAgent
from autonomous.model.autoattr import (
    BoolAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from autonomous.tasks.autotask import AutoTasks
from models.images.image import Image
from models.ttrpgobject.character import Character
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.item import Item


class AutoGMScene(AutoModel):
    type = StringAttr(choices=["social", "combat", "exploration", "stealth"])
    description = StringAttr()
    summary = StringAttr()
    date = StringAttr()
    player = ReferenceAttr(choices=["Character"])
    npcs = ListAttr(ReferenceAttr(choices=["Character"]))
    combatants = ListAttr(ReferenceAttr(choices=["Creature"]))
    loot = ListAttr(ReferenceAttr(choices=["Item"]))
    roll_required = BoolAttr()
    roll_type = StringAttr()
    roll_attribute = StringAttr()
    roll_description = StringAttr()
    roll_result = IntAttr()
    image = ReferenceAttr(choices=["Image"])
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))

    @classmethod
    def generate_image(cls, pk, image_prompt):
        from models.world import World

        scene = cls.get(pk)
        desc = f"""Based on the below description of characters, setting, and events in a scene of a {scene.player.genre} TTRPG session, generate a single comic book panel the the Western comic art style for the scene.
CHARACTER DESCRIPTION
Gender: {scene.player.gender}
Age: {scene.player.age}
Motif: {scene.player.motif}
Physical Description: {scene.player.description_summary or scene.player.description}

SCENE DESCRIPTION
{image_prompt['description']}
"""
        img = Image.generate(
            desc,
            tags=[
                image_prompt["imgtype"],
                "scene",
                scene.player.name,
                scene.player.world.name,
                scene.player.genre,
            ],
        )
        img.save()
        scene.image = img
        scene.save()

    def generate_npcs(self, objs):
        if not objs:
            return
        for obj in objs:
            char = Character.find(
                world=self.player.world, name=obj["name"]
            ) or Character(
                world=self.player.world,
                race=obj["species"],
                name=obj["name"],
                desc=obj["description"],
                backstory=obj["backstory"],
            )
            char.save()
            self.npcs += [char]
            self.save()
            resp = requests.post(
                f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
            )
            log(resp)

    def generate_combatants(self, objs):
        if not objs:
            return
        for obj in objs:
            char = Creature.find(world=self.player.world, name=obj["name"]) or Creature(
                world=self.player.world,
                type=obj["type"],
                name=obj["name"],
                desc=obj["description"],
            )
            char.save()
            self.combatants += [char]
            self.save()
            resp = requests.post(
                f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
            )
            log(resp)

    def generate_loot(self, objs):
        if not objs:
            return
        for obj in objs:
            char = Item.find(world=self.player.world, name=obj["name"]) or Item(
                world=self.player.world,
                rarity=obj["rarity"],
                name=obj["name"],
                desc=obj["description"],
                features=obj["attributes"],
            )
            char.save()
            self.loot += [char]
            self.save()
            resp = requests.post(
                f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
            )
            log(resp)


class AutoGM(AutoModel):
    world = ReferenceAttr(choices=["World"], required=True)
    agent = ReferenceAttr(choices=[JSONAgent])

    _funcobj = {
        "name": "run_scene",
        "description": "creates the initial or next scene for TTRPG players consistent with the previous scene and the uploaded file describing the world",
        "parameters": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["social", "combat", "exploration", "stealth"],
                    "description": "The type of scene, such as social, combat, exploration, or stealth",
                },
                "description": {
                    "type": "string",
                    "description": "The GM's evocative and detailed description of the scene in MARKDOWN, including any relevant information the GM thinks the players need to know",
                },
                "date": {
                    "type": "string",
                    "description": "The in-game date that the events are occuring on",
                },
                "image": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["description", "imgtype"],
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "A detailed description of the scene that can be used to generate an image.",
                        },
                        "imgtype": {
                            "type": "string",
                            "enum": ["scene", "map"],
                            "description": "The type of image that should be generated, such as a scene or a map.",
                        },
                    },
                },
                "player": {
                    "type": "string",
                    "description": "The full name of the player the GM is currently interacting with",
                },
                "npcs": {
                    "type": "array",
                    "description": "A list of descriptions of non-combatant NPCs in the scenario, if any. Use full names, ",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["species", "name", "description", "backstory"],
                        "properties": {
                            "species": {
                                "type": "string",
                                "description": "The species of the NPC, such as human, elf, dwarf, etc.",
                            },
                            "name": {
                                "type": "string",
                                "description": "A unique name for the NPC",
                            },
                            "description": {
                                "type": "string",
                                "description": "A description of the physical appearance of the NPC detailed enough to generate an image",
                                "items": {"type": "string"},
                            },
                            "backstory": {
                                "type": "string",
                                "description": "The NPC's backstory or history, including any relevant information the GM thinks the players need to know in MARKDOWN format",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
                "combatants": {
                    "type": "array",
                    "description": "if and only if it is a combat type scene, provide a list of descriptions of combatants in the scenario, otherwise an empty list",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["type", "name", "description"],
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "humanoid",
                                    "animal",
                                    "monster",
                                    "unique",
                                ],
                                "description": "The type of combatant, such as humanoid, animal, monster, or unique",
                            },
                            "name": {
                                "type": "string",
                                "description": "if unique, the name of the combatant, otherwise a specific name for this type of combatant",
                            },
                            "description": {
                                "type": "string",
                                "description": "A description of the combatant, including any relevant information the GM thinks the players need to know in MARKDOWN format",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
                "loot": {
                    "type": "array",
                    "description": "A list of loot items gained in the scene, if any.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["rarity", "name", "description", "attributes"],
                        "properties": {
                            "rarity": {
                                "type": "string",
                                "enum": [
                                    "common",
                                    "uncommon",
                                    "rare",
                                    "very rare",
                                    "legendary",
                                    "artifact",
                                ],
                                "description": "The rarity of the item, such as common, uncommon, rare, very rare, legendary, or artifact",
                            },
                            "name": {
                                "type": "string",
                                "description": "A unique name for the item",
                            },
                            "description": {
                                "type": "string",
                                "description": "A physical description of the item",
                                "items": {"type": "string"},
                            },
                            "attributes": {
                                "type": "string",
                                "description": "A description of the features if any, limitations, and value of the item in MARKDOWN format",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
                "requires_roll": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "roll_required": {
                            "type": "boolean",
                            "description": "Whether or not the player's next action requires a roll",
                        },
                        "type": {
                            "type": "string",
                            "enum": [
                                "savingthrow",
                                "attack",
                                "damage",
                                "skillcheck",
                                "abilitycheck",
                                "initiative",
                                "none",
                            ],
                            "description": "The type of roll requested, such as a saving throw, attack, damage, skill check, ability check, initiative roll, or none",
                        },
                        "attribute": {
                            "type": "string",
                            "description": "If and only if the player's next action requires, a description of the attribute to roll, such as WIS, DEX, STR, Stealth, Perception, etc.",
                            "items": {"type": "string"},
                        },
                        "description": {
                            "type": "string",
                            "description": "A short description of the scenario or event that requires the roll in MARKDOWN format, including the save value, DC, or target number",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["roll_required", "type", "attribute", "description"],
                },
            },
        },
    }

    ##################### PROPERTY METHODS ####################

    @property
    def gm(self):
        if not self.agent:
            self.agent = JSONAgent(
                name=f"TableTop RPG Game Master for {self.world.name}, in a {self.world.genre} setting",
                instructions=f"""You are highly skilled and creative AI trained to act as a Game Master for a {self.world.genre} Table Top RPG. Use the uploaded file to reference the existing world objects, such as characters, creatures, items, locations, encounters, and storylines.

                Use existing world elements and their connections to expand on existing storylines or generate a new story consistent with the existing elements and timeline of the world. While the new story should be unique, there should also be appropriate connections to one or more existing elements in the world as described by the uploaded file.""",
                description=f"You are a helpful AI assistant trained to act as the Table Top Game Master for 1 or more players. You will create consistent, mysterious, and unique homebrewed {self.world.genre} stories that will challenge, surprise, and delight players. You will also ensure that your stories are consistent with the existing world as described by the uploaded file.",
            )
            self.agent.save()
            self.update_refs()
            self.save()
        return self.agent

    def update_refs(self):
        self.gm.get_client().clear_files()
        world_data = self.world.page_data()
        ref_db = json.dumps(world_data).encode("utf-8")
        self.gm.get_client().attach_file(
            ref_db, filename=f"{self.world.slug}-gm-dbdata.json"
        )
        self.save()

    def parse_scene(self, player, response):
        from models.world import World

        if scene_type := response["type"]:
            if player.autogm_summary:
                prompt = (
                    player.autogm_summary[10].summary
                    if len(player.autogm_summary) > 10
                    else ""
                )
                prompt += ". ".join(
                    ags.description for ags in player.autogm_summary[:10]
                )
                primer = "Generate a summary of less than 250 words of the following events in MARKDOWN format."
                summary = player.world.system.generate_summary(prompt, primer)
                summary = summary.replace("```markdown", "").replace("```", "")
                summary = markdown.markdown(summary)
            else:
                summary = response["description"]
            scene = AutoGMScene(
                type=scene_type,
                player=player,
                description=response["description"],
                date=response["date"],
                summary=summary,
            )
            # Split the text into paragraphs based on double newlines
            paragraphs = scene.description.split(".")

            # Wrap each paragraph to the desired width
            wrapped_paragraphs = ""
            while paragraphs:
                wrapped_paragraphs += ".".join(paragraphs[:4])
                paragraphs = paragraphs[4:] if len(paragraphs) > 4 else []

            # Join the paragraphs back together with double newlines
            scene.description = ".<br><br>".join(wrapped_paragraphs)
            if response.get("requires_roll") and response["requires_roll"].get(
                "roll_required"
            ):
                scene.roll_required = True
                scene.roll_type = response["requires_roll"].get("type")
                scene.roll_attribute = response["requires_roll"].get("attribute")
                scene.roll_description = response["requires_roll"].get("description")
            else:
                scene.roll_required = False
            scene.save()
            player.autogm_summary += [scene]
            player.save()
            AutoTasks().task(
                AutoGMScene.generate_image,
                scene.pk,
                response["image"],
            )
            scene.generate_npcs(response.get("npcs"))
            scene.generate_combatants(response.get("combatants"))
            scene.generate_loot(response.get("loot"))
            return scene

    def start(self, player, scenario=None):
        scenario = (
            scenario
            or "Build on an existing storyline or encounter from the world to surprise and challenge players' expectations."
        )
        prompt = f"As the expert AI Game Master for a new {self.world.genre} TableTop RPG session within the established world of {self.world.name}, start a new game session by describing a setting and scenario plot hook for the players in a vivid and captivating way. Incorporate the following information into the scenario:"
        prompt += f"""
            PLAYER: {player.name} [{player.pk}]
            {player.backstory_summary}

            SCENARIO: {scenario}

            IN-GAME DATE: {self.world.current_date}
        """
        log(prompt, _print=True)
        response = self.gm.generate(prompt, self._funcobj)
        return self.parse_scene(player, response)

    def run(self, player, message):
        prompt = f"""As the AI Game Master for a {self.world.genre} TTRPG session, write a description for the next event, scene, or combat round that moves the story forward for the currently running game session based on the player's message, including the roll result if present, and the previous events using the following details:

PLAYER: {player.name} [{player.pk}]
{player.backstory_summary}

PLAYER ACTIONS
{message}

PREVIOUS EVENTS SUMMARY
Current Date: {player.autogm_summary[-1].date or self.world.current_date}
{player.autogm_summary[-1].summary or player.autogm_summary[-1].description}
"""
        log(prompt, _print=True)
        response = self.gm.generate(prompt, function=self._funcobj)
        return self.parse_scene(player, response)

    def end(self, player, message):
        summary = self._summarize(player.pk)
        prompt = f"""As the AI Game Master for a {self.world.genre} TTRPG session, create a natural stopping point to end the currently running game session, including a cliffhanger scenario, based on the following details:
PLAYER: {player.name} [{player.pk}]
{player.backstory_summary}

PLAYER ACTIONS
{message}

PREVIOUS EVENTS SUMMARY
Timeline: {player.autogm_summary[0].date} - {player.autogm_summary[-1].date}
{summary}
"""
        log(prompt, _print=True)
        response = self.gm.generate(prompt, function=self._funcobj)
        return self.parse_scene(player, response)
