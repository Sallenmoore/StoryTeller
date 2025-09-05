import random

from autonomous import log
from autonomous.model.autoattr import ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.images.image import Image


class Event(AutoModel):
    name = StringAttr(default="")
    scope = StringAttr(default="Local", choices=["Local", "Regional", "Global", "Epic"])
    impact = StringAttr(default="")
    backstory = StringAttr(default="")
    outcome = StringAttr(default="")
    start_date = ReferenceAttr(choices=["Date"])
    end_date = ReferenceAttr(choices=["Date"])
    image = ReferenceAttr(choices=[Image])
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    episodes = ListAttr(ReferenceAttr(choices=["Episode"]))
    story = ReferenceAttr(choices=["Story"])
    world = ReferenceAttr(choices=["World"], required=True)

    @classmethod
    def create_event_from_encounter(cls, encounter):
        event = cls()
        event.name = encounter.name
        event.scope = "Local"
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
        event.story = encounter.story
        event.world = encounter.world
        event.save()
        return event

    @classmethod
    def create_event_from_episode(cls, episode):
        event = cls()
        event.name = episode.name
        event.scope = "Local"
        event.impact = episode.summary
        event.backstory = episode.description
        event.outcome = episode.episode_report
        event.start_date = episode.start_date
        event.end_date = episode.end_date
        event.story = episode.story
        event.associations = episode.associations
        event.episodes += [episode]
        event.story = episode.story
        event.world = episode.world
        event.save()
        return event

    @property
    def path(self):
        return f"event/{self.pk}"

    ############# Association Methods #############
    # MARK: Associations
    def add_association(self, obj):
        # log(len(self.associations), obj in self.associations)
        if obj not in self.associations:
            self.associations += [obj]
            self.save()
        return obj
