import json
import os
import random

import markdown
import requests
from bs4 import BeautifulSoup

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
    player_messages = DictAttr()
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

    def add_association(self, obj):
        if obj not in self.associations:
            self.associations += [obj]
        self.save()

    def generate_audio(self, voice=None):
        from models.world import World

        soup = BeautifulSoup(self.description, "html.parser")
        description = soup.get_text()
        voiced_scene = AudioAgent().generate(description, voice=voice)
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
            first_name = obj["name"].split()[0]
            last_name = obj["name"].split()[-1]
            npc = [
                c
                for c in Character.search(world=self.party.world, name=first_name)
                if last_name in c.name
            ]
            char = npc[0] if npc else []
            if not char:
                char = Character(
                    world=self.party.world,
                    race=obj["species"],
                    name=obj["name"],
                    desc=obj["description"],
                    backstory=obj["backstory"],
                )
                char.save()
                if char not in self.party.players:
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
            char = Creature.find(world=self.party.world, name=obj["name"])

            if not char:
                char = Creature(
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
            char = Item.find(world=self.party.world, name=obj["name"])

            if not char:
                char = Item(
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
            char = Model.find(world=self.party.world, name=obj["name"])
            if not char:
                char = Model(
                    world=self.party.world,
                    name=obj["name"],
                    desc=obj["description"],
                    backstory=obj["backstory"],
                )
                char.save()
                self.places += [char]
                self.save()
                resp = requests.post(
                    f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
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
    voice = StringAttr(default="echo")

    _funcobj = {
        "name": "run_scene",
        "description": "Creates a TTRPG scene that advances the story, maintains narrative consistency, and integrates elements from the uploaded world file.",
        "parameters": {
            "type": "object",
            "properties": {
                "scene_type": {
                    "type": "string",
                    "enum": ["social", "combat", "exploration", "stealth"],
                    "description": "Type of scene to generate (e.g., social, combat, exploration, or stealth).",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed Markdown description of the scene, driving the story forward and providing relevant information.",
                },
                "image": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["description", "imgtype"],
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the scene for image generation.",
                        },
                        "imgtype": {
                            "type": "string",
                            "enum": ["scene", "map"],
                            "description": "Specifies whether the image is a scene or a map.",
                        },
                    },
                },
                "player": {
                    "type": "string",
                    "description": "Name of the active player, or blank if not specific to any player.",
                },
                "npcs": {
                    "type": "array",
                    "description": "List of non-combatant NPCs, including details for interaction or lore.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["species", "name", "description", "backstory"],
                        "properties": {
                            "species": {
                                "type": "string",
                                "description": "NPC species (e.g., human, elf).",
                            },
                            "name": {
                                "type": "string",
                                "description": "Unique name for the NPC.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Markdown description of NPC's appearance.",
                            },
                            "backstory": {
                                "type": "string",
                                "description": "Markdown description of the NPC's history and motivations.",
                            },
                        },
                    },
                },
                "combatants": {
                    "type": "array",
                    "description": "List of combatants for combat scenes, or empty for other scene types.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["combatant_type", "name", "description"],
                        "properties": {
                            "combatant_type": {
                                "type": "string",
                                "enum": ["humanoid", "animal", "monster", "unique"],
                                "description": "Combatant type (e.g., humanoid, monster).",
                            },
                            "name": {
                                "type": "string",
                                "description": "Name of the combatant.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Markdown description of the combatant's appearance and behavior.",
                            },
                        },
                    },
                },
                "places": {
                    "type": "array",
                    "description": "List of locations relevant to the scenario, or empty if none.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "location_type",
                            "name",
                            "description",
                            "backstory",
                        ],
                        "properties": {
                            "location_type": {
                                "type": "string",
                                "enum": ["region", "city", "district", "poi"],
                                "description": "Type of location (e.g., city, point of interest).",
                            },
                            "name": {
                                "type": "string",
                                "description": "Unique name for the location.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Markdown description of the location's appearance.",
                            },
                            "backstory": {
                                "type": "string",
                                "description": "Publicly known history of the location in Markdown.",
                            },
                        },
                    },
                },
                "loot": {
                    "type": "array",
                    "description": "List of loot items discovered in the scene, or empty if none.",
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
                                "description": "Rarity of the loot item.",
                            },
                            "name": {
                                "type": "string",
                                "description": "Unique name for the item.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Markdown description of the item's appearance.",
                            },
                            "attributes": {
                                "type": "array",
                                "description": "Markdown list of item's features, limitations, or value.",
                                "items": {"type": "string"},
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
                            "description": "Whether a roll is required for the player's next action.",
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
                            "description": "Type of roll needed.",
                        },
                        "attribute": {
                            "type": "string",
                            "description": "Attribute to roll against (e.g., WIS, DEX, Stealth).",
                        },
                        "description": {
                            "type": "string",
                            "description": "Markdown description of the event requiring a roll.",
                        },
                    },
                },
                "quest_log": {
                    "type": "array",
                    "description": "List of plot points, quests, or objectives for the players.",
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
                                "description": "Quest or objective name.",
                            },
                            "type": {
                                "type": "string",
                                "enum": [
                                    "main quest",
                                    "side quest",
                                    "optional objective",
                                ],
                                "description": "Type of quest or objective.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Markdown description of the quest or objective.",
                            },
                            "importance": {
                                "type": "string",
                                "description": "Connection to the overarching story.",
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
                                "description": "Current status of the quest.",
                            },
                            "next_steps": {
                                "type": "string",
                                "description": "Markdown description of actions to advance the objective.",
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

        if scene_type := response["scene_type"]:
            summary = response["description"]
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
            description = (
                response["description"].replace("```markdown", "").replace("```", "")
            )
            description = markdown.markdown(description)

            associations = []
            if party.last_scene:
                for ass in [*party.players, *party.last_scene.associations]:
                    if ass not in associations:
                        associations += [ass]

            scene = AutoGMScene(
                type=scene_type,
                party=party,
                description=description,
                date=party.current_date,
                summary=summary,
                associations=associations,
            )
            scene.save()

            if party.last_scene:
                scene.current_quest = party.last_scene.current_quest
                scene.quest_log = party.last_scene.quest_log
                scene.save()

            for q in response.get("quest_log", []):
                try:
                    quest = [
                        quest
                        for quest in party.last_scene.quest_log
                        if quest.name == q["name"]
                    ].pop(0)
                    quest.description = q["description"]
                    quest.importance = q.get("importance")
                    quest.status = q["status"]
                    quest.next_steps = q["next_steps"]
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
            scene.generate_audio(voice="onyx")
            party.autogm_summary += [scene]
            party.save()
            scene.generate_npcs(response.get("npcs"))
            scene.generate_combatants(response.get("combatants"))
            scene.generate_loot(response.get("loot"))
            scene.generate_places(response.get("places"))
            for ags in party.autogm_summary:
                for assoc in [
                    *ags.npcs,
                    *ags.loot,
                    *ags.combatants,
                    *ags.places,
                    *ags.associations,
                ]:
                    assoc.add_associations(ags.associations)

            self.update_refs()
            return scene

    def start(self, party, scenario=None):
        if party.autogm_summary:
            self.end(party)
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
        prompt = f"""You are an expert AI Game Master for a {self.world.genre} tabletop roleplaying game. Your task is to craft an evocative and immersive description for the next event, scene, or combat round that moves the story forward in surprising yet logical ways. The scene should:
- Build suspense, tension, or excitement.
- Incorporate elements from the player's most recent message, past events, and established lore.
- Reflect the player's self-described actions and intentions.
- Be influenced by any provided roll results or narrative outcomes.
- Remain consistent with the tone and pacing of the game.

Provide your response in a way that:
1. Evokes vivid imagery and atmosphere.
2. Introduces unexpected challenges or opportunities to keep the players engaged.
3. Clearly outlines the consequences or setup for player actions, leaving room for creative responses.

PREVIOUS EVENTS SUMMARY
{party.last_scene.summary or party.last_scene.description}

STORY ELEMENTS
{"\n- ".join([f"name: {ass.name}\n  - type: {ass.title}\n  - backstory: {ass.backstory_summary}" for ass in party.last_scene.associations if ass not in party.players]) if party.autogm_summary else "None yet"}

PARTY
{"".join([f"\n- {pc.name} : {pc.backstory_summary}\n" for pc in party.players])}

PLAYER'S ACTIONS
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

    def end(self, party):
        prompt = f"""You are an expert AI Game Master for a {party.genre} TTRPG campaign, create a natural stopping point to end the currently running game session, including a cliffhanger scenario, based on the following details:

{f"Timeline: {party.autogm_summary[0].date} - {party.last_scene.date}" if party.autogm_summary else ""}

CAMPAIGN SUMMARY
{party.last_scene.summary}

PREVIOUS EVENTS
{party.last_scene.description}

PARTY
{"".join([f"\n- {pc.name} : {pc.backstory_summary}\n" for pc in party.characters])}
"""
        log(prompt, _print=True)
        self._update_response_function(party)
        response = self.gm.generate(prompt, function=self._funcobj)
        scene = self.parse_scene(party, response)
        scene.save()
        for p in [party, party.world, *party.players]:
            p.backstory += f"""

{scene.summary}
"""
            p.save()
        party.autogm_history += party.autogm_summary
        party.autogm_summary = []
        party.save()
        return scene

    def rungm(
        self,
        party,
        description,
        scene_type,
        npcs=[],
        combatants=[],
        loot=[],
        places=[],
        date=None,
    ):
        summary = description
        if party.autogm_summary:
            prompt = (
                party.autogm_summary[10].summary
                if len(party.autogm_summary) > 10
                else ""
            )
            prompt += ". ".join(ags.description for ags in party.autogm_summary[:10])
            primer = "Generate a summary of less than 250 words of the following events in MARKDOWN format."
            summary = party.system.generate_summary(prompt, primer)
            summary = summary.replace("```markdown", "").replace("```", "")
            summary = markdown.markdown(summary)
        date = (
            date or (party.last_scene and party.last_scene.date) or party.current_date,
        )
        scene = AutoGMScene(
            type=scene_type,
            party=party,
            description=description,
            summary=summary,
            date=date,
            npcs=npcs,
            combatants=combatants,
            loot=loot,
            places=places,
        )
        if party.last_scene:
            scene.current_quest = party.last_scene.current_quest
            scene.quest_log = party.last_scene.quest_log

        elements = [*npcs, *combatants, *loot, *places]
        associations = (party.last_scene and party.last_scene.associations) or []
        associations = list(set([*associations, *elements, *party.players]))
        for o in associations:
            scene.add_association(o)
        scene.save()
        party.autogm_summary += [scene]
        party.save()
        prompt = f"""As one of the the AI Player Characters for a TTRPG campaign, your task is to respond to the GM's described scene as the character described below in a way that is consistent with the character's description, previous campaign events, and the world described by the uploaded file.

CAMPAIGN SUMMARY
{party.last_scene.summary or "The campaign has just begun."}

STORY ELEMENTS
{"\n- ".join([f"name: {ass.name}\n  - type: {ass.title}\n  - backstory: {ass.backstory_summary}" for ass in elements if ass not in party.players]) if party.autogm_summary else "None yet"}

PARTY
{"".join([f"\n- {pc.name} : {pc.backstory_summary}\n" for pc in party.characters])}

SCENE
{party.last_scene.description}
"""
        pc_prompt = ""
        for pc in party.players:
            pc_prompt = f"""

CHARACTER DESCRIPTION
- Name: {pc.name}
- Species: {pc.species}
- Gender: {pc.gender}
- Age: {pc.age}
- Occupation: {pc.occupation}
- Goal: {pc.goal}
- Backstory: {pc.backstory}
"""
            response = self.gm.generate(pc_prompt)
            scene.player_messages[pc.pk] = response
            scene.save()
