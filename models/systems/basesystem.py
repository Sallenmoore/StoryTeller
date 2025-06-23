import random
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

    _backgrounds = {
        "Acolyte": "You have spent your life in the service of a temple to a specific god or pantheon of gods. You act as an intermediary between the realm of the holy and the mortal world, performing sacred rites and offering sacrifices.",
        "Charlatan": "You have always had a way with people. You know what makes them tick, and you can tease out their hearts’ desires after a few minutes of conversation. You use this skill to your advantage in your line of work.",
        "Criminal": "You have a history of breaking the law. You have spent a lot of time among other criminals and still have contacts within the criminal underworld.",
        "Entertainer": "You thrive in front of an audience. You know how to entrance them, entertain them, and inspire them. Your poise, confidence, and theatrical flair make you a master of performance.",
        "Folk Hero": "You come from a humble social rank, but you are destined for so much more. The people of your home village regard you as their champion, and your destiny calls you to stand against the tyrants and monsters threatening the common folk everywhere.",
        "Guild Artisan": "You are a member of an artisan’s guild, skilled in a particular field and closely associated with other artisans. You are well established in the mercantile world, owning a shop and working with trade networks.",
        "Hermit": "You lived in seclusion—either in a sheltered community such as a monastery or entirely alone—for a formative part of your life. In your time apart from the clamor of society, you found quiet, solitude, and perhaps a bit of insanity.",
        "Noble": "You understand wealth, power, and privilege. You carry a noble title, and your family owns land, collects taxes, and wields significant political influence. You might be a pampered aristocrat or a disinherited scoundrel.",
        "Outlander": "You grew up in the wilds, far from civilization and the comforts of town and technology. You’ve witnessed the migration of herds larger than forests, survived weather more extreme than any city-dweller could comprehend, and enjoyed the solitude of being the only thinking creature for miles in any direction.",
        "Sage": "You spent years learning the lore of the multiverse. You scoured manuscripts, studied scrolls, and listened to the greatest experts on the subjects that interest you.",
        "Sailor": "You sailed on a seagoing vessel for years. In that time, you faced down mighty storms, monsters of the deep, and those who wanted to sink your craft to the bottomless depths.",
        "Soldier": "War has been your life for as long as you care to remember. You trained as a youth, studied the use of weapons and armor, learned survival strategies, and perhaps took part in a war.",
        "Urchin": "You grew up on the streets alone, orphaned, and poor. You had no one to watch over you or to provide for you, so you learned to provide for yourself. You fought fiercely over food and kept a constant watch out for other desperate souls who might take it from you.",
    }

    _classes = {
        "Artificer": [
            "TBD",
        ],
        "Barbarian": [
            "Path of the Berserker",
            "Path of the Totem Warrior",
            "Path of the Ancestral Guardian",
            "Path of the Battlerager",
            "Path of the Storm Herald",
            "Path of the Zealot",
            "Path of Wild Magic",
        ],
        "Bard": [
            "College of Lore",
            "College of Valor",
            "College of Glamour",
            "College of Swords",
            "College of Whispers",
            "College of Creation",
            "College of Eloquence",
        ],
        "Cleric": [
            "Arcana Domain",
            "Death Domain",
            "Forge Domain",
            "Grave Domain",
            "Knowledge Domain",
            "Life Domain",
            "Light Domain",
            "Nature Domain",
            "Order Domain",
            "Tempest Domain",
            "Trickery Domain",
            "War Domain",
        ],
        "Druid": [
            "Circle of Dreams",
            "Circle of the Land",
            "Circle of the Moon",
            "Circle of the Shepherd",
            "Circle of Spores",
            "Circle of Stars",
            "Circle of Wildfire",
        ],
        "Fighter": [
            "Arcane Archer",
            "Banneret",
            "Battle Master",
            "Cavalier",
            "Champion",
            "Echo Knight",
            "Eldritch Knight",
            "Psi Warrior",
            "Rune Knight",
            "Samurai",
        ],
        "Monk": [
            "Way of the Open Hand",
            "Way of Shadow",
            "Way of the Four Elements",
            "Way of the Drunken Master",
            "Way of the Kensei",
            "Way of the Sun Soul",
            "Way of Mercy",
            "Way of the Astral Self",
        ],
        "Paladin": [
            "Oath of Devotion",
            "Oath of the Ancients",
            "Oath of Vengeance",
            "Oath of the Crown",
            "Oath of Conquest",
            "Oath of Redemption",
            "Oath of Glory",
            "Oath of the Watchers",
        ],
        "Ranger": [
            "Beast Master Conclave",
            "Hunter Conclave",
            "Gloom Stalker Conclave",
            "Horizon Walker Conclave",
            "Monster Slayer Conclave",
            "Fey Wanderer",
            "Swarmkeeper",
        ],
        "Rogue": [
            "Arcane Trickster",
            "Assassin",
            "Inquisitive",
            "Mastermind",
            "Phantom",
            "Scout",
            "Soulknife",
            "Swashbuckler",
            "Thief",
        ],
        "Sorcerer": [
            "Divine Soul",
            "Draconic Bloodline",
            "Shadow Magic",
            "Storm Sorcery",
            "Wild Magic",
            "Aberrant Mind",
            "Clockwork Soul",
        ],
        "Warlock": [
            "The Archfey",
            "The Fiend",
            "The Great Old One",
            "The Celestial",
            "The Hexblade",
            "The Fathomless",
            "The Genie",
        ],
        "Wizard": [
            "School of Abjuration",
            "School of Conjuration",
            "School of Divination",
            "School of Enchantment",
            "School of Evocation",
            "School of Illusion",
            "School of Necromancy",
            "School of Transmutation",
            "Bladesinging",
            "Order of Scribes",
        ],
    }

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
- STYLE: Czepeku
- SCALE: 1 inch == 500 feet
{"- DESCRIPTION: " + obj.description if obj.description else ""}
{"- POINTS OF INTEREST: " + ",".join([poi.name for poi in [*obj.districts, *obj.locations] if poi.name]) if [poi.name for poi in obj.districts if poi.name] else ""}
""",
        "region": lambda obj: f"""Generate a top-down map of a {obj.title} suitable for a {obj.genre} tabletop RPG  in a location with the following description: {obj.description_summary}. The map should be detailed and include the following elements:
