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
    DictAttr,
    FileAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.images.image import Image
from models.ttrpgobject.character import Character
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.item import Item


class AutoGMQuest(AutoModel):
    name = StringAttr()
    type = StringAttr(choices=["main quest", "side quest", "optional objective"])
    description = StringAttr()
    status = StringAttr(
        choices=["unknown", "rumored", "active", "completed", "failed", "abandoned"],
        default="unknown",
    )
    next_steps = StringAttr()
    importance = StringAttr()
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))


class AutoGMScene(AutoModel):
    type = StringAttr(choices=["social", "combat", "exploration", "stealth"])
    description = StringAttr()
    summary = StringAttr()
    date = StringAttr()
    player_messages = ListAttr(DictAttr())
    party = ReferenceAttr(choices=["Faction"])
    npcs = ListAttr(ReferenceAttr(choices=["Character"]))
    combatants = ListAttr(ReferenceAttr(choices=["Creature"]))
    loot = ListAttr(ReferenceAttr(choices=["Item"]))
    places = ListAttr(ReferenceAttr(choices=["Place"]))
    roll_required = BoolAttr()
    roll_type = StringAttr()
    roll_attribute = StringAttr()
    roll_description = StringAttr()
    roll_formula = StringAttr()
    roll_result = IntAttr()
    image = ReferenceAttr(choices=[Image])
    audio = FileAttr()
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    current_quest = ReferenceAttr(choices=[AutoGMQuest])
    quest_log = ListAttr(ReferenceAttr(choices=[AutoGMQuest]))

    def delete(self):
        if self.image:
            self.image.delete()
        return super().delete()

    @property
    def music(self):
        return self.party.system.get_music(self.type)

    @property
    def player(self):
        members = self.party.characters
        return members[0] if members else None

    def update_description(self, description):
        log(description, description != self.description)
        if description and description != self.description:
            self.description = description
            self.save()
            requests.post(
                f"http://tasks:{os.environ.get('COMM_PORT')}/generate/audio/{self.pk}"
            )

    def generate_audio(self):
        from models.world import World

        voiced_scene = AudioAgent().generate(self.description, voice="echo")
        if self.audio:
            self.audio.delete()
            self.audio.replace(voiced_scene, content_type="audio/mpeg")
        else:
            self.audio.put(voiced_scene, content_type="audio/mpeg")
        self.save()

    def generate_image(self, image_prompt):
        from models.world import World

        desc = f"""Based on the below description of characters, setting, and events in a scene of a {self.party.genre} TTRPG session, generate a single comic book style panel in the style of {random.choice(['Dan Mora', 'Laura Braga', 'Clay Mann', 'Jorge Jiménez' ])} for the scene.

DESCRIPTION OF CHARACTERS IN THE SCENE
"""

        for char in self.party.characters:
            desc += f"""
-{char.age} year old {char.gender} {char.occupation}. {char.description_summary or char.description}
    - Motif: {char.motif}
"""
        desc += f"""
SCENE DESCRIPTION
{image_prompt['description']}
"""
        img = Image.generate(
            desc,
            tags=[
                image_prompt["imgtype"],
                "scene",
                self.party.name,
                self.party.world.name,
                self.party.genre,
            ],
        )
        img.save()
        self.image = img
        self.save()

    def get_npcs(self):
        return [c for c in self.npcs if c not in self.party.characters]

    def generate_npcs(self, objs):
        if not objs:
            return
        for obj in objs:
            char = Character.find(
                world=self.party.world, name=obj["name"]
            ) or Character(
                world=self.party.world,
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
        return self.npcs

    def generate_combatants(self, objs):
        if not objs:
            return
        for obj in objs:
            char = Creature.find(world=self.party.world, name=obj["name"]) or Creature(
                world=self.party.world,
                type=obj["combatant_type"],
                name=obj["name"],
                desc=obj["description"],
            )
            char.save()
            self.combatants += [char]
            self.save()
            resp = requests.post(
                f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
            )
        return self.combatants

    def generate_loot(self, objs):
        if not objs:
            return
        for obj in objs:
            char = Item.find(world=self.party.world, name=obj["name"]) or Item(
                world=self.party.world,
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
        return self.loot

    def generate_places(self, objs):
        from models.world import World

        if not objs:
            return
        for obj in objs:
            for key, val in self.party.system._titles.items():
                if val.lower() == obj["location_type"].lower():
                    Model = AutoModel.load_model(key)
            obj = Model.find(world=self.party.world, name=obj["name"]) or Model(
                world=self.party.world,
                name=obj["name"],
                desc=obj["description"],
                backstory=obj["backstory"],
            )
            obj.save()
            self.places += [obj]
            self.save()
            resp = requests.post(
                f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{obj.path}"
            )
        return self.places

    def get_additional_associations(self):
        """
        Retrieves additional associations that are not part of the current scene objects.
        This method first combines all scene objects from the party, NPCs, combatants, and loot.
        It then checks if each object is already in the associations list, and if not, adds it.
        Finally, it saves the updated associations and returns a list of associations that are not part of the scene objects.
        Returns:
            list: A list of associations that are not part of the current scene objects.
        """

        scene_objects = [
            *self.party.characters,
            *self.npcs,
            *self.combatants,
            *self.loot,
            *self.places,
        ]
        for o in scene_objects:
            if o not in self.associations:
                self.associations += [o]
        self.save()
        return [o for o in self.associations if o not in scene_objects]

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
        "description": "Creates a scene for TTRPG players that advances the story forward, is consistent with the previous scene, and incorporates elements from the uploaded file describing the world.",
        "parameters": {
            "type": "object",
            "properties": {
                "scene_type": {
                    "type": "string",
                    "enum": ["social", "combat", "exploration", "stealth"],
                    "description": "The type of scene, such as social, combat, exploration, or clandestine.",
                },
                "description": {
                    "type": "string",
                    "description": "The GM's evocative and detailed description in MARKDOWN of a scene that drives the current scenario forward and includes any relevant information the GM thinks the players need to know.",
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
                    "description": "The full name of the player the GM is currently interacting with or blank if not directed at a specific player.",
                },
                "npcs": {
                    "type": "array",
                    "description": "A list of descriptions of non-combatant NPCs in the scenario, if any. For existing NPCs from associations, use full names that can be matched.",
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
                                "description": "A unique name for the NPC.",
                            },
                            "description": {
                                "type": "string",
                                "description": "A description of the physical appearance of the NPC detailed enough to generate an image.",
                            },
                            "backstory": {
                                "type": "string",
                                "description": "The NPC's backstory or history, including any relevant information the GM thinks the players need to know in MARKDOWN format.",
                            },
                        },
                    },
                },
                "combatants": {
                    "type": "array",
                    "description": "If and only if it is a combat type scene, provide a list of descriptions of combatants in the scenario, otherwise an empty list.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["combatant_type", "name", "description"],
                        "properties": {
                            "combatant_type": {
                                "type": "string",
                                "enum": ["humanoid", "animal", "monster", "unique"],
                                "description": "The type of combatant, such as humanoid, animal, monster, or unique.",
                            },
                            "name": {
                                "type": "string",
                                "description": "If unique, the name of the combatant, otherwise a specific name for this type of combatant.",
                            },
                            "description": {
                                "type": "string",
                                "description": "A description of the combatant, including any relevant information the GM thinks the players need to know in MARKDOWN format.",
                            },
                        },
                    },
                },
                "places": {
                    "type": "array",
                    "description": "A list of locations, such as a region, city, district, or point of interest (poi), related to the scenario, if any, otherwise an empty list.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "location_type",
                            "name",
                            "backstory",
                            "description",
                        ],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "A unique name for the location.",
                            },
                            "location_type": {
                                "type": "string",
                                "enum": ["region", "city", "district", "poi"],
                                "description": "The kind of location, such as a region, city, district, or point of interest (poi).",
                            },
                            "backstory": {
                                "type": "string",
                                "description": "The publicly known history of the location.",
                            },
                            "description": {
                                "type": "string",
                                "description": "A physical description of the location.",
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
                                "description": "The rarity of the item, such as common, uncommon, rare, very rare, legendary, or artifact.",
                            },
                            "name": {
                                "type": "string",
                                "description": "A unique name for the item.",
                            },
                            "description": {
                                "type": "string",
                                "description": "A physical description of the item.",
                            },
                            "attributes": {
                                "type": "array",
                                "description": "A list of the features, limitations, and value of the item in MARKDOWN format.",
                                "items": {
                                    "type": "string",
                                    "description": "A feature, limitation, or value of the item in MARKDOWN format.",
                                },
                            },
                        },
                    },
                },
                "requires_roll": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["roll_required", "type", "attribute", "description"],
                    "properties": {
                        "roll_required": {
                            "type": "boolean",
                            "description": "Whether or not the player's next action requires a roll.",
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
                            "description": "The type of roll requested, such as a saving throw, attack, damage, skill check, ability check, initiative roll, or none.",
                        },
                        "attribute": {
                            "type": "string",
                            "description": "A description of the attribute to roll, such as WIS, DEX, STR, Stealth, Perception, etc.",
                        },
                        "description": {
                            "type": "string",
                            "description": "A short description of the scenario or event that requires the roll in MARKDOWN format.",
                        },
                    },
                },
                "quest_log": {
                    "type": "array",
                    "description": "A list of plot points, side quests, and objectives that the players can choose to pursue, delay, or ignore.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "name",
                            "type",
                            "description",
                            "importance",
                            "status",
                            "next_steps",
                        ],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The name of the quest or objective.",
                            },
                            "type": {
                                "type": "string",
                                "enum": [
                                    "main quest",
                                    "side quest",
                                    "optional objective",
                                ],
                                "description": "The type of quest or objective, such as main quest, side quest, or optional objective.",
                            },
                            "description": {
                                "type": "string",
                                "description": "A description of the quest or objective in MARKDOWN format.",
                            },
                            "importance": {
                                "type": "string",
                                "description": "A description of how the quest or objective connects to and advances the story.",
                            },
                            "status": {
                                "type": "string",
                                "enum": [
                                    "rumored",
                                    "active",
                                    "completed",
                                    "failed",
                                    "abandoned",
                                ],
                                "description": "The current status of the quest or objective.",
                            },
                            "next_steps": {
                                "type": "string",
                                "description": "A description of the next set of possible actions that players can take to advance the objective.",
                            },
                        },
                    },
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
                instructions=f"""You are highly skilled and creative AI trained to act as a Game Master for a {self.world.genre} TableTop RPG. Use the uploaded file to reference the existing world objects, such as characters, creatures, items, locations, encounters, and storylines.

                Use existing world elements and their connections to expand on existing storylines or generate a new story consistent with the existing elements and timeline of the world. While the new story should be unique, there should also be appropriate connections to one or more existing elements in the world as described by the uploaded file.""",
                description=f"You are a helpful AI assistant trained to act as the Table Top Game Master for 1 or more players. You will create consistent, mysterious, and unique homebrewed {self.world.genre} stories that will challenge, surprise, and delight players. You will also ensure that your stories are consistent with the existing world as described by the uploaded file.",
            )
            self.agent.save()
            self.update_refs()
            self.save()
        return self.agent

    def _update_response_function(self, party):
        region_str = party.system._titles["region"].lower()
        city_str = party.system._titles["city"].lower()
        district_str = party.system._titles["district"].lower()
        location_str = party.system._titles["location"].lower()
        self._funcobj["parameters"]["properties"]["places"]["items"]["properties"][
            "location_type"
        ] |= {
            "enum": [
                region_str,
                city_str,
                district_str,
                location_str,
            ],
            "description": f"The kind of location, such as a {region_str}, {city_str}, {district_str}, or specific {location_str} or landmark.",
        }
        log(self._funcobj, _print=True)

    def update_refs(self):
        self.gm.get_client().clear_files()
        world_data = self.world.page_data()
        ref_db = json.dumps(world_data).encode("utf-8")
        self.gm.get_client().attach_file(
            ref_db, filename=f"{self.world.slug}-gm-dbdata.json"
        )
        self.save()

    def parse_scene(self, party, response):
        from models.world import World

        if scene_type := response["type"]:
            if party.autogm_summary:
                prompt = (
                    party.autogm_summary[10].summary
                    if len(party.autogm_summary) > 10
                    else ""
                )
                prompt += ". ".join(
                    ags.description for ags in party.autogm_summary[:10]
                )
                primer = "Generate a summary of less than 250 words of the following events in MARKDOWN format."
                summary = party.world.system.generate_summary(prompt, primer)
                summary = summary.replace("```markdown", "").replace("```", "")
                summary = markdown.markdown(summary)
            else:
                summary = response["description"]
            description = (
                response["description"].replace("```markdown", "").replace("```", "")
            )
            associations = party.characters + (
                party.autogm_summary[-1].associations if party.autogm_summary else []
            )
            description = markdown.markdown(description)
            scene = AutoGMScene(
                type=scene_type,
                party=party,
                description=description,
                date=party.current_date,
                summary=summary,
                associations=associations,
            )
            scene.save()

            if len(party.autogm_summary) > 2:
                scene.current_quest = party.autogm_summary[-1].current_quest
                scene.quest_log = party.autogm_summary[-1].quest_log
            for q in response.get("quest_log", []):
                try:
                    quest = [
                        quest
                        for quest in party.autogm_summary[-1].quest_log
                        if quest.name == q["name"]
                    ].pop(0)
                except IndexError:
                    quest = AutoGMQuest(
                        name=q["name"],
                        type=q["type"],
                        description=q["description"],
                        status=q["status"],
                        next_steps=q["next_steps"],
                        importance=q.get("importance"),
                    )
                    scene.quest_log += [quest]
                else:
                    quest.status = q["status"]
                    quest.next_steps = q["next_steps"]
                quest.save()
            scene.save()

            # handle rolls
            if response.get("requires_roll") and response["requires_roll"].get(
                "roll_required"
            ):
                scene.roll_required = True
                scene.roll_type = response["requires_roll"].get("type")
                scene.roll_attribute = response["requires_roll"].get("attribute")
                scene.roll_description = response["requires_roll"].get("description")
            else:
                scene.roll_required = False
            scene.generate_image(response["image"])
            scene.generate_audio()
            party.autogm_summary += [scene]
            party.save()
            scene.generate_npcs(response.get("npcs"))
            scene.generate_combatants(response.get("combatants"))
            scene.generate_loot(response.get("loot"))
            scene.generate_places(response.get("places"))
            for ags in party.autogm_summary:
                for assoc in ags.associations:
                    assoc.add_associations(ags.associations)

            self.update_refs()
            return scene

    def start(self, party, scenario=None):
        scenario = (
            scenario
            or "Build on an existing storyline or encounter from the world to surprise and challenge players' expectations."
        )
        prompt = f"You are an expert AI Game Master for a new {self.world.genre} TableTop RPG campaign within the established world of {self.world.name}, described in the uploaded file. Your job is to start the first session by describing the world, campaign setting, and a plot hook for the players in a vivid and captivating way. The first session should also explain what brought these characters together and what their initial goal is. The party consists of the following characters:"
        for pc in party.players:
            prompt += f"""
        PARTY MEMBER: {pc.name} [{pc.pk}]
        {pc.backstory_summary}
"""
        prompt += f"""

            SCENARIO: {scenario}

            IN-GAME DATE: {party.current_date}
"""
        self._update_response_function(party)
        response = self.gm.generate(prompt, self._funcobj)
        scene = self.parse_scene(party, response)
        scene.save()
        return scene

    def run(self, party, message):
        prompt = f"""You are an expert AI Game Master for a {self.world.genre} TTRPG campaign, write a description for the next event, scene, or combat round that moves the story forward and creates suspense or a sense of danger. The new scene should be based on and consistent with the player's message, the previous events, associated elements, the players self-described actions, and the roll result if present:

PREVIOUS EVENTS SUMMARY
{party.autogm_summary[-1].summary or party.autogm_summary[-1].description}

ASSOCIATED WORLD ELEMENTS
{"\n- ".join([f"name: {ass.name}\n  - type: {ass.title}\n  - backstory: {ass.backstory_summary}" for ass in party.autogm_summary[-1].associations if ass not in party.characters]) if party.autogm_summary else "None yet"}

PARTY
{"".join([f"\n- {pc.name} : {pc.backstory_summary}\n" for pc in party.players])}

PLAYERS ACTIONS
{message}
"""
        log(prompt, _print=True)
        self._update_response_function(party)
        response = self.gm.generate(prompt, function=self._funcobj)
        scene = self.parse_scene(party, response)
        scene.save()
        return scene

    def regenerate(self, party, message):
        if party.autogm_summary:
            redo = party.autogm_summary.pop(-1)
            redo.delete()
        return (
            self.run(party, message)
            if party.autogm_summary
            else self.start(party, message)
        )

    def end(self, party, message):
        prompt = f"""You are an expert AI Game Master for a {party.genre} TTRPG campaign, create a natural stopping point to end the currently running game session, including a cliffhanger scenario, based on the following details:

{f"Timeline: {party.autogm_summary[0].date} - {party.last_scene.date}" if party.autogm_summary else ""}

CAMPAIGN SUMMARY
{party.last_scene.summary}

PREVIOUS EVENTS
{party.last_scene.description}

PARTY
{"".join([f"\n- {pc.name} : {pc.backstory_summary}\n" for pc in party.characters])}

PLAYERS ACTIONS
{message}
"""
        log(prompt, _print=True)
        self._update_response_function(party)
        response = self.gm.generate(prompt, function=self._funcobj)
        scene = self.parse_scene(party, response)
        scene.save()
        for p in [party, party.world, *party.characters]:
            p.backstory += f"""

{scene.summary}
"""
            p.save()
        return scene
