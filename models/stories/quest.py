import random

import markdown
from bs4 import BeautifulSoup

from autonomous import log
from autonomous.model.autoattr import DictAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.base.ttrpgbase import TTRPGBase


class Scene(AutoModel):
    type = StringAttr(
        choices=[
            "social",
            "encounter",
            "combat",
            "investigation",
            "exploration",
            "stealth",
            "puzzle",
        ]
    )
    setup = StringAttr(default="")
    description = StringAttr(default="")
    task = StringAttr(default="")
    challenges = ListAttr(StringAttr(default=""))
    npcs = ListAttr(StringAttr(default=""))
    information = ListAttr(StringAttr(default=""))
    stakes = StringAttr(default="")
    resolution = StringAttr(default="")
    rewards = StringAttr(default="")
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))


class Quest(AutoModel):
    name = StringAttr(default="")
    storyline = ReferenceAttr(choices=["Story"])
    description = StringAttr(default="")
    scenes = ListAttr(ReferenceAttr(choices=[Scene]))
    summary = StringAttr(default="")
    rewards = StringAttr(default="")
    contact = ReferenceAttr(choices=["Character"])
    rumors = ListAttr(StringAttr(default=""))
    antagonist = StringAttr(default="")
    rumors = ListAttr(StringAttr(default=""))
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
                "scenes": {
                    "type": "array",
                    "description": "A detailed description of scenes the players may encounter when trying to resolve the situation. For each scene include the setup for the scene, npcs, complication the players will face in the scene, a quick description of the scene, and its resolution.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "type",
                            "setup",
                            "description",
                            "npcs",
                            "challenges",
                            "information",
                            "task",
                            "stakes",
                            "resolution",
                            "rewards",
                        ],
                        "properties": {
                            "type": {
                                "type": "string",
                                "description": "The type of scene. Must be one of the following: social, encounter, combat, investigation, exploration, stealth, or puzzle",
                            },
                            "setup": {
                                "type": "string",
                                "description": "The initial description of the scene to draw players in",
                            },
                            "description": {
                                "type": "string",
                                "description": "A quick summary of the scene, including any important details about the environment and the situation the players find themselves in",
                            },
                            "task": {
                                "type": "string",
                                "description": "The specific and concrete task that the characters must complete to resolve the scene, including any game mechanics associated with the task",
                            },
                            "npcs": {
                                "type": "array",
                                "description": "A list of npcs that will be involved in the scene, including their names, descriptions, and any relevant information about their motivations or goals. This should include both allies and antagonists that the players may encounter in the scene.",
                                "items": {"type": "string"},
                            },
                            "challenges": {
                                "type": "array",
                                "description": "A list of complications that the players will face in the scene, including the gameplay mechanics (skill check, saving throw, etc.) associated with each complication. These should be specific challenges that the players must overcome to complete the scene.",
                                "items": {"type": "string"},
                            },
                            "information": {
                                "type": "array",
                                "description": "A list of relevant and actionable information players may gain from the scene. This should include any clues, hints, or other information that the players may gain from the scene that will help them resolve the situation. This should not include information that is not relevant to the situation or that does not help the players resolve the situation.",
                                "items": {"type": "string"},
                            },
                            "stakes": {
                                "type": "string",
                                "description": "What's at risk immediately if the players characters don't act? What are the consequences of failure in this scene? This should be a specific, concrete consequence that the players will face if they fail to complete the scene.",
                            },
                            "resolution": {
                                "type": "string",
                                "description": "The resolution of the scene, including any important details about how the player characters can progress to the next scene or how they can fail. This should include any game mechanics associated with the resolution, such as skill checks or saving throws.",
                            },
                            "rewards": {
                                "type": "string",
                                "description": "Any specific rewards, items, or information that the players will receive for completing the scene. This should be a specific, concrete reward, such as an item or relevant information that the players will receive for completing the scene.",
                            },
                        },
                    },
                },
                "summary": {
                    "type": "string",
                    "description": "A one sentence summary of the task, worded like a job posting to entice someone to take on the task",
                },
                "rumors": {
                    "type": "array",
                    "description": "A list of rumors that will help the player characters understand the situation, in the order they should be revealed. Rumors are not always true, but they should be relevant to the situation and provide useful information to the player characters about the situation.",
                    "items": {"type": "string"},
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
        scenes,
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
        if self.scenes:
            for scene in self.scenes:
                scene.delete()
        for scene in scenes:
            new_scene = Scene(**scene)
            new_scene.save()
            self.scenes += [new_scene]
        self.save()
