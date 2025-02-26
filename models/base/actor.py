import random

import markdown
from bs4 import BeautifulSoup

from autonomous import log
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
from models.ttrpgobject.ability import Ability
from models.ttrpgobject.ttrpgobject import TTRPGObject


class Actor(TTRPGObject):
    meta = {"abstract": True, "allow_inheritance": True, "strict": False}
    goal = StringAttr(default="")
    is_player = BoolAttr(default=False)
    level = IntAttr(default=1)
    gender = StringAttr(default="")
    age = IntAttr(default=0)
    species = StringAttr(default="")
    abilities = ListAttr(ReferenceAttr(choices=["Ability"]))
    hitpoints = IntAttr(default=30)
    status = StringAttr(default="healthy")
    ac = IntAttr(default=10)
    current_hitpoints = IntAttr(default=10)
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
    audio = FileAttr(default="")

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
            "description": "goals and closely guarded secrets",
        },
        "abilities": {
            "type": "array",
            "description": "Generate at least 2 offensive combat, 2 defensive combat AND 2 roleplay special ability objects for the array. Each object in the array should have attributes for the ability name, type of action, detailed description in MARKDOWN, effects, duration, and the dice roll mechanics involved in using the ability.",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "name",
                    "action",
                    "description",
                    "effects",
                    "duration",
                    "dice_roll",
                ],
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Unique name for the Ability.",
                    },
                    "action": {
                        "type": "string",
                        "enum": [
                            "main action",
                            "bonus action",
                            "reaction",
                            "free action",
                            "passive",
                        ],
                        "description": "type of action required.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the ability and how the Character aquired the ability in MARKDOWN.",
                    },
                    "effects": {
                        "type": "string",
                        "description": "Description of the ability's effects.",
                    },
                    "duration": {
                        "type": "string",
                        "description": "The duration of the ability's effects.",
                    },
                    "dice_roll": {
                        "type": "string",
                        "description": "The dice roll mechanics for determining the success or failure of the ability.",
                    },
                },
            },
        },
        "archetype": {
            "type": "string",
            "description": "archetype or role in the world, such as Rogue, Wizard, Soldier, etc.",
        },
        "hitpoints": {
            "type": "integer",
            "description": "maximum hit points",
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
            _voices = [
                "alloy",
                "echo",
                "fable",
                "onyx",
                "nova",
                "shimmer",
            ]
            if self.gender.lower() == "male":
                if self.age < 30:
                    self.pc_voice = random.choice(["alloy", "echo", "fable"])
                else:
                    self.pc_voice = random.choice(["onyx", "echo"])
            elif self.gender.lower() == "female":
                if self.age < 30:
                    self.pc_voice = random.choice(["nova", "shimmer"])
                else:
                    self.pc_voice = random.choice(["fable", "shimmer"])
            else:
                self.pc_voice = random.choice(_voices)
            self.save()
        return self.pc_voice

    def generate(self, prompt=""):
        self._funcobj["parameters"]["properties"] |= Actor._funcobj
        super().generate(prompt)

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
        document.pre_save_skills()

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_ac()
        document.pre_save_ability()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ############### Verification Methods ##############

    def pre_save_skills(self):
        if not self.skills:
            self.skills = self.system.skills.copy()

    def pre_save_ac(self):
        self.ac = max(
            10,
            ((int(self.dexterity) - 10) // 2) + ((int(self.strength) - 10) // 2) + 10,
        )

    def pre_save_ability(self):
        for idx, ability in enumerate(self.abilities):
            if isinstance(ability, str):
                a = Ability(description=ability)
                a.save()
                self.abilities[idx] = a
            elif isinstance(ability, dict):
                a = Ability(**ability)
                a.save()
                self.abilities[idx] = a
            else:
                ability.description = (
                    markdown.markdown(
                        ability.description.replace("```markdown", "").replace(
                            "```", ""
                        )
                    )
                    .replace("h1>", "h3>")
                    .replace("h2>", "h3>")
                )

        self.abilities = [a for a in self.abilities if a.name]
