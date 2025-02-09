import json
import os
import random
import re

import markdown
import requests
from bs4 import BeautifulSoup

from autonomous import log
from autonomous.model.autoattr import (
    FileAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.base.ttrpgbase import TTRPGBase
from models.campaign.scenenote import SceneNote
from models.ttrpgobject.district import District
from models.ttrpgobject.location import Location


class Episode(AutoModel):
    name = StringAttr(default="")
    episode_num = IntAttr(default=0)
    description = StringAttr(default="")
    scenenotes = ListAttr(ReferenceAttr(choices=[SceneNote]))
    start_date = StringAttr(default="")
    end_date = StringAttr(default="")
    campaign = ReferenceAttr(choices=["Campaign"], required=True)
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    episode_report = StringAttr(default="")
    outline = ListAttr(ReferenceAttr(choices=["SceneNote"]))
    summary = StringAttr(default="")
    images = ListAttr(ReferenceAttr(choices=["Image"]))

    _outline_funcobj = {
        "name": "generate_session_outline",
        "description": "generates a session outline for a Table Top RPG with characters, items, and scenes",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the session",
                },
                "description": {
                    "type": "string",
                    "description": "A brief overview of the session, it's story arc, and the general theme.",
                },
                "plot_outline": {
                    "type": "array",
                    "description": "Create an outline breakdown for a main storyline with at least 5 acts, modeled after the 5 room dungeon. Mention major twists and opportunities.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "name",
                            "act",
                            "scene",
                            "scenario",
                            "description",
                            "type",
                            "music",
                            "allies",
                            "antagonists",
                            "places",
                            "items",
                        ],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the scene.",
                            },
                            "act": {
                                "type": "integer",
                                "description": "The Act Number",
                            },
                            "scene": {
                                "type": "integer",
                                "description": "The Scene Number",
                            },
                            "scenario": {
                                "type": "string",
                                "description": "A detailed description of the scene's scenario.",
                            },
                            "description": {
                                "type": "string",
                                "description": "A physical description of the scene that could be used to generate an image, including characters involved in the scene.",
                            },
                            "type": {
                                "type": "string",
                                "enum": [
                                    "social",
                                    "encounter",
                                    "combat",
                                    "investigation",
                                    "exploration",
                                    "stealth",
                                    "puzzle",
                                ],
                                "description": "Type of scene to generate (e.g., social, combat, encounter, exploration, investigation, puzzle, or stealth).",
                            },
                            "music": {
                                "type": "string",
                                "enum": [
                                    "battle",
                                    "suspense",
                                    "celebratory",
                                    "restful",
                                    "creepy",
                                    "relaxed",
                                    "skirmish",
                                    "themesong",
                                ],
                                "description": "Type of music appropriate for the scene (e.g., battle, suspense, celebratory, restful, creepy, relaxed, skirmish, or themesong)",
                            },
                            "allies": {
                                "type": "array",
                                "description": "List of allied NPCs involved in the scene, including details for interaction or lore.",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": [
                                        "species",
                                        "name",
                                        "description",
                                        "backstory",
                                    ],
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
                            "antagonists": {
                                "type": "array",
                                "description": "List of antagonists involved in the scene, including details for interaction or lore.",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": [
                                        "combatant_type",
                                        "name",
                                        "description",
                                    ],
                                    "properties": {
                                        "combatant_type": {
                                            "type": "string",
                                            "enum": [
                                                "humanoid",
                                                "animal",
                                                "monster",
                                                "unique",
                                            ],
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
                                "description": "List of locations relevant to the scene.",
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
                                            "enum": [
                                                "region",
                                                "city",
                                                "district",
                                                "poi",
                                            ],
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
                            "items": {
                                "type": "array",
                                "description": "List of items  involved in the scene, including details for interaction or lore, or empty if None.",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": [
                                        "rarity",
                                        "name",
                                        "description",
                                        "attributes",
                                    ],
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
                        },
                    },
                },
            },
        },
    }

    ##################### PROPERTY METHODS ####################

    @property
    def actors(self):
        return [*self.characters, *self.creatures]

    @property
    def characters(self):
        return [a for a in self.associations if a.model_name() == "Character"]

    @property
    def creatures(self):
        return [a for a in self.associations if a.model_name() == "Creature"]

    @property
    def encounters(self):
        return [a for a in self.associations if a.model_name() == "Encounter"]

    @property
    def factions(self):
        return [a for a in self.associations if a.model_name() == "Faction"]

    @property
    def genre(self):
        return self.world.genre

    @property
    def items(self):
        return [a for a in self.associations if a.model_name() == "Item"]

    @property
    def districts(self):
        return [a for a in self.associations if a.model_name() == "District"]

    @property
    def players(self):
        return [a for a in self.characters if a.is_player]

    @property
    def locations(self):
        return [a for a in self.associations if a.model_name() == "Location"]

    @property
    def cities(self):
        return [a for a in self.associations if a.model_name() == "City"]

    @property
    def places(self):
        return [a for a in [*self.scenes, *self.cities, *self.regions]]

    @property
    def regions(self):
        return [a for a in self.associations if a.model_name() == "Region"]

    @property
    def vehicles(self):
        return [a for a in self.associations if a.model_name() == "Vehicle"]

    @property
    def scenes(self):
        return [
            a for a in self.associations if a.model_name() in ["Location", "District"]
        ]

    @property
    def music_choices(self):
        return json.load(open("static/sounds/music.json"))

    @property
    def world(self):
        # IMPORTANT: this is here to register the model
        # without it, the model may not have been registered yet and it will fail
        from models.world import World

        return self.campaign.world

    ##################### INSTANCE METHODS ####################
    def resummarize(self):
        self.summary = (
            self.world.system.generate_summary(
                self.episode_report,
                primer="Generate a summary of less than 100 words of the episode events in MARKDOWN format with a paragraph breaks where appropriate, but after no more than 4 sentences.",
            )
            if len(self.episode_report) > 256
            else self.episode_report
        )
        self.summary = self.summary.replace("```markdown", "").replace("```", "")
        self.summary = (
            markdown.markdown(self.summary).replace("h1>", "h3>").replace("h2>", "h3>")
        )
        self.save()
        return self.summary

    def get_scene(self, pk):
        return Location.get(pk) or District.get(pk)

    def set_as_current(self):
        self.campaign.current_episode = self
        self.campaign.save()
        return self.campaign

    def add_association(self, obj):
        if not obj:
            raise ValueError("obj must be a valid object")
        if obj not in self.associations:
            self.associations += [obj]
            self.save()
            obj.save()
        return obj

    def add_scene_note(self, name=None):
        num = len(self.scenenotes) + 1
        if not name:
            name = f"Episode {len(self.scenenotes)}:"
        scenenote = SceneNote(name=name, num=num)
        scenenote.actors += self.players
        scenenote.save()
        self.scenenotes += [scenenote]
        self.save()
        return scenenote

    def generate_gn(self):
        for scene in self.scenenotes:
            scene.generate_image()

    def remove_association(self, obj):
        self.associations = [a for a in self.associations if a != obj]
        self.save()

    def generate_outline(self):
        prompt = f"""Generate a complete and full Tabletop RPG session outline with a clear story arc of events in valid JSON. Create a main storyline with at least 5 ACTS, that mirror the 5 room dungeon structure. Include a villain or antagonist with a detailed goal and a network of supporting antagonists.

 In addition, use the information provided in the uploaded file to connect elements to the existing {self.genre} world. Each Scene in the outline should include the following details:

DESCRIPTION

- Description of the scene, including any relevant plot points in the scene
- Mention major twists and opportunities for character development.
"""
        description = BeautifulSoup(self.description, "html.parser").get_text()
        prompt += f"""
{f"CURRENT SCENARIO\n\n{description}" if description else ""}

PARTY

- The party members include:
  - {"\n  - ".join([f"{c.name}: {BeautifulSoup(c.backstory_summary, 'html.parser').get_text()}" for c in self.players])}

ADDITIONAL CHARACTERS

- Incorporate the following characters into the story:
  - {"\n  - ".join([f"{c.name}: {BeautifulSoup(c.backstory_summary, 'html.parser').get_text()}" for c in self.characters if c not in self.players])}
  - {"\n  - ".join([f"{c.name}: {BeautifulSoup(c.backstory_summary, 'html.parser').get_text()}" for c in self.creatures])}
- For each scene, describe any NPCs in the scene, including allies, neutral parties, and foes for each scene.
  - Provide brief backstories, motivations, and potential interactions with the players.


ITEMS

- Incorporate the following items:
  - {"\n  - ".join([f"{c.name}: {BeautifulSoup(c.backstory_summary, 'html.parser').get_text()}" for c in self.items])}
- For each scene, describe key magical, technological, or significant items available in the scene.
  - Include their origins, powers, and any consequences or risks associated with their use.
  - Mention how players might obtain or interact with these items.


LOCATION:

- Incorporate the following places:
  - {"\n  - ".join([f"{c.name}: {BeautifulSoup(c.backstory_summary, 'html.parser').get_text()}" for c in self.places])}
- For each scene, describe the location where the scene unfolds.
  - Describe the location’s key features, cultural aspects, and role in the story.
  - Include at least one central hub or recurring area where players can regroup and gather resources.


The session outline should be consistent with the world described in the uploaded file, incorporating its themes, factions, geography, and unique elements. Make the storyline and details flexible enough to allow player choices to influence the narrative direction.
"""

        primer = f"""
# AI Primer: Understanding the World

**1. Genre and Themes:**
- The world described in the uploaded file is a {self.genre} setting. It emphasizes {self.world.traits}.

**2. Setting Overview:**
- The setting scale is {self.world.get_title("Region")}s, {self.world.get_title("City")}s, and {self.world.get_title("District")}s.
- Factions include {random.choice(self.world.factions).name}, {random.choice(self.world.factions).name}, {random.choice(self.world.factions).name}, and they have unique goals and rivalries.


**4. Player Interaction:**
- The players will likely start as underdog adventurers but can shape their roles as the session progresses.
- Their choices should meaningfully affect the world, impacting alliances, environments, or outcomes.
- The Player Characters are:
  - {"  -  ".join([f"{c.name}: {c.backstory_summary}" for c in self.players])}

**5. Key Historical/Lore Points:**

{self.world.history}

"""
        log(prompt, _print=True)
        response = self.world.system.generate_json(
            prompt, primer=primer, funcobj=self._outline_funcobj
        )
        self.name = response["name"] if not self.name else self.name
        self.description = response["description"]

        from models.campaign.episode import SceneNote

        for scene in self.outline:
            scene.delete()
        self.outline = []

        for po in response["plot_outline"]:
            allies = self.generate_npcs(po.get("allies"))
            antagonists = self.generate_combatants(po.get("antagonists"))
            places = self.generate_places(po.get("places"))
            items = self.generate_items(po.get("items"))
            sn = SceneNote(
                name=po["name"],
                act=po["act"],
                scene=po["scene"],
                description=po["description"],
                type=po["type"],
                notes=po["scenario"],
                music=po["music"],
                actors=allies + antagonists,
                setting=places,
                loot=items,
            )
            sn.save()
            self.outline += [sn]
        self.save()

    def generate_npcs(self, objs):
        from models.ttrpgobject.character import Character
        from models.ttrpgobject.creature import Creature

        if not objs:
            return []

        actors = []
        for obj in objs:
            first_name = obj["name"].split()[0]
            last_name = obj["name"].split()[-1]
            results = Character.search(
                world=self.world, name=first_name
            ) + Creature.search(world=self.world, name=first_name)
            npc = [c for c in results if last_name in c.name]
            char = npc[0] if npc else []

            if not char:
                char = Character(
                    world=self.world,
                    species=obj["species"],
                    name=obj["name"],
                    desc=obj["description"],
                    backstory=obj["backstory"],
                )
                char.save()
                self.associations += [char]
                actors += [char]
                self.save()
                requests.post(
                    f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
                )
        return actors

    def generate_combatants(self, objs):
        from models.ttrpgobject.character import Character
        from models.ttrpgobject.creature import Creature

        if not objs:
            return []

        actors = []
        for obj in objs:
            first_name = obj["name"].split()[0]
            last_name = obj["name"].split()[-1]
            results = Character.search(
                world=self.world, name=first_name
            ) + Creature.search(world=self.world, name=first_name)
            npc = [c for c in results if last_name == first_name or last_name in c.name]
            char = npc[0] if npc else []

            if not char:
                char = Creature(
                    world=self.world,
                    type=obj["combatant_type"],
                    name=obj["name"],
                    desc=obj["description"],
                )
                char.save()
                self.associations += [char]
                actors += [char]
                self.save()
                requests.post(
                    f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
                )
        return actors

    def generate_items(self, objs):
        from models.ttrpgobject.item import Item

        if not objs:
            return []
        items = []
        for obj in objs:
            first_name = obj["name"].split()[0]
            last_name = obj["name"].split()[-1]
            item = [
                c
                for c in Item.search(world=self.world, name=first_name)
                if last_name == first_name or last_name in c.name
            ]
            char = item[0] if item else []

            if not char:
                char = Item(
                    world=self.world,
                    rarity=obj["rarity"],
                    name=obj["name"],
                    desc=obj["description"],
                    features=obj["attributes"],
                )
                char.save()
                self.associations += [char]
                items += [char]
                self.save()
                requests.post(
                    f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
                )
        return items

    def generate_places(self, objs):
        if not objs:
            return []
        places = []
        for obj in objs:
            Model = None
            for key, val in self.world.system._titles.items():
                if (
                    key.lower() != "world"
                    and val.lower() == obj["location_type"].lower()
                ):
                    Model = AutoModel.load_model(key)
                    break
            log(Model, key, _print=True)
            if Model:
                first_name = obj["name"].split()[0]
                last_name = obj["name"].split()[-1]
                char = None
                for c in Model.search(world=self.world, name=first_name):
                    if last_name == first_name or last_name in c.name:
                        char = c
                        break
                if not char:
                    char = Model(
                        world=self.world,
                        name=obj["name"],
                        desc=obj["description"],
                        backstory=obj["backstory"],
                    )
                    char.save()
                    self.associations += [char]
                    places += [char]
                    self.save()
                    requests.post(
                        f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
                    )
        return places

    ## MARK: - Verification Hooks
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_campaign()
        document.pre_save_associations()
        document.pre_save_episode_num()
        document.pre_save_scene_note()

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify methods ##################
    def pre_save_campaign(self):
        if self not in self.campaign.episodes:
            self.campaign.episodes += [self]

    def pre_save_associations(self):
        assoc = []
        for a in self.associations:
            if a:
                if a not in assoc:
                    assoc += [a]
                if a not in self.campaign.associations:
                    self.campaign.associations += [a]
        self.associations = assoc
        self.associations.sort(key=lambda x: (x.model_name(), x.name))

    ################### verify current_scene ##################
    def pre_save_episode_num(self):
        if not self.episode_num:
            num = re.search(r"\b\d+\b", self.name).group(0)
            if num.isdigit():
                self.episode_num = int(num)

    def pre_save_scene_note(self):
        self.scenenotes = [s for s in self.scenenotes if s]
        self.scenenotes.sort(key=lambda x: x.num)