- STYLE: Czepeku
- MAP TYPE: top-down navigation map with key cities, locations, and pois marked
- SCALE: 1 inch == 50 miles
{"- DESCRIPTION: " + obj.description if obj.description else ""}
""",
        "world": lambda obj: f"""Generate a top-down map of a {obj.title} suitable for a {obj.genre} tabletop RPG in a {obj.title} with the following description: {obj.description_summary}. The map should be detailed and include the following elements:
- STYLE: Czepeku
- MAP TYPE: Directly overhead, top-down atlas style map of the {obj.title}
- SCALE: 1 inch == 500 miles
{"- DESCRIPTION: " + obj.description if obj.description else ""}
""",
        "location": lambda obj: f"""Generate a top-down navigable Table Top RPG battle map of a {obj.location_type} {obj.title} suitable for a {obj.genre} encounter in a location with the following description: {obj.description_summary}. The map should be detailed enough for players to clearly understand how to navigate the environment and include the following elements:
- STYLE: Czepeku
- MAP TYPE: directly overhead, top-down
- SCALE: 1 inch == 5 feet
{"- DESCRIPTION: " + obj.description if obj.description else ""}
""",
        "shop": lambda obj: f"""Generate a top-down navigable Table Top RPG  map of an establishment suitable for a {obj.genre} encounter in a location with the following description: {obj.description_summary}. The map should be detailed enough for players to clearly understand how to navigate the environment and include the following elements:
- STYLE: Czepeku
- MAP TYPE: directly overhead, top-down
- SCALE: 1 inch == 5 feet
{"- DESCRIPTION: " + obj.description if obj.description else ""}
""",
        "district": lambda obj: f"""Generate a top-down navigable Table Top RPG battle map of a {obj.title} suitable for a {obj.genre} encounter in a location with the following description: {obj.description_summary}. The map should be detailed enough for players to clearly understand how to navigate the environment and include the following elements:
- STYLE: Czepeku
- MAP TYPE: directly overhead, top-down
- SCALE: 1 inch == 5 feet
{"- DESCRIPTION: " + obj.description if obj.description else ""}
""",
        "vehicle": lambda obj: f"""Generate a top-down navigable Table Top RPG battle map of the floor plan of a {obj.type} with the following description: {obj.description_summary}. The map should be detailed enough for players to clearly understand how to navigate the environment and include the following elements:
