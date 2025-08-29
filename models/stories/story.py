import random

from autonomous import log
from autonomous.model.autoattr import DictAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.base.ttrpgbase import TTRPGBase


class Story(AutoModel):
    name = StringAttr(default="")
    scope = StringAttr(default="Local")
    situation = StringAttr(default="")
    current_status = StringAttr(default="")
    backstory = StringAttr(default="")
    tasks = ListAttr(StringAttr(default=""))
    rumors = ListAttr(StringAttr(default=""))
    information = ListAttr(StringAttr(default=""))
    bbeg = ReferenceAttr(choices=["Character"])
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    encounters = ListAttr(ReferenceAttr(choices=["Encounter"]))
    events = ListAttr(ReferenceAttr(choices=["Event"]))
    world = ReferenceAttr(choices=["World"])

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
                    "description": "A list of tasks that the player characters must complete to advance the story. These tasks should be relevant to the situation and provide a scenario for the player characters to engage with the story.",
                    "items": {"type": "string"},
                },
                "rumors": {
                    "type": "array",
                    "description": "A list of rumors that will draw the players in and cause the player characters to want to learn more about the situation, in the order they should be revealed. Rumors are not always true, but they should be relevant to the situation and provide useful information to the player characters.",
                    "items": {"type": "string"},
                },
                "information": {
                    "type": "array",
                    "description": " A list of information that the player characters can discover about the situation, in the order they should be revealed. This information should be relevant to the situation and provide useful context for the player characters.",
                    "items": {"type": "string"},
                },
            },
        },
    }

    def generate(self):
        prompt = f"Your task is to create a new storyline for the following {self.world.genre} TTRPG world. The story should incorporate existing world elements and relationships. The storyline can range from a local event to a global paradigm shift; however, the plot must include elements that can benefit from outside assistance or interference. Here is some context about the world: {self.world.name}, {self.world.description}. "

        if self.world.stories:
            prompt += "\n\nHere are some existing storylines in the world: "
            for story in random.sample(
                self.world.stories, min(len(self.world.stories), 3)
            ):
                prompt += f"\n\n{story.name}: {story.situation}. "
        if self.world.cities:
            city = random.choice(self.world.cities)
            prompt += f"\n\nHere is some context about a random city in the world: {city.name}, {city.description}. "
            if city.government:
                prompt += f"\n\nThe city is governed by {city.government}. "
            if city.ruler:
                prompt += f"\n\nThe ruler of the city is {city.ruler.name}, {city.ruler.description}. "
            if city.factions:
                faction = random.choice(city.factions)
                prompt += f"\n\nOne of the factions in the city is {faction.name}, {faction.description}. "
            if city.districts:
                district = random.choice(city.districts)
                prompt += f"\n\nOne of the districts in the city is {district.name}, {district.description}. "
            if city.locations:
                location = random.choice(city.locations)
                prompt += f"\n\nOne of the locations in the city is {location.name}, {location.description}. "
            if city.characters:
                character = random.choice(city.characters)
                prompt += f"\n\nOne of the notable characters in the city is {character.name}, {character.description}. "
            if city.creatures:
                creature = random.choice(city.creatures)
                prompt += f"\n\nOne of the notable creatures in the city is {creature.name}, {creature.description}. "
            if city.items:
                item = random.choice(city.items)
                prompt += f"\n\nOne of the notable items in the city is {item.name}, {item.description}. "
            if city.vehicles:
                vehicle = random.choice(city.vehicles)
                prompt += f"\n\nOne of the notable vehicles in the city is {vehicle.name}, {vehicle.description}. "

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
