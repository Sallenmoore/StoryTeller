import json
import os
import random

import markdown
import requests

from autonomous import log
from autonomous.ai.audioagent import AudioAgent
from autonomous.ai.jsonagent import JSONAgent
from autonomous.model.autoattr import (
    BoolAttr,
    FileAttr,
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
    audio = FileAttr()
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))

    _music_lists = {
        "social": ["themesong.mp3"],
        "combat": [
            "battle2.mp3",
            "battle4.mp3",
            "battle3.mp3",
            "battle5.mp3",
            "skirmish4.mp3",
            "skirmish3.mp3",
            "skirmish2.mp3",
            "skirmish1.mp3",
        ],
        "exploration": ["relaxed1.mp3", "creepy1.mp3", "creepy2.mp3", "creepy3.mp3"],
        "stealth": [
            "suspense1.mp3",
            "suspense2.mp3",
            "suspense3.mp3",
            "suspense4.mp3",
            "suspense5.mp3",
            "suspense6.mp3",
            "suspense7.mp3",
        ],
    }

    def delete(self):
        if self.image:
            self.image.remove_img_file()
            self.image.delete()
        return super().delete()

    @property
    def music(self):
        return f"/static/sounds/music/{random.choice(self._music_lists.get(self.type, ["themesong.mp3"]))}"

    @classmethod
    def generate_audio(cls, pk):
        from models.world import World

        scene = cls.get(pk)
        if not scene.audio:
            voiced_scene = AudioAgent().generate(scene.description, voice="echo")
            scene.audio.put(voiced_scene, content_type="audio/mpeg")
            scene.save()

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

    def get_additional_associations(self):
        scene_objects = [self.player, *self.npcs, *self.combatants, *self.loot]
        for o in scene_objects:
            if o not in self.associations:
                self.associations += [o]
        self.save()
        associations = [o for o in self.associations if o not in scene_objects]
        return associations

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     # log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)
    #     =

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_associations()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verification methods ##################

    def pre_save_associations(self):
        self.associations.sort(key=lambda x: (x.title, x.name))


class AutoGM(AutoModel):
    world = ReferenceAttr(choices=["World"], required=True)
    agent = ReferenceAttr(choices=[JSONAgent])

    _funcobj = {
        "name": "run_scene",
        "description": "Creates a scene for TTRPG players that advances the story forward,  is consistent with the previous scene, and incorporates elements from the uploaded file describing the world.",
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
                    "description": "The GM's evocative and detailed description in MARKDOWN of a scene that drives the story forward, including any relevant information the GM thinks the players need to know",
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
                    "description": "A list of descriptions of non-combatant NPCs in the scenario, if any. For existing npcs from associations, use full names that can be matched.",
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
                    "description": "if and only if it is a combat type scene, provide a list of descriptions of combatants in the scenario, otherwise an empty list. ",
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
                                "type": "array",
                                "description": "A list of the features, limitations, and value of the item in MARKDOWN format.",
                                "items": {
                                    "type": "string",
                                    "description": "A feature, limitation, or value of the item in MARKDOWN format",
                                },
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
                associations = [player, *player.autogm_summary[-1].associations]
            else:
                summary = response["description"]
                associations = [player]
            description = (
                response["description"].replace("```markdown", "").replace("```", "")
            )
            description = markdown.markdown(description)
            scene = AutoGMScene(
                type=scene_type,
                player=player,
                description=description,
                date=player.world.current_date,
                summary=summary,
                associations=associations,
            )
            # Split the text into paragraphs based on double newlines
            paragraphs = scene.description.split(".")

            # Wrap each paragraph to the desired width
            wrapped_paragraphs = []
            while paragraphs:
                wrapped_paragraphs += [".".join(paragraphs[:4])]
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
            AutoTasks().task(AutoGMScene.generate_audio, scene.pk)
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
        prompt = f"""As the AI Game Master for a {self.world.genre} TTRPG session, write a description for the next event, scene, or combat round that moves the story forward and creates suspense or a sense of danger. The new scene should be based on and consistent with the player's message,  the previous scene events and elements described below, and the roll result if present:

ASSOCIATED WORLD ELEMENTS
{"\n- ".join([f"name: {ass.name}\n  - type: {ass.title}\n  - backstory: {ass.backstory_summary}" for ass in player.autogm_summary[-1].associations if ass != player]) if player.autogm_summary else "None yet"}

PREVIOUS EVENTS SUMMARY
{player.autogm_summary[-1].summary or player.autogm_summary[-1].description}

PLAYER
{player.name}
{player.backstory_summary}

PLAYER ACTIONS
{message}
"""
        log(prompt, _print=True)
        response = self.gm.generate(prompt, function=self._funcobj)
        return self.parse_scene(player, response)

    def end(self, player, message):
        prompt = f"""As the AI Game Master for a {self.world.genre} TTRPG session, create a natural stopping point to end the currently running game session, including a cliffhanger scenario, based on the following details:

PREVIOUS EVENTS SUMMARY
Timeline: {player.autogm_summary[0].date} - {player.autogm_summary[-1].date}
{player.autogm_summary[-1]}
PLAYER
{player.name} [{player.pk}]
{player.backstory_summary}

PLAYER ACTIONS
{message}
"""
        log(prompt, _print=True)
        response = self.gm.generate(prompt, function=self._funcobj)
        result = self.parse_scene(player, response)
        player.world.backstory += f"""

{result.summary}
"""
        player.world.save()
        for ags in player.autogm_summary:
            for assoc in ags.associations:
                assoc.add_associations(ags.associations)
        return result
