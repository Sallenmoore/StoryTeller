import random

import markdown
import requests
from autonomous.ai.audioagent import AudioAgent
from autonomous.model.autoattr import (
    BoolAttr,
    DictAttr,
    FileAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from bs4 import BeautifulSoup

from autonomous import log
from models.audio.audio import Audio
from models.ttrpgobject.ability import Ability
from models.ttrpgobject.ttrpgobject import TTRPGObject
from models.utility import tasks as utility_tasks


class Actor(TTRPGObject):
    meta = {"abstract": True, "allow_inheritance": True, "strict": False}
    goal = StringAttr(default="")
    level = IntAttr(default=1)
    gender = StringAttr(default="")
    faction = ReferenceAttr(choices=["Faction"])
    age = IntAttr(default=0)
    species = StringAttr(default="")
    abilities = ListAttr(ReferenceAttr(choices=["Ability"]))
    hitpoints = IntAttr(default=30)
    ac = IntAttr(default=10)
    speed = IntAttr(default=30)
    speed_units = StringAttr(default="ft")
    strength = IntAttr(default=10)
    dexterity = IntAttr(default=10)
    constitution = IntAttr(default=10)
    wisdom = IntAttr(default=10)
    intelligence = IntAttr(default=10)
    charisma = IntAttr(default=10)
    archetype = StringAttr(default="")
    voice_description = StringAttr(default="")
    lookalike = StringAttr(default="")
    skills = DictAttr(default={})
    pc_voice = StringAttr(default="")
    chat_summary = StringAttr(default="")
    chats = ListAttr(DictAttr(default={}))
    audio = FileAttr()

    _genders = ["male", "female", "non-binary"]

    _funcobj = {
        "name": {
            "type": "string",
            "description": "A unique and unusual first, middle, and last name",
        },
        "gender": {
            "type": "string",
            "description": "preferred gender",
        },
        "status": {
            "type": "string",
            "description": "current, immediate situation the actor is in, such as working as an artisan, exploring a location, resting at an safe house, etc.",
        },
        "age": {
            "type": "integer",
            "description": "physical age in years",
        },
        "voice_description": {
            "type": "string",
            "description": "where applicable, description of the voice including pitch, placement (i.e. throaty to nasally), tempo, volume, tone, and accent",
        },
        "lookalike": {
            "type": "string",
            "description": "A public figure or character that the npc looks like",
        },
        "species": {
            "type": "string",
            "description": "species, such as human, orc, monster, etc.",
        },
        "traits": {
            "type": "string",
            "description": "A tag line or motif that describes the character",
        },
        "desc": {
            "type": "string",
            "description": "A detailed physical description optimized for AI image generation of the NPC",
        },
        "backstory": {
            "type": "string",
            "description": "detailed backstory that includes only publicly known information about the NPC, being careful not to reveal sensitive information or secrets",
        },
        "goal": {
            "type": "string",
            "description": "The character's public and private goals. The public goal is what the character tells others, while the private goal is what the character truly desires. The character goials should be at least tangentially related to an existing world story",
        },
        "archetype": {
            "type": "string",
            "description": "archetype or role in the world, such as Rogue, Wizard, Soldier, etc.",
        },
        "hitpoints": {
            "type": "integer",
            "description": "maximum hit points",
        },
        "speed": {
            "type": "integer",
            "description": "the amount of movement units the actor has per round, where the average is 30",
        },
        "speed_units": {
            "type": "string",
            "description": "the units of measurement for the actor's speed (e.g., feet, meters)",
        },
        "strength": {
            "type": "integer",
            "description": "The amount of Strength from 1-20",
        },
        "dexterity": {
            "type": "integer",
            "description": "The amount of Dexterity from 1-20",
        },
        "constitution": {
            "type": "integer",
            "description": "The amount of Constitution from 1-20",
        },
        "intelligence": {
            "type": "integer",
            "description": "The amount of Intelligence from 1-20",
        },
        "wisdom": {
            "type": "integer",
            "description": "The amount of Wisdom from 1-20",
        },
        "charisma": {
            "type": "integer",
            "description": "The amount of Charisma from 1-20",
        },
        "sensory_details": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of sensory details, such as sight, sound, smell, and touch, that a GM can use to bring the character to life",
        },
    }

    @property
    def last_chat(self):
        return self.chats[-1] if self.chats else {}

    @property
    def map(self):
        return self.parent.map if self.parent else None

    @property
    def race(self):
        return self.species

    @race.setter
    def race(self, value):
        self.species = value

    @property
    def voice(self):
        if not self.pc_voice:
            self.pc_voice = Audio.get_voice(filters=[self.gender.lower()])
            self.save()
        return self.pc_voice

    def generate(self, prompt=""):
        self._funcobj["parameters"]["properties"] |= Actor._funcobj
        prompt += f"""
{f"ABILITIES: {self.abilities}" if self.abilities else ""}
"""
        super().generate(prompt)
        if not self.abilities:
            for _ in range(random.randint(1, 6)):
                ability = Ability(
                    world=self.world,
                    type=self.model_name().lower(),
                )
                ability.save()
                self.abilities.append(ability)
                self.save()
                utility_tasks.start_task(f"/generate/ability/{ability.pk}")

    def speak(self, message):
        return Audio.tts(
            audio_text=self.verbal,
            voice=self.voice,
        )

    def chat(self, message=""):
        # summarize conversation
        if self.chats and self.chats[-1]["pc"] and self.chats[-1]["npc"]:
            primer = f"""As an expert AI in {self.world.genre} TTRPG Worldbuilding, use the previous chat CONTEXT as a starting point to generate a readable summary from the PLAYER MESSAGE and NPC RESPONSE that clarifies the main points of the conversation.
            """
            text = f"""
            CONTEXT:\n{self.chat_summary or "This is the beginning of the conversation."}
            PLAYER MESSAGE:\n{self.chats[-1]["pc"]}
            NPC RESPONSE:\n{self.chats[-1]["npc"]}"
            """

            self.chat_summary = self.system.text_agent.summarize_text(
                text, primer=primer
            )

        message = message.strip() or "Tell me a little more about yourself..."
        primer = f"You are playing the role of a {self.gender} NPC named {self.name} who is talking to a Player. You should reference the Character model information in the uploaded file with the primary key: {self.pk}."
        prompt = "Respond as the NPC matching the following description:"
        prompt += f"""
            MOTIF: {self.traits}

            DESCRIPTION: {self.desc}

            BACKSTORY: {self.backstory}

            SECRET GOAL: {self.goal}

        Use the following chat CONTEXT as a starting point:

        CONTEXT: {self.chat_summary or "This is the beginning of the conversation."}

        PLAYER MESSAGE: {message}
        """

        response = self.system.generate_text(prompt, primer)
        self.chats += [{"pc": message, "npc": response}]
        self.save()

        npc_message = BeautifulSoup(response, "html.parser").get_text()
        voice = self.voice if hasattr(self, "voice") else "onyx"
        voiced_scene = AudioAgent().generate(npc_message, voice=voice)
        if self.audio:
            self.audio.delete()
            self.audio.replace(voiced_scene, content_type="audio/mpeg")
        else:
            self.audio.put(voiced_scene, content_type="audio/mpeg")
        self.save()

        return self.chats

    def clear_chat(self):
        self.chats = []
        self.save()

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    @classmethod
    def auto_post_init(cls, sender, document, **kwargs):
        super().auto_post_init(sender, document, **kwargs)
        document.pre_save_ac()

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_ac()
        document.pre_save_ability()
        document.pre_save_skills()
        document.pre_save_faction()

        ###### MIGRATION CODE ######
        for ability in document.abilities:
            ability.world = document.world
            ability.save()
        ############################

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ############### Verification Methods ##############

    def pre_save_skills(self):
        # log(self.skills.items(), _print=True)
        if not self.skills or all(
            isinstance(v, list) or not v or int(v) <= 0 for k, v in self.skills.items()
        ):
            self.skills = self.system.get_skills(self)
            # log(f"pre_save_skills: {self.skills}")

    def pre_save_ac(self):
        if not self.ac or self.ac == 10:
            self.ac = max(
                10,
                ((int(self.dexterity) - 10) // 2)
                + ((int(self.strength) - 10) // 2)
                + 10,
            )

    def pre_save_ability(self):
        for idx, ability in enumerate(self.abilities):
            if isinstance(ability, str):
                a = Ability(world=self.world, description=ability)
                a.save()
                self.abilities[idx] = a
            elif isinstance(ability, dict):
                a = Ability(world=self.world, **ability)
                a.save()
                self.abilities[idx] = a

        self.abilities = [a for a in self.abilities if a]

    def pre_save_faction(self):
        from models.ttrpgobject.faction import Faction

        if isinstance(self.faction, str):
            self.faction = Faction.get(self.faction)
        elif self.faction and not isinstance(self.faction, Faction):
            log(f"pre_save_faction: {self.faction}")
            raise ValueError(
                "Invalid faction reference: must be a Faction pk or object."
            )
