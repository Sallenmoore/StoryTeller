import random

import markdown
from bs4 import BeautifulSoup

from autonomous import log
from autonomous.model.autoattr import DictAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.base.ttrpgbase import TTRPGBase


class Quest(AutoModel):
    name = StringAttr(default="")
    storyline = ReferenceAttr(choices=["Story"])
    description = StringAttr(default="")
    summary = StringAttr(default="")
    rewards = StringAttr(default="")
    contact = ReferenceAttr(choices=["Character"], required=True)
    antagonist = StringAttr(default="")
    hook = StringAttr(default="")
    plot_twists = ListAttr(StringAttr(default=""))
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    status = StringAttr(
        default="available", choices=["available", "active", "completed", "failed"]
    )

    funcobj = {
        "name": "generate_quest",
        "description": "creates a morally complicated, urgent, situation that player characters must resolve for or with the described character. The situation should not have immediate global consequences, but localized consequences for the NPC associated with it.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the situation, which should be intriguing and suggestive",
                },
                "rewards": {
                    "type": "string",
                    "description": "The reward for completing the situation depending on the outcome, including the specific financial compensation, items, or the detailed information that the player characters will receive",
                },
                "description": {
                    "type": "string",
                    "description": "A detailed description of the situation that must be resolved.",
                },
                "summary": {
                    "type": "string",
                    "description": "A one sentence summary of the task, worded like a job posting to entice someone to take on the task",
                },
                "antagonist": {
                    "type": "string",
                    "description": "Who or what is the main antagonist? What do they want, why? What is their plan? Name, appearance, and motivations. ",
                },
                "hook": {
                    "type": "string",
                    "description": "Describe the complete scene that hooks the player characters into action and gives them the initial task to accomplish.",
                },
                "plot_twists": {
                    "type": "array",
                    "description": "A list of potential plot twists that may occur during the situation, in the order they should be revealed. An unexpected complication, twist, or reveal that changes the direction of the story, raises stakes and threat level, or redefines the goal.",
                    "items": {"type": "string"},
                },
            },
        },
    }

    @property
    def rumors(self):
        return self.storyline.rumors

    @property
    def world(self):
        return self.storyline.world

    def generate_quest(self):
        prompt = f"""Generate a scenario for a sandbox style {self.contact.genre} Table Top RPG.The situation challenging for the player characters to overcome. The scenario can involve a mix of encounter types, such as Combat, Social, Exploration, and Stealth. The situation is brought to the players' attention by or with the character named {self.contact.name} who is described as: {self.contact.backstory}.

        The initiating npc also has the following goals, which may or may not play into the situation: {self.contact.goal}.
"""

        parent = self.contact.parent
        if parent:
            prompt += f"""
The scenario should start in {parent.name} and should include the following world elements:
LOCATION: {parent.backstory}.
"""
            while parent.parent:
                parent = parent.parent
                prompt += f"""Which is located in:
        {parent.name} [{parent.title}]: {parent.backstory}.
"""
        prompt += "\nADDITIONAL ELEMENTS:\n"
        for ass in self.associations:
            if ass not in self.contact.geneology:
                prompt += f"""
        {ass.name} [{ass.title}]: {ass.backstory}
"""

        prompt += f"""
The situation should be tangentially related in some way to the following global storyline:
- {self.storyline.name}: {BeautifulSoup(self.storyline.situation, "html.parser").get_text()}
  - Backstory: {BeautifulSoup(self.storyline.backstory, "html.parser").get_text()}
  - Current Situation: {BeautifulSoup(self.storyline.current_status, "html.parser").get_text()}
"""
        if self.description:
            prompt += f"""\n\nUse the following prompt as an additional design constraint on the situation:
{self.description}
"""

        primer = "You are an expert AI Table Top RPG Situation Generator. You will be provided with a character and a location. Generate a situation that is connected to the character's backstory, world events, and has a clearly defined story arc."
        log(prompt, _print=True)
        results = self.contact.system.generate_json(prompt, primer, self.funcobj)
        # log(results, _print=True)
        self.update_quest(**results)

    def update_quest(
        self,
        name,
        description,
        summary,
        rewards,
        antagonist,
        hook,
        rumors,
        plot_twists,
    ):
        description = (
            markdown.markdown(description.replace("```markdown", "").replace("```", ""))
            .replace("h1>", "h3>")
            .replace("h2>", "h3>")
        )

        self.name = name
        self.rewards = rewards
        self.description = description
        self.summary = summary
        self.antagonist = antagonist
        self.rumors = rumors
        self.hook = hook
        self.plot_twists = plot_twists
        self.save()

    ############# Association Methods #############
    # MARK: Associations
    def add_association(self, obj):
        # log(len(self.associations), obj in self.associations)
        if obj not in self.associations:
            self.associations += [obj]
            self.save()
        return obj
