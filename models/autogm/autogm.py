import random

import markdown

from autonomous import log
from autonomous.model.autoattr import (
    FileAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel


class AutoGM(AutoModel):
    """
    AutoGM is a class for generating and managing graphs using the AutoGM framework.
    """

    scenes = ListAttr(StringAttr(default=""))
    campaign = ReferenceAttr(choices=["Campaign"])

    funcobj = {
        "name": "generate_session",
        "description": "Creates a morally complicated, interesting, and multi-part TTRPG session outline that player characters can discover for or with the described non-player characters and world elements.",
        "parameters": {
            "type": "object",
            "properties": {
                "scenes": {
                    "type": "array",
                    "description": "A list scenes in the session",
                    "items": {
                        "type": "string",
                        "description": "A description of the scene including the characters, location, and other world elements involved in the scene.",
                    },
                }
            },
        },
    }

    @property
    def episode(self):
        """
        Returns the episode summary.
        """
        return "\n".join(self.scenes)

    @property
    def last_scene(self):
        """
        Returns the last scene in the scenes list.
        """
        return self.scenes[-1] if self.scenes else ""

    def generate_episode(self, msg):
        """
        Generates the next scene using the AutoGM framework.
        """
        prompt = f"""Generate a 5 act TTRPG session outline in MARKDOWN using the following structure:
Act 1: The Guardian or the Call to Adventure
Act 2: A roleplay opportunity or puzzle
Act 3: A battle or other resource drain
Act 4: The Final Showdown
Act 5: The twist or the resolution

{f"THE STORY SO FAR...\n\n{self.campaign.summary}" if self.campaign.summary else ""}

The player characters are described as follows:

- {"\n- ".join([f"{c.name} [{c.gender, c.age}]: {c.backstory}" for c in self.campaign.party.players])}

CAMPAIGN ELEMENTS TO BE INCORPORATED

- {"\n- ".join([f"{c.name} [{c.title}]: {c.backstory}" for c in self.campaign.associations if hasattr(c, "is_player") and not c.is_player])}


BASE THE SESSION ON THE FOLLOWING STORYLINE:

"""
        if msg:
            prompt += f"""
            {msg}
"""
        else:
            npc = random.choice(
                [c for c in self.campaign.characters if not c.is_player]
            )
            if not npc.quests:
                npc.generate_quest()
            quest = random.choice(self.npc.quests)
            prompt += f"""
NPC
{npc.name}
{npc.backstory}

STORY:
{quest.description}
"""
        log(prompt, _print=True)
        results = self.campaign.world.system.generate_json(
            prompt,
            primer="You are an expert AI in generating exciting and suspensful TTRPG sessions",
            funcobj=self.funcobj,
        )
        log(results, _print=True)
        self.scenes = results["scenes"]

        self.save()

    def generate_scene(self, idx):
        if not self.scenes:
            self.generate_episode()
        prompt = (
            "You are a TTRPG GM. Your party consists of the following characters:\n"
        )

        prompt += "\n".join(
            [
                f"- {c.name} [{c.gender, c.age}]: {c.backstory}"
                for c in self.campaign.party.players
            ]
        )

        if self.scenes:
            prompt += f"""
GIVEN THE BELOW OUTLINE OF A TTRPG SESSION:
{self.episode}
"""

        prompt += f"""
INSTRUCTIONS:
Expand on the following scene description, giving more specific details about the non-player characters, location(s), and other world elements involved in the scene, as well as potential outcomes and consequences of the scene given the player characters' possible actions:
{self.scenes[idx]}
"""
        log(prompt, _print=True)
        self.scenes[idx] = self.campaign.world.system.generate_text(prompt)
        log(self.scenes[idx], _print=True)
        self.scenes[idx] = (
            markdown.markdown(
                self.scenes[idx].replace("```markdown", "").replace("```", "")
            )
            .replace("h1>", "h3>")
            .replace("h2>", "h3>")
        )
        self.save()
