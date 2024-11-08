import json
import random

import markdown

from autonomous import log
from autonomous.ai.jsonagent import JSONAgent
from autonomous.model.autoattr import (
    DictAttr,
    ListAttr,
    ReferenceAttr,
)
from autonomous.model.automodel import AutoModel
from autonomous.tasks.autotask import AutoTasks
from models.images.image import Image


class AutoGM(AutoModel):
    player = ReferenceAttr(choices=["Character"])
    world = ReferenceAttr(choices=["World"], required=True)
    agent = ReferenceAttr(choices=[JSONAgent])
    history = ListAttr(DictAttr())
    images = ListAttr(ReferenceAttr(choices=[Image]))
    # start_date = ReferenceAttr(choices=["Event"])
    # end_date = ReferenceAttr(choices=["Event"])

    _encounter_types = [
        "combat",
        "social",
        "exploration",
        "mystery",
        "rescue",
        "infiltration",
    ]

    _funcobj = {
        "name": "run_encounter",
        "description": "creates an encounter scenario for the players",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "The GM's description of the scene and any relevant information the GM thinks the players need to know",
                },
                "player": {
                    "type": "string",
                    "description": "Determines the player the GM is currently interacting with",
                    "items": {"type": "string"},
                },
                "npcs": {
                    "type": "array",
                    "description": "A list of descriptions of non-combatant NPCs in the scenario, if any",
                    "items": {"type": "string"},
                },
                "combatants": {
                    "type": "array",
                    "description": "A list of descriptions of combatants in the scenario, if it is a combat scenario",
                    "items": {"type": "string"},
                },
                "loot": {
                    "type": "array",
                    "description": "A list of loot items gained in the scenario, if any.",
                    "items": {"type": "string"},
                },
                "requires_roll": {
                    "type": "string",
                    "description": "Determines if the players' next action requires a roll of the dice, and if so, what type of roll, such as a WIS skill check, attack, or dmg roll",
                },
            },
        },
    }

    ##################### CLASS METHODS ####################
    @classmethod
    def _summarize(cls, pk):
        from models.world import World

        gm = cls.get(pk)
        prompt = ". ".join([h["description"] for h in gm.history if "description" in h])
        primer = "Generate a summary of less than 250 words of the following events in MARKDOWN format."
        summary = gm.world.system.generate_summary(prompt, primer)
        summary = summary.replace("```markdown", "").replace("```", "")
        summary = markdown.markdown(summary)
        gm.history = [{"description": summary}]
        gm.save()
        return summary

    ##################### PROPERTY METHODS ####################

    @property
    def gm(self):
        if not self.agent:
            self.agent = JSONAgent(
                name=f"TableTop RPG Game Master for {self.world.name}, a {self.world.genre} setting",
                instructions=f"""You are highly skilled and creative AI trained to act as a Game Master for a {self.world.genre} Table Top RPG. Use the uploaded file to reference the existing world objects, such as characters, creatures, items, locations, encounters, and storylines.

                Use existing world elements and their connections to expand on existing storylines or generate a new story consiostent with the existing elements and timeline of the world. While the new story should be unique, there should also be appropriate connections to one or more existing elements in the world as described by the uploaded file.""",
                description=f"A helpful AI assistant trained to act as the Table Top Game Master for 1 or more players. You will create consistent, mysterious, and unique homebrewed {self.world.genre} stories that will challenge, surprise, and delight players. You will also ensure that your stories are consistent with the existing world as described by the uploaded file.",
            )
            self.agent.save()
            self.save()
            self.update_refs()
        return self.agent

    @property
    def summary(self):
        summary = ""
        if len(self.history) > 4:
            AutoTasks().task(AutoGM._summarize, self.pk)
        for h in self.history:
            if "description" in h:
                summary += f'{h["description"]}\n'
        return summary

    def update_refs(self):
        self.gm.get_client().clear_files()
        world_data = self.world.page_data()
        ref_db = json.dumps(world_data).encode("utf-8")
        self.gm.get_client().attach_file(
            ref_db, filename=f"{self.world.slug}-gm-dbdata.json"
        )
        self.save()

    def start(self, player, year=None, scenario=None):
        self.history = []
        self.player = player
        self.year = year or self.world.current_date.year
        self.scenario = (
            scenario
            or "Build on an existing storyline or encounter from the world to surprise and challenge player's expectations."
        )
        prompt = f"As the AI Game Master for a new {self.world.genre} TTRPG session within the established world of {self.world.name}, start a new game session by describing a setting and scenario plot hook to the players in a vivid and interesting way. Incorporate the following information into the scenario:"
        prompt += f"""
            PLAYER: {self.player.name} [{self.player.pk}]
            {self.player.backstory_summary}

            ENCOUNTER TYPE: {random.choice(self._encounter_types)}

            DESCRIPTION: {self.scenario}

            IN-GAME DATE: {self.year}
        """
        log(prompt, _print=True)
        response = self.gm.generate(
            prompt,
            function={
                "name": "start_encounter",
                "description": "creates a setting and scenario plot hook for the player to investigate",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "The initial description of the scene, events, and any relevant information the Game Master thinks the players need to know",
                        },
                    },
                },
            },
        )
        if desc := response["description"]:
            desc = f"CHARACTER DESCRIPTION:{self.player.description}\n\nSCENE: {desc}"
            img = Image.generate(
                desc,
                tags=["episode", "autogm"],
            )
            self.images.append(img)
            response["image"] = img
        self.history.append(response)
        self.save()
        return response

    def run(self, message):
        prompt = f"""As the AI Game Master for a {self.world.genre} TTRPG session, write a description for the next event, scene, or combat round for the currently running game session based on the player's message, including the roll result if present, and the previous events using the following details:
            PLAYER: {self.player.name} [{self.player.pk}]
            PLAYER MESSAGE: {message}

            PREVIOUS EVENTS SUMMARY: {self.summary}

        """
        log(prompt, _print=True)
        response = self.gm.generate(prompt, function=self._funcobj)
        self.history.append(response)
        if desc := response["description"]:
            desc = f"CHARACTER DESCRIPTION:{self.player.description}\n\nSCENE: {desc}"
            img = Image.generate(
                desc,
                tags=["episode", "autogm"],
            )
            self.images.append(img)
            response["image"] = img
        self.save()
        return response

    def end(self, message):
        prompt = f"""As the AI Game Master for a {self.world.genre} TTRPG session, create a end session cliffhanger scenario for the currently running game session based on the following details:
            PLAYER: {self.player.name} [{self.player.pk}]

            CURRENT SUMMARY: {self.summary}

            PLAYER ACTIONS: {message}
        """
        log(prompt, _print=True)
        response = self.gm.generate(prompt, function=self._funcobj)
        self.history.append(response)
        if desc := response["description"]:
            desc = f"CHARACTER DESCRIPTION:{self.player.description}\n\nSCENE: {desc}"
            img = Image.generate(
                desc,
                tags=["episode", "autogm"],
            )
            self.images.append(img)
            response["image"] = img
        self.save()
        return response
