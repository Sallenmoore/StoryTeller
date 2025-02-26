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
    current_episode = ReferenceAttr(choices=[Episode])

    def delete(self):
        all(e.delete() for e in self.episodes)
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
