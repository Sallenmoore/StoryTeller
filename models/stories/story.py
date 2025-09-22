import random

from autonomous.model.autoattr import DictAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel

from autonomous import log
from models.base.ttrpgbase import TTRPGBase
from models.images.image import Image
from models.stories.event import Event
from models.stories.quest import Quest
from models.ttrpgobject.encounter import Encounter


class Story(AutoModel):
    name = StringAttr(default="")
    scope = StringAttr(default="Local")
    situation = StringAttr(default="")
    current_status = StringAttr(default="")
    backstory = StringAttr(default="")
    tasks = ListAttr(StringAttr(default=""))
    image = ReferenceAttr(choices=[Image])
    rumors = ListAttr(StringAttr(default=""))
    information = ListAttr(StringAttr(default=""))
    bbeg = ReferenceAttr(choices=["Character"])
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    world = ReferenceAttr(choices=["World"], required=True)

    def __str__(self):
        return f"{self.situation}"

    funcobj = {
        "name": "generate_story",
        "description": "creates a compelling narrative consistent with the described world for the players to engage with, explore, and advance in creative and unexpected ways.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A name for the storyline.",
                },
                "scope": {
                    "type": "string",
                    "description": "The scope of the story and how it fits into the larger world.",
                },
                "situation": {
                    "type": "string",
                    "description": "A description of the overall situation and its effects on the TTRPG world. This should be a specific, concrete situation that the players can engage with and explore.",
                },
                "current_status": {
                    "type": "string",
                    "description": "A detailed description of the current status of the situation, including things unknown to the player characters.",
                },
                "backstory": {
                    "type": "string",
                    "description": "A detailed description of the backstory leading up to the current situation.",
                },
                "tasks": {
                    "type": "array",
                    "description": "A list of tasks that the player characters must complete to advance the story. These tasks should be relevant to the situation and motivate players to enage with the larger story, plot, or related elements.",
                    "items": {"type": "string"},
                },
                "rumors": {
                    "type": "array",
                    "description": "A list of rumors that will draw the players in and cause the player characters to want to learn more about the situation, in the order they should be revealed. Rumors are not always true, but they should be relevant to the situation and provide useful information to the player characters.",
                    "items": {"type": "string"},
                },
                "information": {
                    "type": "array",
                    "description": " A list of reliable information that the player characters can discover about the situation, in the order they should be revealed. This information should be relevant to the situation and provide useful context or additional flavor for the player characters.",
                    "items": {"type": "string"},
                },
            },
        },
    }

    @property
    def encounters(self):
        return Encounter.search(story=self)

    @property
    def events(self):
        if events := [e for e in Event.search(world=self.world) if self in e.stories]:
            events.sort(
                key=lambda x: x.end_date if x.end_date else x.world.current_date
            )
        return events

    @property
    def quests(self):
        return Quest.search(storyline=self)

    @property
    def history(self):
        return (
            f"{self.situation}<br><br> {self.backstory}<br><br> {self.current_status}"
        )

    @property
    def path(self):
        return f"story/{self.pk}"

    def generate(self):
        prompt = f"Your task is to create a new storyline with a {self.scope} scope for the following {self.world.genre} TTRPG world. The story should incorporate existing world elements and relationships. however, the plot must include elements that can benefit from outside assistance or interference. Here is some context about the world: {self.world.name}, {self.world.description}. "

        if self.world.stories:
            prompt += "\n\nHere are some existing storylines in the world: "
            for story in random.sample(
                self.world.stories, min(len(self.world.stories), 3)
            ):
                prompt += f"\n\n{story.name}: {story.situation}. "

        if self.associations:
            prompt += "\n\nHere are some existing elements related to this storyline: "
            for assoc in self.associations:
                prompt += f"\n\n{assoc.name}: {assoc.backstory}. "

        if self.situation:
            prompt += f"\n\nUse the following prompt to guide the storyline: {self.situation}. "

        result = self.world.system.generate_json(
            prompt=prompt,
            primer=f"Create a new storyline that fits into the described world. {self.funcobj['description']}. Respond in JSON format consistent with this structure: {self.funcobj['parameters']}.",
            funcobj=self.funcobj,
        )
        if result:
            result.get("name") and setattr(self, "name", result.get("name"))
            result.get("scope") and setattr(self, "scope", result.get("scope"))
            result.get("situation") and setattr(
                self, "situation", result.get("situation")
            )
            result.get("current_status") and setattr(
                self, "current_status", result.get("current_status")
            )
            result.get("backstory") and setattr(
                self, "backstory", result.get("backstory")
            )
            result.get("tasks") and setattr(self, "tasks", result.get("tasks"))
            result.get("rumors") and setattr(self, "rumors", result.get("rumors"))
            result.get("information") and setattr(
                self, "information", result.get("information")
            )
            self.save()
            log(f"Generated Story: {self.name}", __print=True)
        else:
            log("Failed to generate Story", __print=True)

    ############# Association Methods #############
    # MARK: Associations
    def add_association(self, obj):
        # log(len(self.associations), obj in self.associations)
        if obj not in self.associations:
            self.associations += [obj]
            self.save()
        return obj
