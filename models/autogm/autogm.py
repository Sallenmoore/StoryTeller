import random

import markdown

from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel


class AutoGM(AutoModel):
    """
    AutoGM is a class for generating and managing graphs using the AutoGM framework.
    """

    world = ReferenceAttr("World", default=None)
    quest = ReferenceAttr("Quest", default=None)
    player = ReferenceAttr("Character", default=None)
    episode = StringAttr(default="")
    scenes = ListAttr(StringAttr(default=""))
    summary = StringAttr(default="The beginning of the ttrpg session.")
    party = ReferenceAttr("Faction", default=None)

    def generate_episode(self):
        """
        Generates a campaign using the AutoGM framework.
        """
        npc = random.choice([c for c in self.world.characters if not c.is_player])
        if not npc.quests:
            npc.generate_quest()
        self.quest = random.choice(npc.quests)
        self.save()
        prompt = f"""Generate a 5 act TTRPG session outline in MARKDOWN using the following structure:
    Act 1: The Guardian or the Call to Adventure
    Act 2: A roleplay opportunity or puzzle
    Act 3: A battle or other resource drain
    Act 4: The Final Showdown
    Act 5: The twist or the resolution

The session starts in the following location:
    {self.quest.location}

Base the story on the following mystery:
    {self.quest.description}
"""
        self.episode = self.world.system.generate_text(prompt)
        self.episode = (
            markdown.markdown(
                self.episode.replace("```markdown", "").replace("```", "")
            )
            .replace("h1>", "h3>")
            .replace("h2>", "h3>")
        )
        self.save()
