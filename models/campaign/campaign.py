# from autonomous.model.autoattr import AutoAttribute
import os
import random

import markdown
import requests
from autonomous.model.autoattr import BoolAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from bs4 import BeautifulSoup

from autonomous import log
from models.base.ttrpgbase import TTRPGBase
from models.utility.parse_attributes import parse_text

from .episode import Episode


class Campaign(AutoModel):
    name = StringAttr(default="")
    description = StringAttr(default="")
    world = ReferenceAttr(choices=["World"], required=True)
    episodes = ListAttr(ReferenceAttr(choices=[Episode]))
    party = ReferenceAttr(choices=["Faction"])
    summary = StringAttr(default="")
    one_shot = BoolAttr(default="False")

    def delete(self):
        all(e.delete() for e in self.episodes)
        super().delete()

    @property
    def associations(self):
        associations = []
        for ep in self.episodes:
            associations += ep.associations
        associations = list(set(associations))
        associations.sort(key=lambda x: (x.model_name(), x.name))
        return associations

    @property
    def characters(self):
        return [a for a in self.associations if a.model_name() == "Character"]

    @property
    def creatures(self):
        return [a for a in self.associations if a.model_name() == "Creature"]

    @property
    def events(self):
        return [e for ep in self.episodes for e in ep.events]

    @property
    def encounters(self):
        encounters = []
        for a in self.episodes:
            encounters += a.encounters
        return list(set(encounters))

    @property
    def factions(self):
        return [a for a in self.associations if a.model_name() == "Faction"]

    @property
    def geneology(self):
        return [self.world]

    @property
    def genre(self):
        return self.world.genre

    @property
    def history(self):
        return self.summary

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
    def path(self):
        return f"campaign/{self.pk}"

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
    def stories(self):
        return list(set([s for ep in self.episodes for s in ep.stories]))

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

    def generate_history(self):
        text = ""
        for entry in sorted(self.episodes, key=lambda x: x.episode_num):
            if entry.summary.strip():
                text += f"\n{entry.summary}\n"
            elif entry.end_date:
                entry.generate_history()
                text += f"\n{entry.summary}\n"
        storylines = (
            ", ".join([f"{s.name}:{s.summary}" for s in self.stories])
            if self.stories
            else "None"
        )
        text = f"Summarize the following campaign for a {self.world.genre} TTRPG world. The summary should be concise and engaging, highlighting the key elements of the campaign and its significance within the larger story. Here is some context about the world: {self.world.name}, {self.world.history}. Here is some context about the campaign: {self.name}, {self.description}. Here are the storylines the party has interacted with: {storylines} Here are the episode summaries: {text}."
        if text:
            self.summary = self.world.system.generate_summary(
                text,
                primer="Provide an engaging, narrative summary of the campaign, highlighting its key elements and significance within the larger story in MARKDOWN.",
            )
            self.summary = self.summary.replace("```markdown", "").replace("```", "")
            self.summary = (
                markdown.markdown(self.summary)
                .replace("h1>", "h3>")
                .replace("h2>", "h3>")
                .replace("h3>", "h4>")
                .replace("h4>", "h5>")
            )
            self.summary = parse_text(self, self.summary)
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
            campaign=self, name="[Title]", episode_num=len(self.episodes) + 1
        )
        episode.save()
        self.episodes = [episode] + self.episodes
        self.save()
        if episode.previous_episode:
            episode.loot = episode.previous_episode.loot
            episode.hooks = episode.previous_episode.hooks
            episode.associations = episode.previous_episode.associations
            if (
                episode.previous_episode.end_date
                and episode.previous_episode.end_date.year > 0
            ):
                episode.start_date = episode.previous_episode.end_date.copy(episode)
            episode.episode_num = episode.previous_episode.episode_num + 1
        else:
            episode.loot = ""
            episode.hooks = ""
            episode.associations = episode.party.members if episode.party else []
            episode.start_date = (
                self.end_date.copy(episode)
                if self.end_date.year > 0
                else episode.world.current_date.copy(episode)
            )
        episode.save()
        self.episodes = list(set(self.episodes))
        self.episodes.sort(key=lambda x: x.episode_num, reverse=True)
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
            "pk": str(self.pk),
            "description": self.description,
            "summary": self.summary,
        }
        data["start_date"] = str(self.start_date) if self.start_date else "Unknown"
        data["end_date"] = str(self.end_date) if self.end_date else "Ongoing"
        data["episodes"] = [
            e.page_data() for e in sorted(self.episodes, key=lambda x: x.episode_num)
        ]
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
        document.pre_save_players()
        document.pre_save_one_shot()
        document.description = parse_text(document, document.description)
        # document.pre_save_associations()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # log([p.name for p in document.players])

    # def clean(self):
    #     super().clean()

    ################### Verification Methods ###################

    def pre_save_players(self):
        for p in self.players:
            if not p.pk:
                # log(f"{p} is unsaved. Saving....")
                p.save()

    def pre_save_one_shot(self):
        if len(self.episodes) <= 1:
            self.one_shot = True
        elif isinstance(self.one_shot, str):
            if self.one_shot.lower() in ["true", "1", "yes"]:
                self.one_shot = True
            else:
                self.one_shot = False
