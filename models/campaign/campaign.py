# from autonomous.model.autoattr import AutoAttribute
import os
import random

import markdown
import requests
from bs4 import BeautifulSoup

from autonomous import log
from autonomous.model.autoattr import ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.base.ttrpgbase import TTRPGBase

from .episode import Episode


class Campaign(AutoModel):
    name = StringAttr(default="")
    description = StringAttr(default="")
    world = ReferenceAttr(choices=["World"], required=True)
    episodes = ListAttr(ReferenceAttr(choices=[Episode]))
    party = ReferenceAttr(choices=["Faction"])
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    summary = StringAttr(default="")
    outline = ListAttr(ReferenceAttr(choices=["SceneNote"]))
    side_quests = ListAttr(ReferenceAttr(choices=["SceneNote"]))
    current_episode = ReferenceAttr(choices=[Episode])

    _outline_funcobj = {
        "name": "generate_campaign_outline",
        "description": "generates a campaign outline for a Table Top RPG with characters, items, and scenes",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the campaign",
                },
                "description": {
                    "type": "string",
                    "description": "A brief overview of the campaign, it's story arc, and the general theme.",
                },
                "plot_outline": {
                    "type": "array",
                    "description": "Create an outline breakdown for a main storyline with at least 3 acts, including an inciting event, key conflicts, and a climactic resolution. Mention major twists and opportunities.",
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
                                "description": "Name of the side quest.",
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
                                "description": "A physical description of the scene, including characters involved in the scene, taht could be used to generate an image.",
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

    def delete(self):
        all(e.delete() for e in self.episodes)
        all(e.delete() for e in self.outline)
        all(e.delete() for e in self.side_quests)
        super().delete()

    ## MARK: Properties
    ##################### PROPERTY METHODS ####################
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
    def locations(self):
        return [a for a in self.associations if a.model_name() == "Location"]

    @property
    def places(self):
        return [
            a
            for a in self.associations
            if a.model_name() in ["Region", "City", "District", "Location"]
        ]

    @property
    def players(self):
        return self.party.players if self.party else []

    @property
    def vehicles(self):
        return [a for a in self.associations if a.model_name() == "Vehicle"]

    @property
    def regions(self):
        return [a for a in self.associations if a.model_name() == "Region"]

    @property
    def end_date(self):
        if self.episodes:
            for episode in self.episodes:
                if episode.end_date:
                    return episode.end_date

    @property
    def start_date(self):
        if self.episodes:
            for episode in self.episodes[::-1]:
                if episode.start_date:
                    return episode.start_date

    @property
    def episode_reports(self):
        reports = []
        for episode in self.episodes:
            reports.append(episode.episode_report)
        return reports

    ## MARK: INSTANCE METHODS
    ################################################################
    ##                     INSTANCE METHODS                       ##
    ################################################################
    def generate_outline(self):
        prompt = f"""Generate a complete and full Tabletop RPG campaign outline with a clear story arc events in valid JSON. Create a main storyline with at least 3 ACTS and 4-8 SESSIONS per ACT, including an inciting event, key conflicts, and a climactic resolution. Include a main villain or antagonist with a detailed goal and a network of supporting antagonists.

 In Addition, use the information provided in the uploaded file to connect elements to the existing {self.genre} world. Each Scene in the outline should include the following details:

DESCRIPTION

- Description of the scene, including any relevant plot points in the scene
- Mention major twists and opportunities for character development.
"""
        description = f"{self.description}\n\n " + "\n\n".join(
            {ep.summary for ep in self.episodes if ep.summary}
        )
        description = BeautifulSoup(description, "html.parser").get_text()
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


The campaign outline should be consistent with the world described in the uploaded file, incorporating its themes, factions, geography, and unique elements. Make the storyline and details flexible enough to allow player choices to influence the narrative direction.
"""

        primer = f"""
# AI Primer: Understanding the World

**1. Genre and Themes:**
- The world described in the uploaded file is a {self.genre} setting. It emphasizes {self.world.traits}.

**2. Setting Overview:**
- The world contains {self.world.get_title("Region")}s, {self.world.get_title("City")}s, and {self.world.get_title("District")}s.
- Factions include {random.choice(self.world.factions).name}, {random.choice(self.world.factions).name}, {random.choice(self.world.factions).name}, and they have unique goals and rivalries.


**4. Player Interaction:**
- The players will likely start as underdog adventurers but can shape their roles as the campaign progresses.
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

    def resummarize(self):
        text = ""
        for entry in sorted(self.episodes, key=lambda x: x.episode_num):
            if entry.summary.strip():
                text += f"\n{entry.summary}\n"
            elif entry.end_date:
                entry.resummarize()
                text += entry.summary
        if text:
            self.summary = self.world.system.generate_summary(
                text,
                primer="Generate a summary of the campaign events in MARKDOWN format with a paragraph breaks where appropriate, but after no more than 4 sentences.",
            )
            self.summary = self.summary.replace("```markdown", "").replace("```", "")
            self.summary = (
                markdown.markdown(self.summary)
                .replace("h1>", "h3>")
                .replace("h2>", "h3>")
                .replace("h3>", "h4>")
                .replace("h4>", "h5>")
            )
            self.save()

    def add_episode(
        self,
        name=None,
        description=None,
        start_date=None,
        end_date=None,
        report=None,
    ):
        episode = Episode(
            campaign=self,
            name=f"Episode {len(self.episodes) + 1}: [Title]",
        )
        episode.save()
        self.episodes += [episode]
        self.save()
        return self.update_episode(
            pk=episode.pk,
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            report=report,
        )

    def update_episode(
        self,
        pk,
        name=None,
        description=None,
        start_date=None,
        end_date=None,
        report=None,
    ):
        if episode := Episode.get(pk):
            episode.name = episode.name if name is None else name
            episode.description = (
                episode.description if description is None else description
            )
            episode.start_date = (
                episode.start_date if start_date is None else start_date
            )
            episode.end_date = episode.end_date if end_date is None else end_date
            if report != episode.episode_report:
                episode.episode_report = report
            episode.save()
            self.episodes = list(set(self.episodes))
            self.episodes.sort(key=lambda x: x.episode_num, reverse=True)
            self.save()
        else:
            raise ValueError("Episode not found in campaign")
        return episode

    def add_association(self, obj, episode=None):
        if obj not in self.associations:
            self.associations += [obj]
            self.save()
        if episode:
            return episode.add_association(obj)
        return obj

    def get_episode(self, episodepk=None):
        return self.get_episode(episodepk)

    def delete_episode(self, episodepk):
        episode = Episode.get(episodepk)
        if episode in self.episodes:
            self.episodes.remove(episode)
            episode.delete()
            self.summary = ""
            self.save()

    def page_data(self):
        data = {
            "name": self.name,
            "description": self.description,
            "summary": self.summary,
        }
        data["start_date"] = str(self.start_date) if self.start_date else "Unknown"
        data["end_date"] = str(self.end_date) if self.end_date else "Ongoing"
        return data

    # MARK: Verification
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
        document.pre_save_current_episode()
        document.pre_save_episodes()
        document.pre_save_players()
        document.pre_save_associations()

        ###### MIGRATION ######
        if not isinstance(document.outline, list):
            document.outline = []

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # log([p.name for p in document.players])

    # def clean(self):
    #     super().clean()

    ################### Verification Methods ###################

    def pre_save_current_episode(self):
        if not self.current_episode and self.episodes:
            self.current_episode = self.episodes[0]

    def pre_save_episodes(self):
        self.episodes = list(set(self.episodes))
        self.episodes.sort(key=lambda x: x.episode_num, reverse=True)

    def pre_save_players(self):
        for p in self.players:
            if not p.pk:
                # log(f"{p} is unsaved. Saving....")
                p.save()

    def pre_save_associations(self):
        for ep in self.episodes:
            for a in ep.associations:
                if a and a not in self.associations:
                    self.associations += [a]
        for a in self.associations:
            if a.world != self.world:
                a.world = self.world
                a.save()
        self.associations = sorted(
            self.associations,
            key=lambda x: (
                x.model_name() == "World",
                x.model_name() == "Region",
                x.model_name() == "City",
                x.model_name() == "Location",
                x.model_name() == "District",
                x.model_name() == "Vehicle",
                x.model_name() == "Faction",
                x.model_name() == "Character",
                x.model_name() == "Creature",
                x.model_name() == "Item",
                x.model_name() == "Encounter",
                x.name,
            ),
        )
