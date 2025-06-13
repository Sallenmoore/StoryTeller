import random

import markdown

from autonomous import log
from autonomous.model.autoattr import (
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from models.base.actor import Actor


class Character(Actor):
    dnd_beyond_id = StringAttr(default="")
    occupation = StringAttr(default="")
    wealth = ListAttr(StringAttr(default=""))
    quests = ListAttr(ReferenceAttr(choices=["Quest"]))

    parent_list = ["Location", "District", "Faction", "City", "Vehicle", "Shop"]

    _template = [
        [
            "Criminal, thug, thief, swindler",
            "Menial, cleaner, retail worker, servant",
            "Unskilled heavy labor, porter, construction",
            "Skilled trade, electrician, mechanic, pilot",
            "Idea worker, programmer, writer",
            "Merchant, business owner, trader, banker",
            "Official, bureaucrat, courtier, clerk",
            "Military, soldier, enforcer, law officer",
        ],
        [
            "The local underclass",
            "Common laborer",
            "Aspiring bourgeoise or upper class",
            "The elite of this society",
            "Minority or foreigner",
            "Offworlders or exotic",
        ],
        [
            "They have significant debt or money woes",
            "A loved one is in trouble",
            "Romantic failure with a desired person",
            "Drug or behavioral addiction",
            "Their superior dislikes or resents them",
            "They have a persistent sickness",
            "They hate their job or life situation",
            "Someone dangerous is targeting them",
            "They're pursuing a disastrous purpose",
            "They have no problems worth mentioning",
        ],
        [
            "Unusually young or old for their role",
            "Young adult",
            "Mature prime",
            "Middle-aged or elderly",
        ],
        [
            "They want a particular romantic partner",
            "They want money for them or a loved one",
            "They want a promotion in their job",
            "They want answers about a past trauma",
            "They want revenge on an enemy",
            "They want to help a beleaguered friend",
            "They want an entirely different job",
            "They want protection from an enemy",
            "They want to leave their current life",
            "They want fame and glory",
            "They want power over those around them",
            "They have everything they want from life",
        ],
    ]

    _funcobj = {
        "name": "generate_npc",
        "description": "creates, completes, and expands on the attributes and story of an existing NPC",
        "parameters": {
            "type": "object",
            "properties": {
                "occupation": {
                    "type": "string",
                    "description": "The NPC's profession or daily occupation",
                },
            },
        },
    }

    ################# Instance Properities #################

    @property
    def child_key(self):
        return "players" if self.is_player else "characters"

    @property
    def history_primer(self):
        return "Incorporate the below LIFE EVENTS into the BACKSTORY to generate a chronological summary of the character's history in MARKDOWN format with paragraph breaks after no more than 4 sentences."

    @property
    def history_prompt(self):
        if self.age and self.backstory_summary:
            return f"""
AGE
---
{self.age}

BACKSTORY
---
{self.backstory_summary}

LIFE EVENTS
---
"""

    @property
    def image_tags(self):
        age_tag = f"{self.age // 10}0s"
        return super().image_tags + [self.gender, age_tag, self.species]

    @property
    def image_prompt(self):
        if not self.age:
            self.age = random.randint(15, 50)
            self.save()
        prompt = f"""
A full-body color portrait of a fictional {self.gender} {self.species} {self.genre} character aged {self.age or 32} who is a {self.occupation}, looks like {self.lookalike}, and is described as: {self.description}

PRODUCE ONLY A SINGLE REPRESENTATION. DO NOT GENERATE VARIATIONS.
"""
        return prompt

    ################# Instance Methods #################

    def generate(self):
        age = self.age if self.age else random.randint(21, 55)
        gender = (
            self.gender or random.choices(self._genders, weights=[10, 10, 1], k=1)[0]
        )

        prompt = f"Generate a {gender} {self.species} {self.archetype} NPC aged {age} years that is a {self.occupation} who is described as: {self.traits}. Create, or if already present expand on, the NPC's detailed backstory. Also give the NPC a unique, but {random.choice(('mysterious', 'mundane', 'sinister', 'absurd', 'deadly', 'awesome'))} secret to protect."

        result = super().generate(prompt=prompt)

        self.generate_quest()

        return result

    def generate_quest(self, extra_prompt="", associations=None):
        from models.ttrpgobject.quest import Quest

        funcobj = {
            "name": "generate_quest",
            "description": "creates a morally complicated, urgent, multi-part adventure that player characters can explore for or with the described character",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the adventure",
                    },
                    "rewards": {
                        "type": "string",
                        "description": "The specific rewards for solving the adventure depending on the outcome, including financial compensation and any items or information that the player characters will receive",
                    },
                    "description": {
                        "type": "string",
                        "description": "A detailed description of the adventure plot in MARKDOWN, including the major challenges the players will face, the main antagonist, and specific, concrete details about the adventure",
                    },
                    "scenes": {
                        "type": "array",
                        "description": "A detailed description of the adventure in 5 main scenes in MARKDOWN. For each scene include the setup for the scene, npcs, challenges the players will face in the scene, a detailed description of the scene, and its resolution",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "setup",
                                "description",
                                "npcs",
                                "challenges",
                                "information",
                                "task",
                                "resolution",
                            ],
                            "properties": {
                                "setup": {
                                    "type": "string",
                                    "description": "The initial setup for the scene, including what draws players in and any actionable details about the setup",
                                },
                                "description": {
                                    "type": "string",
                                    "description": "An in depth, detailed description of the initial scene and setting, including any actionable details about the scene",
                                },
                                "npcs": {
                                    "type": "array",
                                    "description": "A list of npcs that will be involved in the scene, including their names, descriptions, and any important details about them",
                                    "items": {"type": "string"},
                                },
                                "challenges": {
                                    "type": "array",
                                    "description": "A list of challenges that the players will face in the scene, including any gameplay mechanics associated with each challenge",
                                    "items": {"type": "string"},
                                },
                                "information": {
                                    "type": "array",
                                    "description": "A list of relevant and actionable information or secrets that could be revealed to the players in the scene",
                                    "items": {"type": "string"},
                                },
                                "task": {
                                    "type": "string",
                                    "description": "The next specific and concrete task given to or discovered by the players in the scene, including any important details or game mechanics associated with the task",
                                },
                                "resolution": {
                                    "type": "string",
                                    "description": "The resolution of the scene, including any important details about how the players can progress to the next scene or how they can fail",
                                },
                            },
                        },
                    },
                    "summary": {
                        "type": "string",
                        "description": "A one sentence summary of the adventure, including a specific and concrete reward for solving the mystery",
                    },
                    "locations": {
                        "type": "array",
                        "description": "A list of the locations involved in the adventure, including any important details about each location and its inhabitants",
                        "items": {"type": "string"},
                    },
                    "antagonist": {
                        "type": "string",
                        "description": "Who is the main antagonist? What do they want, why? What is their evil plan? Name, appearance, personality, occupation, and motivations. ",
                    },
                    "hook": {
                        "type": "string",
                        "description": "How do the players encounter the problem? How to make them care? Develop a complete scene that draws the heroes into action, and gives them the initial set of tasks to accomplish.",
                    },
                    "dramatic_crisis": {
                        "type": "string",
                        "description": "What is the dramatic question? What are the stakes? How does it affect the player characters?",
                    },
                    "climax": {
                        "type": "string",
                        "description": "Describe the climax of the adventure? How does it resolve the main conflict?",
                    },
                    "plot_twists": {
                        "type": "array",
                        "description": "A list of potential plot twists that may occur during the adventure, in the order they should be revealed. An unexpected complication, twist, or reveal that changes the direction of the story, raises stakes and threat level, or redefines the goal.",
                        "items": {"type": "string"},
                    },
                },
            },
        }

        prompt = f"""Generate a multipart adventure for a {self.genre} Table Top RPG. The adventure should be revealed through a series of clues and interactions with npcs, and should tell a complete story that is morally complicated, impactful, and challenging for the player characters to complete. The adventure should involve a mix of encounter types, such as Combat, Social, Exploration, Mystery, and Stealth. The adventure should have specific details and should be initiated by or with the character named {self.name} who is a {self.occupation} described as: {self.backstory}.

        The initiating npc has the following goals and secrets: {self.goal}.
"""

        parent = self.parent
        if parent:
            prompt += f"""
The adventure should start in {parent.name} and should include details about the location and its inhabitants: {parent.backstory}.
"""
            while parent.parent:
                parent = parent.parent
                prompt += f"""Located in:
    {parent.name}: {parent.backstory}.
"""
        if extra_prompt:
            prompt += (
                f"Use the following prompt to design the adventure:\n\n{extra_prompt}"
            )

        if associations:
            prompt += f"""
The adventure should also involve the following elements:
- {"\n- ".join([f"{a.name}: {a.backstory}" for a in associations])}.
"""
        else:
            associations = []

        primer = "You are an expert AI Table Top RPG Mystery Generator. You will be provided with a character and a description of the character's traits. Generate an adventure that is connected to the character's backstory, morally complicated, and challenging for the player characters to complete."
        log(prompt, _print=True)
        results = self.system.generate_json(prompt, primer, funcobj)
        # log(results, _print=True)
        self.add_quest(associations, **results)

    def add_quest(
        self,
        associations,
        name,
        description,
        summary,
        rewards,
        locations,
        antagonist,
        hook,
        dramatic_crisis,
        climax,
        plot_twists,
        scenes,
    ):
        from models.ttrpgobject.quest import Quest

        description = (
            markdown.markdown(description.replace("```markdown", "").replace("```", ""))
            .replace("h1>", "h3>")
            .replace("h2>", "h3>")
        )
        antagonist = (
            markdown.markdown(antagonist.replace("```markdown", "").replace("```", ""))
            .replace("h1>", "h3>")
            .replace("h2>", "h3>")
        )

        q = Quest(
            name=name,
            rewards=rewards,
            description=description,
            summary=summary,
            contact=self,
            locations=locations,
            antagonist=antagonist,
            hook=hook,
            dramatic_crisis=dramatic_crisis,
            climax=climax,
            plot_twists=plot_twists,
            scenes=scenes,
        )
        q.save()
        self.quests += [q]
        self.save()

    def remove_quest(self, quest):
        self.quests = [q for q in self.quests if q != quest]
        self.save()
        quest.delete()

    ############################# Object Data #############################
    ## MARK: Object Data
    def page_data(self):
        return {
            "pk": str(self.pk),
            "image_pk": str(self.image.pk) if self.image else None,
            "name": self.name,
            "desc": self.desc,
            "backstory": self.backstory,
            "history": self.history,
            "gender": self.gender,
            "age": self.age,
            "occupation": self.occupation,
            "species": self.species,
            "hitpoints": self.hitpoints,
            "attributes": {
                "strength": self.strength,
                "dexerity": self.dexterity,
                "constitution": self.constitution,
                "wisdom": self.wisdom,
                "intelligence": self.intelligence,
                "charisma": self.charisma,
            },
            "abilities": [str(a) for a in self.abilities],
            "wealth": [w for w in self.wealth],
            "items": [{"name": r.name, "pk": str(r.pk)} for r in self.items],
        }

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_is_player()
        document.pre_save_description()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ############### Verification Methods ##############
    def pre_save_is_player(self):
        # log(self.is_player)
        if self.is_player == "False":
            self.is_player = False
        else:
            self.is_player = bool(self.is_player)
        # log(self.is_player)

    def pre_save_description(self):
        if not self.backstory:
            for t in self._template:
                self.backstory += f"""
<p>{random.choice(t)}</p>
"""
