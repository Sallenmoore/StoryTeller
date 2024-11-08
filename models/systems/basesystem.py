import inspect
import json
import re

from bs4 import BeautifulSoup

from autonomous import log
from autonomous.ai.jsonagent import JSONAgent
from autonomous.ai.textagent import TextAgent
from autonomous.db import ValidationError
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
        "poi": "POI",
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

    _map_prompts = {
        "city": lambda obj: f"""Generate a top-down map of a {obj.title} suitable for a {obj.genre} tabletop RPG. The map should be detailed and include the following elements:
            - MAP TYPE: A detailed layout of the {obj.title}, including key locations, points of interest, and districts
            - SCALE: 1 inch == 500 feet
            {"- CONTEXT: " + obj.backstory_summary if obj.backstory_summary else ""}
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            {"- POINTS OF INTEREST: " + ",".join([poi.name for poi in [*obj.pois, *obj.locations] if poi.name]) if [poi.name for poi in obj.pois if poi.name] else ""}
            """,
        "region": lambda obj: f"""Generate a top-down map of a {obj.title} suitable for a {obj.genre} tabletop RPG. The map should be detailed and include the following elements:
            - MAP TYPE: top-down navigation map with key cities, locations, and pois marked
            - SCALE: 1 inch == 50 miles
            {"- CONTEXT: " + obj.backstory_summary if obj.backstory_summary else ""}
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            """,
        "world": lambda obj: f"""Generate a top-down navigable map of a {obj.title} suitable for a {obj.genre} tabletop RPG. The map should be detailed and include the following elements:
            - MAP TYPE: Directly overhead, top-down atlas style map of the {obj.title}
            - SCALE: 1 inch == 500 miles
            {"- CONTEXT: " + obj.backstory_summary if obj.backstory_summary else ""}
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            """,
        "location": lambda obj: f"""Generate a top-down navigable Table Top RPG battle map of a {obj.location_type} suitable for a {obj.genre} encounter. The map should be detailed enough for players to clearly understand how to navigate the environment and include the following elements:
            - MAP TYPE: directly overhead, top-down
            - SCALE: 1 inch == 5 feet
            {"- CONTEXT: " + obj.backstory_summary if obj.backstory_summary else ""}
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            """,
        "poi": lambda obj: f"""Generate a top-down navigable Table Top RPG battle map of a {obj.location_type} suitable for a {obj.genre} encounter. The map should be detailed enough for players to clearly understand how to navigate the environment and include the following elements:
            - MAP TYPE: directly overhead, top-down
            - SCALE: 1 inch == 5 feet
            {"- CONTEXT: " + obj.backstory_summary if obj.backstory_summary else ""}
            {"- DESCRIPTION: " + obj.description if obj.description else ""}
            """,
    }

    ############# Class Methods #############

    @classmethod
    def get_title(cls, obj_type):
        if inspect.isclass(obj_type):
            obj_type = obj_type.__name__
        elif not isinstance(obj_type, str):
            obj_type = obj_type.__class__.__name__
        obj_type = obj_type.lower()
        return cls._titles.get(obj_type, obj_type.capitalize())

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

    ############# Generation Methods #############
    def update_refs(self, agent=None):
        world_data = self.world.page_data()
        if self.text_agent:
            self.text_agent.get_client().clear_files()
            ref_db = json.dumps(world_data).encode("utf-8")
            self.text_agent.attach_file(
                ref_db, filename=f"{self.world.slug}-dbdata.json"
            )

        if self.json_agent:
            self.json_agent.get_client().clear_files()
            ref_db = json.dumps(world_data).encode("utf-8")
            self.json_agent.attach_file(
                ref_db, filename=f"{self.world.slug}-dbdata.json"
            )

    def generate(self, obj, prompt):
        additional = f"\n\nIMPORTANT: The generated data must be new, unique, consistent with, and connected to the world data described by the uploaded reference file. If existing data is present in the object, expand on the {obj.title} data by adding greater specificity where possible, while ensuring the original concept remains unchanged. The result must be in VALID JSON format."
        prompt = self.sanitize(prompt)
        # log(f"=== generation prompt ===\n\n{prompt}", _print=True)
        response = self.json_agent.generate(
            prompt, function=obj.funcobj, additional_instructions=additional
        )
        # log(f"=== generation response ===\n\n{response}", _print=True)
        return response

    def chat(self, prompt, primer):
        prompt = self.sanitize(prompt)
        log(f"=== generation primer and prompt ===\n\n{primer}\n\n{prompt}")
        response = self.text_agent.generate(prompt, additional_instructions=primer)
        log(f"=== generation response ===\n\n{response}")
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
            summary += f"{self.text_agent.summarize_text(summary+p, primer=primer)}"

        return summary
