import re

from bs4 import BeautifulSoup

from autonomous import log
from autonomous.ai.jsonagent import JSONAgent
from autonomous.ai.textagent import TextAgent
from autonomous.model.autoattr import (
    ReferenceAttr,
)
from autonomous.model.automodel import AutoModel


class BaseSystem(AutoModel):
    meta = {
        "abstract": True,
        "allow_inheritance": True,
        "strict": False,
    }
    text_client = ReferenceAttr(choices=[TextAgent])
    json_client = ReferenceAttr(choices=[JSONAgent])
    world = ReferenceAttr(choices=["World"])

    _genre = "Mixed"
    MAX_TOKEN_LENGTH = 7500
    _titles = {
        "city": "City",
        "creature": "Creature",
        "faction": "Faction",
        "region": "Region",
        "world": "World",
        "location": "Location",
        "shop": "Shop",
        "vehicle": "Vehicle",
        "district": "District",
        "item": "Item",
        "encounter": "Encounter",
        "character": "Character",
    }

    _stats = {
        "strength": "STR",
        "dexterity": "DEX",
        "constitution": "CON",
        "intelligence": "INT",
        "wisdom": "WIS",
        "charisma": "CHA",
        "hit_points": "HP",
        "armor_class": "AC",
    }

    _currency = {
        "money": "gold pieces",
    }

    _music_lists = {
        "social": ["themesong.mp3"],
        "encounter": [
            "skirmish4.mp3",
            "skirmish3.mp3",
            "skirmish2.mp3",
            "skirmish1.mp3",
        ],
        "combat": [
            "battle2.mp3",
            "battle4.mp3",
            "battle3.mp3",
            "battle5.mp3",
        ],
        "exploration": ["relaxed1.mp3"],
        "investigation": [
            "creepy1.mp3",
            "creepy2.mp3",
            "creepy3.mp3",
            "creepy4.mp3",
            "creepy5.mp3",
            "creepy6.mp3",
            "creepy7.mp3",
        ],
        "puzzle": ["pursuit1.mp3", "puzzle2.mp3", "puzzle3.mp3", "puzzle4.mp3"],
        "stealth": [
            "suspense1.mp3",
            "suspense2.mp3",
            "suspense3.mp3",
            "suspense4.mp3",
            "suspense5.mp3",
            "suspense6.mp3",
            "suspense7.mp3",
        ],
    }

    _map_prompts = {
        "city": lambda obj: f"""Generate a top-down map of a {obj.title} suitable for a {obj.genre} tabletop RPG. The map should be detailed and include the following elements:
            - MAP TYPE: A detailed layout of the {obj.title}, including key locations, points of interest, and districts
            - SCALE: 1 inch == 500 feet
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            {"- POINTS OF INTEREST: " + ",".join([poi.name for poi in [*obj.districts, *obj.locations] if poi.name]) if [poi.name for poi in obj.districts if poi.name] else ""}
            """,
        "region": lambda obj: f"""Generate a top-down map of a {obj.title} suitable for a {obj.genre} tabletop RPG. The map should be detailed and include the following elements:
            - MAP TYPE: top-down navigation map with key cities, locations, and pois marked
            - SCALE: 1 inch == 50 miles
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            """,
        "world": lambda obj: f"""Generate a top-down navigable map of a {obj.title} suitable for a {obj.genre} tabletop RPG. The map should be detailed and include the following elements:
            - MAP TYPE: Directly overhead, top-down atlas style map of the {obj.title}
            - SCALE: 1 inch == 500 miles
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            """,
        "location": lambda obj: f"""Generate a top-down navigable Table Top RPG battle map of a {obj.location_type} {obj.title} suitable for a {obj.genre} encounter. The map should be detailed enough for players to clearly understand how to navigate the environment and include the following elements:
            - MAP TYPE: directly overhead, top-down
            - SCALE: 1 inch == 5 feet
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            """,
        "district": lambda obj: f"""Generate a top-down navigable Table Top RPG battle map of a {obj.title} suitable for a {obj.genre} encounter. The map should be detailed enough for players to clearly understand how to navigate the environment and include the following elements:
            - MAP TYPE: directly overhead, top-down
            - SCALE: 1 inch == 5 feet
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            """,
        "vehicle": lambda obj: f"""Generate a top-down navigable Table Top RPG battle map of the floor plan of a {obj.type}. The map should be detailed enough for players to clearly understand how to navigate the environment and include the following elements:
            - MAP TYPE: directly overhead, top-down
            - SCALE: 1 inch == 5 feet
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            """,
    }

    ############# Class Methods #############

    @classmethod
    def sanitize(cls, data):
        if isinstance(data, str):
            data = BeautifulSoup(data, "html.parser").get_text()
        return data

    @classmethod
    def map_prompt(cls, obj):
        return f"""{cls._map_prompts[obj.model_name().lower()](obj)}

    !!IMPORTANT!!: DIRECTLY OVERHEAD TOP DOWN VIEW, NO TEXT, NO CREATURES, NO CHARACTERS
    """

    ############# Property Methods #############

    @property
    def text_agent(self):
        if not self.text_client:
            log("Creating new text agent...")
            self.text_client = TextAgent(
                name=f"{self._genre} TableTop RPG Worldbuiding Content Agent",
                instructions=self.instructions,
                description=self.description,
            )
            self.text_client.save()
            self.save()
            log(f"Created new text agent with id: {self.text_client.get_agent_id()}")
        return self.text_client

    @property
    def json_agent(self):
        if not self.json_client:
            log("Creating new json agent...")
            self.json_client = JSONAgent(
                name=f"{self._genre} TableTop RPG Worldbuiding JSON Agent",
                instructions=self.instructions,
                description=self.description,
            )
            self.json_client.save()
            self.save()
        return self.json_client

    @property
    def instructions(self):
        return f"""You are highly skilled and creative AI trained to assist completing the object data for a {self._genre} Table Top RPG. The existing data is provided as structured JSON data describing the schema for characters, creatures, items, locations, encounters, and storylines. You should rephrase and expand on the object's existing data where appropriate, but not ignore it.

        Use the uploaded file to reference existing world objects and their existing connections while generating creative new data to expand the world. While the new enitity should be unique, there should also be appropriate connections to one or more existing elements in the world as described by the uploaded file."""

    @property
    def description(self):
        return f"A helpful AI assistant trained to return structured JSON data for help in world-building a consistent, mysterious, and dangerous universe as the setting for a series of {self._genre} TTRPG campaigns."

    ############# CRUD Methods #############

    def get_title(self, model):
        return self._titles.get(model, "Object")

    def delete(self):
        if self.text_client:
            self.text_client.delete()
        if self.json_client:
            self.json_client.delete()
        return super().delete()

    ############# Generation Methods #############

    def generate(self, obj, prompt, funcobj):
        additional = f"\n\nIMPORTANT: The generated data must be new, unique, consistent with, and connected to the world data described by the uploaded reference file. If existing data is present in the object, expand on the {obj.title} data by adding greater specificity where possible, while ensuring the original concept remains unchanged. The result must be in VALID JSON format."
        prompt = self.sanitize(prompt)
        log(f"=== generation prompt ===\n\n{prompt}", _print=True)
        log(f"=== generation function ===\n\n{funcobj}", _print=True)
        response = self.json_agent.generate(
            prompt, function=funcobj, additional_instructions=additional
        )
        log(f"=== generation response ===\n\n{response}", _print=True)
        return response

    def generate_text(self, prompt, primer=""):
        prompt = self.sanitize(prompt)
        return self.text_agent.generate(prompt, additional_instructions=primer)

    def generate_summary(self, prompt, primer=""):
        prompt = self.sanitize(prompt)
        updated_prompt_list = []
        # Find all words in the prompt
        words = re.findall(r"\w+", prompt)

        # Split the words into chunks
        for i in range(0, len(words), self.MAX_TOKEN_LENGTH):
            # Join a chunk of words and add to the list
            updated_prompt_list.append(" ".join(words[i : i + self.MAX_TOKEN_LENGTH]))

        summary = ""
        for p in updated_prompt_list:
            summary += f"{self.text_agent.summarize_text(summary + p, primer=primer)}"

        return summary
