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
    side_quests = ListAttr(ReferenceAttr(choices=["SceneNote"]))
    current_episode = ReferenceAttr(choices=[Episode])

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
    #     def generate_outline(self):
    #         prompt = f"""Generate a complete and full Tabletop RPG session outline with a clear story arc of events in valid JSON. Create a main storyline with at least 5 ACTS, that jirror the 5 room dungeon structure. Include a villain or antagonist with a detailed goal and a network of supporting antagonists.

    #  In Addition, use the information provided in the uploaded file to connect elements to the existing {self.genre} world. Each Scene in the outline should include the following details:

    # DESCRIPTION

    # - Description of the scene, including any relevant plot points in the scene
    # - Mention major twists and opportunities for character development.
    # """
    #         description = f"{self.description}\n\n " + "\n\n".join(
    #             {ep.summary for ep in self.episodes if ep.summary}
    #         )
    #         description = BeautifulSoup(description, "html.parser").get_text()
    #         prompt += f"""
    # {f"CURRENT SCENARIO\n\n{description}" if description else ""}

    # PARTY

    # - The party members include:
    #   - {"\n  - ".join([f"{c.name}: {BeautifulSoup(c.backstory_summary, 'html.parser').get_text()}" for c in self.players])}

    # ADDITIONAL CHARACTERS

    # - Incorporate the following characters into the story:
    #   - {"\n  - ".join([f"{c.name}: {BeautifulSoup(c.backstory_summary, 'html.parser').get_text()}" for c in self.characters if c not in self.players and c in self.outline_associations])}
    #   - {"\n  - ".join([f"{c.name}: {BeautifulSoup(c.backstory_summary, 'html.parser').get_text()}" for c in self.creatures if c in self.outline_associations])}
    # - For each scene, describe any NPCs in the scene, including allies, neutral parties, and foes for each scene.
    #   - Provide brief backstories, motivations, and potential interactions with the players.

    # ITEMS

    # - Incorporate the following items:
    #   - {"\n  - ".join([f"{c.name}: {BeautifulSoup(c.backstory_summary, 'html.parser').get_text()}" for c in self.items if c in self.outline_associations])}
    # - For each scene, describe key magical, technological, or significant items available in the scene.
    #   - Include their origins, powers, and any consequences or risks associated with their use.
    #   - Mention how players might obtain or interact with these items.

    # LOCATION:

    # - Incorporate the following places:
    #   - {"\n  - ".join([f"{c.name}: {BeautifulSoup(c.backstory_summary, 'html.parser').get_text()}" for c in self.places if c in self.outline_associations])}
    # - For each scene, describe the location where the scene unfolds.
    #   - Describe the location’s key features, cultural aspects, and role in the story.
    #   - Include at least one central hub or recurring area where players can regroup and gather resources.

    # The session outline should be consistent with the world described in the uploaded file, incorporating its themes, factions, geography, and unique elements. Make the storyline and details flexible enough to allow player choices to influence the narrative direction.
    # """

    #         primer = f"""
    # # AI Primer: Understanding the World

    # **1. Genre and Themes:**
    # - The world described in the uploaded file is a {self.genre} setting. It emphasizes {self.world.traits}.

    # **2. Setting Overview:**
    # - The setting scale is {self.world.get_title("Region")}s, {self.world.get_title("City")}s, and {self.world.get_title("District")}s.
    # - Factions include {random.choice(self.world.factions).name}, {random.choice(self.world.factions).name}, {random.choice(self.world.factions).name}, and they have unique goals and rivalries.

    # **4. Player Interaction:**
    # - The players will likely start as underdog adventurers but can shape their roles as the session progresses.
    # - Their choices should meaningfully affect the world, impacting alliances, environments, or outcomes.
    # - The Player Characters are:
    #   - {"  -  ".join([f"{c.name}: {c.backstory_summary}" for c in self.players])}

    # **5. Key Historical/Lore Points:**

    # {self.world.history}

    # """
    #         log(prompt, _print=True)
    #         response = self.world.system.generate_json(
    #             prompt, primer=primer, funcobj=self._outline_funcobj
    #         )
    #         self.name = response["name"] if not self.name else self.name
    #         self.description = response["description"]

    #         from models.campaign.episode import SceneNote

    #         for scene in self.outline:
    #             scene.delete()
    #         self.outline = []

    #         for po in response["plot_outline"]:
    #             allies = self.generate_npcs(po.get("allies"))
    #             antagonists = self.generate_combatants(po.get("antagonists"))
    #             places = self.generate_places(po.get("places"))
    #             items = self.generate_items(po.get("items"))
    #             sn = SceneNote(
    #                 name=po["name"],
    #                 act=po["act"],
    #                 scene=po["scene"],
    #                 description=po["description"],
    #                 type=po["type"],
    #                 notes=po["scenario"],
    #                 music=po["music"],
    #                 actors=allies + antagonists,
    #                 setting=places,
    #                 loot=items,
    #             )
    #             sn.save()
    #             self.outline += [sn]
    #         self.save()

    #     def generate_npcs(self, objs):
    #         from models.ttrpgobject.character import Character
    #         from models.ttrpgobject.creature import Creature

    #         if not objs:
    #             return []

    #         actors = []
    #         for obj in objs:
    #             first_name = obj["name"].split()[0]
    #             last_name = obj["name"].split()[-1]
    #             results = Character.search(
    #                 world=self.world, name=first_name
    #             ) + Creature.search(world=self.world, name=first_name)
    #             npc = [c for c in results if last_name in c.name]
    #             char = npc[0] if npc else []

    #             if not char:
    #                 char = Character(
    #                     world=self.world,
    #                     species=obj["species"],
    #                     name=obj["name"],
    #                     desc=obj["description"],
    #                     backstory=obj["backstory"],
    #                 )
    #                 char.save()
    #                 self.associations += [char]
    #                 actors += [char]
    #                 self.save()
    #                 requests.post(
    #                     f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
    #                 )
    #         return actors

    #     def generate_combatants(self, objs):
    #         from models.ttrpgobject.character import Character
    #         from models.ttrpgobject.creature import Creature

    #         if not objs:
    #             return []

    #         actors = []
    #         for obj in objs:
    #             first_name = obj["name"].split()[0]
    #             last_name = obj["name"].split()[-1]
    #             results = Character.search(
    #                 world=self.world, name=first_name
    #             ) + Creature.search(world=self.world, name=first_name)
    #             npc = [c for c in results if last_name == first_name or last_name in c.name]
    #             char = npc[0] if npc else []

    #             if not char:
    #                 char = Creature(
    #                     world=self.world,
    #                     type=obj["combatant_type"],
    #                     name=obj["name"],
    #                     desc=obj["description"],
    #                 )
    #                 char.save()
    #                 self.associations += [char]
    #                 actors += [char]
    #                 self.save()
    #                 requests.post(
    #                     f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
    #                 )
    #         return actors

    #     def generate_items(self, objs):
    #         from models.ttrpgobject.item import Item

    #         if not objs:
    #             return []
    #         items = []
    #         for obj in objs:
    #             first_name = obj["name"].split()[0]
    #             last_name = obj["name"].split()[-1]
    #             item = [
    #                 c
    #                 for c in Item.search(world=self.world, name=first_name)
    #                 if last_name == first_name or last_name in c.name
    #             ]
    #             char = item[0] if item else []

    #             if not char:
    #                 char = Item(
    #                     world=self.world,
    #                     rarity=obj["rarity"],
    #                     name=obj["name"],
    #                     desc=obj["description"],
    #                     features=obj["attributes"],
    #                 )
    #                 char.save()
    #                 self.associations += [char]
    #                 items += [char]
    #                 self.save()
    #                 requests.post(
    #                     f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
    #                 )
    #         return items

    #     def generate_places(self, objs):
    #         if not objs:
    #             return []
    #         places = []
    #         for obj in objs:
    #             Model = None
    #             for key, val in self.world.system._titles.items():
    #                 if (
    #                     key.lower() != "world"
    #                     and val.lower() == obj["location_type"].lower()
    #                 ):
    #                     Model = AutoModel.load_model(key)
    #                     break
    #             log(Model, key, _print=True)
    #             if Model:
    #                 first_name = obj["name"].split()[0]
    #                 last_name = obj["name"].split()[-1]
    #                 char = None
    #                 for c in Model.search(world=self.world, name=first_name):
    #                     if last_name == first_name or last_name in c.name:
    #                         char = c
    #                         break
    #                 if not char:
    #                     char = Model(
    #                         world=self.world,
    #                         name=obj["name"],
    #                         desc=obj["description"],
    #                         backstory=obj["backstory"],
    #                     )
    #                     char.save()
    #                     self.associations += [char]
    #                     places += [char]
    #                     self.save()
    #                     requests.post(
    #                         f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
    #                     )
    #         return places

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
        self.associations = []
        for ep in self.episodes:
            for a in ep.associations:
                if a and a not in self.associations:
                    self.associations += [a]
                    if not a.canon:
                        a.canon = True
                        a.save()
        for a in self.associations:
            if a.world != self.world:
                a.world = self.world
                a.save()
        self.associations = sorted(
            self.associations,
            key=lambda x: (x.name,),
        )