- STYLE: Czepeku
- MAP TYPE: directly overhead, top-down
- SCALE: 1 inch == 5 feet
{"- DESCRIPTION: " + obj.description if obj.description else ""}
""",
    }
    _traits_list = {
        "city": [
            "bohemian",
            "rude",
            "aggressive",
            "proud",
            "distrustful",
            "anarchic",
            "aristocratic",
            "bureaucratic",
            "theocratic",
            "tribalist",
        ],
        "creature": [
            "aggressive",
            "cunning",
            "deceptive",
            "intelligent",
            "loyal",
            "savage",
            "sneaky",
            "vicious",
        ],
        "faction": [
            "colonists",
            "deep rooted",
            "cult",
            "suspicious",
            "violent",
            "sinister",
            "fanatical",
            "racist",
            "egalitarian",
            "ambitious",
            "corrupt",
            "charitable",
            "greedy",
            "generous",
            "imperialist",
            "isolationist",
            "mercenary",
        ],
        "region": [
            "coastal",
            "mountainous",
            "desert",
            "forest",
            "jungle",
            "plains",
            "swamp",
            "frozen",
            "underground",
        ],
        "world": [
            "bohemian",
            "rude",
            "aggressive",
            "proud",
            "distrustful",
            "anarchic",
            "aristocratic",
            "bureaucratic",
            "theocratic",
            "tribalist",
        ],
        "location": [
            "bohemian",
            "rude",
            "aggressive",
            "proud",
            "distrustful",
            "anarchic",
            "aristocratic",
            "bureaucratic",
            "theocratic",
            "tribalist",
        ],
        "shop": [
            "bohemian",
            "rude",
            "aggressive",
            "proud",
            "distrustful",
            "anarchic",
            "aristocratic",
            "bureaucratic",
            "theocratic",
            "tribalist",
        ],
        "vehicle": [
            "fast",
            "slow",
            "stealthy",
            "heavily armed",
            "heavily armored",
            "lightly armed",
            "lightly armored",
            "well designed",
            "poorly designed",
            "well maintained",
            "poorly maintained",
        ],
        "district": [
            "bohemian",
            "rude",
            "aggressive",
            "proud",
            "distrustful",
            "anarchic",
            "aristocratic",
            "bureaucratic",
            "theocratic",
            "tribalist",
        ],
        "item": [
            "common",
            "uncommon",
            "rare",
            "very rare",
            "legendary",
            "artifacts",
            "cursed",
            "sentient",
            "magical",
            "mundane",
            "unique",
        ],
        "encounter": [
            "easy",
            "difficult",
            "deadly",
            "ambush",
            "puzzle",
            "trap",
            "combat",
            "social",
            "exploration",
            "investigation",
            "stealth",
            "mystery",
        ],
        "character": [
            "secretly evil",
            "shy and gentle",
            "outgoing and imaginative",
            "unfriendly, but not unkind",
            "cruel and sadistic",
            "power-hungry and ambitious",
            "kind and helpful",
            "proud and self-absorbed",
            "silly, a prankster",
            "overly serious",
            "incredibly greedy",
            "extremely generous",
            "hardworking",
            "cowardly and insecure",
            "practical to a fault",
            "dangerously curious",
            "cautious and occasionally paranoid",
            "reckless, but heroic",
            "Ambition",
            "Avarice",
            "Bitterness",
            "Courage",
            "Cowardice",
            "Curiosity",
            "Deceitfulness",
            "Determination",
            "Devotion to a cause",
            "Filiality",
            "Hatred",
            "Honesty",
            "Hopefulness",
            "Love of a person",
            "Nihilism",
            "Paternalism",
            "Pessimism",
            "Protectiveness",
            "Resentment",
            "Shame",
        ],
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

    @property
    def classes(self):
        return self._classes

    @property
    def backgrounds(self):
        return self._backgrounds

    ############# CRUD Methods #############

    def get_title(self, model):
        return self._titles.get(model, "Object")

    def get_skills(self, actor=None):
        if actor:
            # log(actor.dexterity, (actor.dexterity - 10) // 2)
            result = {
                "Acrobatics": (int(actor.dexterity) - 10) // 2,
                "Animal Handling": (int(actor.charisma) - 10) // 2,
                "Arcana": (int(actor.intelligence) - 10) // 2,
                "Athletics": (int(actor.dexterity) - 10) // 2,
                "Deception": (int(actor.charisma) - 10) // 2,
                "History": (int(actor.intelligence) - 10) // 2,
                "Insight": (int(actor.wisdom) - 10) // 2,
                "Intimidation": (int(actor.charisma) - 10) // 2,
                "Investigation": (int(actor.intelligence) - 10) // 2,
                "Medicine": (int(actor.intelligence) - 10) // 2,
                "Nature": (int(actor.intelligence) - 10) // 2,
                "Perception": (int(actor.wisdom) - 10) // 2,
                "Performance": (int(actor.charisma) - 10) // 2,
                "Persuasion": (int(actor.charisma) - 10) // 2,
                "Religion": (int(actor.wisdom) - 10) // 2,
                "Sleight of Hand": (int(actor.dexterity) - 10) // 2,
                "Stealth": (int(actor.dexterity) - 10) // 2,
                "Survival": (int(actor.wisdom) - 10) // 2,
            }
        else:
            result = {
                "Acrobatics": random.randint(-2, 5),
                "Animal Handling": random.randint(-2, 5),
                "Arcana": random.randint(-2, 5),
                "Athletics": random.randint(-2, 5),
                "Deception": random.randint(-2, 5),
                "History": random.randint(-2, 5),
                "Insight": random.randint(-2, 5),
                "Intimidation": random.randint(-2, 5),
                "Investigation": random.randint(-2, 5),
                "Medicine": random.randint(-2, 5),
                "Nature": random.randint(-2, 5),
                "Perception": random.randint(-2, 5),
                "Performance": random.randint(-2, 5),
                "Persuasion": random.randint(-2, 5),
                "Religion": random.randint(-2, 5),
                "Sleight of Hand": random.randint(-2, 5),
                "Stealth": random.randint(-2, 5),
                "Survival": random.randint(-2, 5),
            }
        # log(result)
        return result

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

    def generate_json(self, prompt, primer, funcobj):
        prompt = self.sanitize(prompt)
        response = self.json_agent.generate(
            prompt, function=funcobj, additional_instructions=primer
        )
        return response

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
