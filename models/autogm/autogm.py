import random

import markdown
from bs4 import BeautifulSoup

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

    campaign = ReferenceAttr(choices=["Campaign"])

    def generate_episode(self, msg, associations):
        """
        Generates the next scene using the AutoGM framework.
        """
        prompt = f"""Generate a 5 act TTRPG session outline with clearly defined social interactions and combat encounters in MARKDOWN using the following structure:
Act 1: The Guardian or the Call to Adventure
Act 2: A roleplay opportunity or puzzle
Act 3: A battle or other resource drain
Act 4: The Final Showdown
Act 5: The twist or the resolution

{f"THE STORY SO FAR...\n\n{self.campaign.summary}" if self.campaign.summary else ""}

The player characters are described as follows:

- {"\n- ".join([f"{c.name} [{c.gender, c.age}]: {c.backstory}" for c in self.campaign.party.players])}

CAMPAIGN ELEMENTS TO BE INCORPORATED

- {"\n- ".join([f"{c.name} [{c.title}]: {c.backstory}" for c in associations if hasattr(c, "is_player") and not c.is_player])}


BASE THE SESSION OUTLINE ON THE FOLLOWING PROMPT:

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
        results = self.campaign.world.system.generate_text(
            prompt,
            primer="You are an expert AI in generating outlines for exciting and suspensful TTRPG sessions",
        )
        log(results, _print=True)
        results = (
            markdown.markdown(results.replace("```markdown", "").replace("```", ""))
            .replace("h1>", "h3>")
            .replace("h2>", "h3>")
        )
        return results

    def generate_scene(self, msg):
        msg = BeautifulSoup(msg, "html.parser").get_text()
        prompt = (
            "You are a TTRPG GM. Your party consists of the following characters:\n"
        )

        prompt += "\n".join(
            [
                f"- {c.name} [{c.gender, c.age}]: {c.backstory}"
                for c in self.campaign.party.players
            ]
        )

        prompt += f"""
GIVEN THE BELOW OUTLINE OF A TTRPG SESSION:
{msg}

INSTRUCTIONS:
Expand on the outline, giving more specific details about the non-player characters, location(s), and other world elements, as well as potential outcomes and consequences of each scene given the player characters' possible actions
"""

        result = self.campaign.world.system.generate_text(prompt)
        result = (
            markdown.markdown(result.replace("```markdown", "").replace("```", ""))
            .replace("h1>", "h3>")
            .replace("h2>", "h3>")
        )
        return result
