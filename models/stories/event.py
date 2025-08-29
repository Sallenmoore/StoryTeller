import random

from autonomous import log
from autonomous.model.autoattr import DictAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.base.ttrpgbase import TTRPGBase


class Event(AutoModel):
    name = StringAttr(default="")
    type = StringAttr(default="Local", choices=["Local", "Global", "Epic"])
    impact = StringAttr(default="")
    backstory = StringAttr(default="")
    outcome = ListAttr(StringAttr(default=""))
    start_date = ReferenceAttr(choices=["Date"])
    end_date = ReferenceAttr(choices=["Date"])
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    episodes = ListAttr(ReferenceAttr(choices=["Episode"]))
    story = ReferenceAttr(choices=["Story"])

    @classmethod
    def create_event_from_encounter(cls, encounter):
        event = cls()
        event.name = encounter.name
        event.type = "Local"
        event.impact = (
            f"A {encounter.enemy_type} encounter of {encounter.difficulty} difficulty."
        )
        event.backstory = encounter.backstory
        event.outcome = ";----;".join(encounter.potential_outcomes)
        event.start_date = encounter.start_date
        event.end_date = encounter.end_date
        event.story = encounter.story
        event.associations = encounter.associations
        event.episodes = encounter.episodes
        event.save()
        return event

    @classmethod
    def create_event_from_episode(cls, episode):
        event = cls()
        event.name = episode.name
        event.type = "Local"
        event.impact = episode.summary
        event.backstory = episode.description
        event.outcome = episode.episode_report
        event.start_date = episode.start_date
        event.end_date = episode.end_date
        event.story = episode.story
        event.associations = episode.associations
        event.episodes += [episode]
        event.save()
        return event
