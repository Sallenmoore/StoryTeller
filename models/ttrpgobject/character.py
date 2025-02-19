import random

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
    _traits_list = [
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
    ]
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
        age = self.age if self.age else random.randint(15, 45)
        gender = (
            self.gender or random.choices(self._genders, weights=[10, 10, 1], k=1)[0]
        )

        prompt = f"Generate a {gender} {self.species} {self.archetype} NPC aged {age} years that is a {self.occupation} who is described as: {self.traits}. Create, or if already present expand on, the NPC's detailed backstory. Also give the NPC a unique, but {random.choice(('mysterious', 'mundane', 'sinister', 'absurd', 'deadly', 'awesome'))} secret to protect."

        return super().generate(prompt=prompt)

    def generate_quest(self):
        from models.ttrpgobject.quest import Quest

        funcobj = {
            "name": "generate_quest",
            "description": "creates a morally complicated, interesting, and multi-part mystery that player characters can discover for or with the described character",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the mystery",
                    },
                    "rewards": {
                        "type": "string",
                        "description": "The specific rewards for solving the mystery depending on the outcome, including financial compensation",
                    },
                    "description": {
                        "type": "string",
                        "description": "A detailed description of the mystery, what is required to solve it, including any ethical complications involved in solving the mystery",
                    },
                    "summary": {
                        "type": "string",
                        "description": "A one sentence summary of the mystery, including rewards",
                    },
                    "location": {
                        "type": "string",
                        "description": "A detailed description of the primary starting location of the mystery",
                    },
                },
            },
        }

        prompt = f"Generate a multipart mystery for a {self.genre} Table Top RPG. The mysteries should be revealed as each part is discovered, and should tell a complete story that is morally complicated, interesting, and challenging for the player characters to complete. Include specific ethical complications involved in various possible outcomes of completing the mystery. The mystery should be suitable for a party of 4-6 players. The mystery should be more than just item retrieval, involving aspects of political intrigue, illegal smuggling, or safe escort. The mystery should have specific details and should be initiated by or with the character named {self.name} who is a {self.occupation} described as: {self.description}."

        primer = "You are an expert AI Table Top RPG Mystery Generator. You will be provided with a character and a description of the character's traits. Generate a mystery that is connected to the character's backstory, morally complicated, and challenging for the player characters to complete. The mystery should be suitable for a party of 4-6 players. Include specific ethical complications involved in solving the mystery using various methods with different outcomes."
        results = self.system.generate_json(prompt, primer, funcobj)
        self.add_quest(**results)

    def add_quest(self, name, description, summary, rewards, location):
        from models.ttrpgobject.quest import Quest

        q = Quest(
            name=name,
            rewards=rewards,
            description=description,
            summary=summary,
            contact=self,
            location=location,
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
