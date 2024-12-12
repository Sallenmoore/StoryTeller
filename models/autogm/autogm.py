import json

import markdown
from bs4 import BeautifulSoup
from dmtoolkit import dmtools

from autonomous import log
from autonomous.ai.jsonagent import JSONAgent
from autonomous.model.autoattr import (
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.autogm.autogmquest import AutoGMQuest


class AutoGM(AutoModel):
    world = ReferenceAttr(choices=["World"], required=True)
    agent = ReferenceAttr(choices=[JSONAgent])
    voice = StringAttr(default="echo")

    _gm_funcobj = {
        "name": "run_scene",
        "description": "Generates a structured JSON response for each party member's reaction to the GM's described scene.",
        "parameters": {
            "type": "object",
            "properties": {
                "responses": {
                    "type": "array",
                    "description": "List of responses from all party members.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "character_pk",
                            "response",
                            "intent",
                            "emotion",
                        ],
                        "properties": {
                            "character_pk": {
                                "type": "string",
                                "description": "The primary key (pk) of the character responding.",
                            },
                            "response": {
                                "type": "string",
                                "description": "A detailed description of the character's reaction or dialogue.",
                            },
                            "intent": {
                                "type": "string",
                                "description": "The primary intent behind the character's response (e.g., 'prepare for combat').",
                            },
                            "emotion": {
                                "type": "string",
                                "description": "Emotion the character is experiencing.",
                            },
                        },
                    },
                },
            },
            "required": ["responses"],
        },
    }
    _pc_funcobj = {
        "name": "run_scene",
        "description": "Creates a TTRPG scene that advances the story, maintains narrative consistency, and integrates elements from the uploaded world file.",
        "parameters": {
            "type": "object",
            "properties": {
                "scene_type": {
                    "type": "string",
                    "enum": [
                        "social",
                        "encounter",
                        "combat",
                        "investigation",
                        "exploration",
                        "stealth",
                        "puzzle",
                    ],
                    "description": "Type of scene to generate (e.g., social, combat, encounter, exploration, investigation, puzzle, or stealth).",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the scene in MARKDOWN, driving the story forward and providing relevant information.",
                },
                "image": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["description", "imgtype"],
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the scene for image generation.",
                        },
                        "imgtype": {
                            "type": "string",
                            "enum": ["scene", "map"],
                            "description": "Specifies whether the image is a scene or a map.",
                        },
                    },
                },
                "player": {
                    "type": "string",
                    "description": "Name of the active player, or blank if not specific to any player.",
                },
                "npcs": {
                    "type": "array",
                    "description": "List of non-combatant NPCs, including details for interaction or lore.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["species", "name", "description", "backstory"],
                        "properties": {
                            "species": {
                                "type": "string",
                                "description": "NPC species (e.g., human, elf).",
                            },
                            "name": {
                                "type": "string",
                                "description": "Unique name for the NPC.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Markdown description of NPC's appearance.",
                            },
                            "backstory": {
                                "type": "string",
                                "description": "Markdown description of the NPC's history and motivations.",
                            },
                        },
                    },
                },
                "combatants": {
                    "type": "array",
                    "description": "List of combatants for combat scenes, or empty for other scene types.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["combatant_type", "name", "description"],
                        "properties": {
                            "combatant_type": {
                                "type": "string",
                                "enum": ["humanoid", "animal", "monster", "unique"],
                                "description": "Combatant type (e.g., humanoid, monster).",
                            },
                            "name": {
                                "type": "string",
                                "description": "Name of the combatant.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Markdown description of the combatant's appearance and behavior.",
                            },
                        },
                    },
                },
                "places": {
                    "type": "array",
                    "description": "List of locations relevant to the scenario, or empty if none.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "location_type",
                            "name",
                            "description",
                            "backstory",
                        ],
                        "properties": {
                            "location_type": {
                                "type": "string",
                                "enum": ["region", "city", "district", "poi"],
                                "description": "Type of location (e.g., city, point of interest).",
                            },
                            "name": {
                                "type": "string",
                                "description": "Unique name for the location.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Markdown description of the location's appearance.",
                            },
                            "backstory": {
                                "type": "string",
                                "description": "Publicly known history of the location in Markdown.",
                            },
                        },
                    },
                },
                "loot": {
                    "type": "array",
                    "description": "List of loot items discovered in the scene, or empty if none.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["rarity", "name", "description", "attributes"],
                        "properties": {
                            "rarity": {
                                "type": "string",
                                "enum": [
                                    "common",
                                    "uncommon",
                                    "rare",
                                    "very rare",
                                    "legendary",
                                    "artifact",
                                ],
                                "description": "Rarity of the loot item.",
                            },
                            "name": {
                                "type": "string",
                                "description": "Unique name for the item.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Markdown description of the item's appearance.",
                            },
                            "attributes": {
                                "type": "array",
                                "description": "Markdown list of item's features, limitations, or value.",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
                "requires_roll": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "roll_player",
                        "roll_required",
                        "type",
                        "attribute",
                        "description",
                    ],
                    "properties": {
                        "roll_required": {
                            "type": "boolean",
                            "description": "Whether a roll is required for the player's next action.",
                        },
                        "roll_player": {
                            "type": "string",
                            "description": "The primary key (pk) of the player who must roll.",
                        },
                        "type": {
                            "type": "string",
                            "enum": [
                                "saving throw",
                                "attack",
                                "damage",
                                "skill check",
                                "ability check",
                                "initiative",
                                "none",
                            ],
                            "description": "Type of roll needed.",
                        },
                        "attribute": {
                            "type": "string",
                            "description": "Attribute or Skill to roll against (e.g., WIS, DEX, Stealth).",
                        },
                        "description": {
                            "type": "string",
                            "description": "Markdown description of the event requiring a roll, including the success value the player must meet or beat.",
                        },
                    },
                },
                "quest_log": {
                    "type": "array",
                    "description": "List of plot points, quests, or objectives for the players.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "name",
                            "type",
                            "description",
                            "importance",
                            "status",
                            "next_steps",
                        ],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Quest or objective name.",
                            },
                            "type": {
                                "type": "string",
                                "enum": [
                                    "main quest",
                                    "side quest",
                                    "optional objective",
                                ],
                                "description": "Type of quest or objective.",
                            },
                            "description": {
                                "type": "string",
                                "description": "Markdown description of the quest or objective.",
                            },
                            "importance": {
                                "type": "string",
                                "description": "Connection to the overarching story.",
                            },
                            "status": {
                                "type": "string",
                                "enum": [
                                    "rumored",
                                    "active",
                                    "completed",
                                    "failed",
                                    "abandoned",
                                ],
                                "description": "Current status of the quest.",
                            },
                            "next_steps": {
                                "type": "string",
                                "description": "Markdown description of actions to advance the objective.",
                            },
                        },
                    },
                },
            },
        },
    }

    _combat_funcobj = {
        "name": "run_combat_round",
        "description": "Generates the action, bonus action, and movement for a single actor's turn of combat for a TTRPG using the described context and setting.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "visual, evocative, and concrete description of the full turn in MARKDOWN.",
                },
                "action": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "description",
                        "attack_roll",
                        "damage_roll",
                        "saving_throw",
                        "target",
                        "result",
                    ],
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "A concrete description of the attempted main action, including any abilities used.",
                        },
                        "attack_roll": {
                            "type": "integer",
                            "description": "The result of rolling dice to attack, or 0 if not attacking.",
                        },
                        "damage_roll": {
                            "type": "integer",
                            "description": "The result of rolling dice for damage, if attacking and attack is successful.",
                        },
                        "saving_throw": {
                            "type": "integer",
                            "description": "The result of rolling dice for a saving throw, if required by status or effect.",
                        },
                        "target": {
                            "type": "string",
                            "description": "The Primary Key (pk) of the action's target, or blank for no target.",
                        },
                        "result": {
                            "type": "string",
                            "description": "A description of the result of the action. Ensure the result is consistent with the success or failure of the dice rolls and the target's status.",
                        },
                    },
                },
                "bonus_action": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "description",
                        "attack_roll",
                        "damage_roll",
                        "saving_throw",
                        "target",
                        "result",
                    ],
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "A concrete description of the attempted bonus action, including any abilities used.",
                        },
                        "attack_roll": {
                            "type": "integer",
                            "description": "The result of rolling dice to attack, or 0 if not attacking.",
                        },
                        "damage_roll": {
                            "type": "integer",
                            "description": "The result of rolling dice for damage, if attacking and attack is successful.",
                        },
                        "saving_throw": {
                            "type": "integer",
                            "description": "The result of rolling dice for a saving throw, if required by status or effect.",
                        },
                        "target": {
                            "type": "string",
                            "description": "The Primary Key (pk) of the action's target, or blank for no target.",
                        },
                        "result": {
                            "type": "string",
                            "description": "A description of the result of the action. Ensure the result is consistent with the success or failure of the dice rolls and the target's status.",
                        },
                    },
                },
                "movement": {
                    "type": "string",
                    "description": "A description movement of the actor in the scene, including the distance in feet from the starting position, the direction, and the actors the character/creature is near.",
                },
            },
        },
    }

    ##################### PROPERTY METHODS ####################

    def _prompt(self, party):
        prompt = f"""
CAMPAIGN TONE
{party.next_scene.tone}

CAMPAIGN SUMMARY
{(party.last_scene and party.last_scene.summary) or "The campaign has just begun."}

"""

        if party.next_scene.quest_log:
            prompt += f"""
PLOT LINES AND QUESTS
- {"\n- ".join([f"name: {ass.name}{"\n  - Party's Primary Focus" if ass == party.next_scene.current_quest else ""}\n  - type: {ass.type}\n  - description: {ass.description} \n  - status: {ass.status}\n  - importance: {ass.importance}" for ass in party.next_scene.quest_log]) if party.next_scene.quest_log else "None"}
"""

        if party.next_scene.places:
            prompt += f"""
PLACES
- {"\n- ".join([f"name: {ass.name}\n  - backstory: {ass.backstory_summary}" for ass in party.next_scene.places]) if party.next_scene.places else "None"}

"""

        if party.next_scene.factions:
            prompt += f"""
FACTIONS
- {"\n- ".join([f"name: {ass.name}\n  - backstory: {ass.backstory_summary}" for ass in party.next_scene.factions if ass != party]) if party.next_scene.factions else "None"}

"""

        if party.next_scene.npcs:
            prompt += f"""
NPCS
- {"\n- ".join([f"name: {ass.name}\n  - backstory: {ass.backstory_summary}" for ass in party.next_scene.npcs]) if party.next_scene.npcs else "None"}

"""

        if party.next_scene.combatants:
            prompt += f"""
ENEMIES
- {"\n- ".join([f"name: {ass.name}\n  - backstory: {ass.backstory_summary}" for ass in party.next_scene.combatants]) if party.next_scene.combatants else "None"}

"""

        if party.next_scene.loot:
            prompt += f"""
ITEMS
- {"\n- ".join([f"name: {ass.name}\n  - backstory: {ass.backstory_summary}" for ass in party.next_scene.loot]) if party.next_scene.loot else "None"}

"""

        if assoc := party.next_scene.get_additional_associations():
            prompt += f"""
ADDITIONAL ASSOCIATIONS
- {"\n- ".join([f"{ass.name} [{ass.title}]\n  - pk: {ass.pk}" for ass in assoc])}

"""

        prompt += f"""
PARTY DESCRIPTION
{party.backstory_summary}

PARTY PLAYER CHARACTERS
"""
        for pc in party.players:
            abilities = [
                BeautifulSoup(a, "html.parser").get_text() for a in pc.abilities
            ]
            prompt += f"""
- Name: {pc.name}
- pk: {pc.pk}
- Species: {pc.species}
- Gender: {pc.gender}
- Age: {pc.age}
- Occupation: {pc.occupation}
- Goal: {pc.goal.strip()}
- Backstory: {BeautifulSoup(pc.backstory_summary, "html.parser").get_text()}
- Abilities:
    - {"\n    - ".join(abilities)}

"""
        return prompt

    def get_gm_prompt(self, party, start=False):
        return f"""You are the AI roleplayer for a {self.world.genre} TTRPG campaign. Your task is to generate a structured JSON response where each party member reacts to the GM's described scene.

For each character:
1. Respond in a way that is consistent with their personality, backstory, abilities, and motivations as described in the campaign.
2. Incorporate relevant elements from previous campaign events and the world described in the uploaded file.
3. Address the scene's challenges or opportunities uniquely, reflecting each character's perspective and role in the group.
4. Ensure the responses align with the tone and stakes of the scene while driving the story forward.
5. Acknowledge or react to the responses of other party members where appropriate, enhancing the sense of collaboration or conflict within the group.

Return the responses in the following structured JSON format:
```json
{{
  "responses": [
    {{
      "character_name": "string",
      "response": "string",
      "intent": "string",
      "emotions": ["string"]
    }}
  ]
}}

{self._prompt(party)}
"""

    def get_pc_prompt(self, party, start=False):
        if start:
            prompt = f"""
You are an expert AI Game Master for a {self.world.genre} tabletop roleplaying game. Your task is to craft an evocative and gripping description of the first session by describing the world, campaign setting, and a plot hook for the players in a vivid and captivating way. The first session should also explain what brought these characters together and what their common goal is. The scene should:
- Build suspense, tension, or excitement.
- Incorporate elements from established lore decribed in the uploaded file.

Provide your response in a way that:
1. Evokes vivid imagery and atmosphere.
2. Introduces concrete challenges or opportunities to keep the players engaged.
3. Clearly outlines the consequences or setup for player actions, leaving room for creative responses.

{self._prompt(party)}
"""
        else:
            prompt = f"""
You are an expert AI Game Master for an ongoing {self.world.genre} tabletop roleplaying game. Your primary objective is to craft a concrete, immersive, and interactive description for the next event, scene, or combat round in a game session. The goal is to crafte a scene that has concrete consequences from the previous scene while also driving the story forward in ways that are surprising yet logical and grounded in the game's established lore. Ensure that your response adheres to the following guidelines:

- INTEGRATION: Seamlessly incorporate elements and logical consequences from previous events, the player's most recent message and roll, as well as lore from the uploaded file.
- CONSISTENCY: Maintain alignment with the previous scene's events as well as the game's tone, pacing, and narrative style.
- ATMOSPHERE: Use concrete and sensory-rich imagery to bring the scene to life.
- ENAGEMENT: Introduce unexpected challenges, twists, enemy ambushes, or opportunities that inspire creative thinking and problem-solving.
- CLARITY: Offer clear and concrete next steps or options for player actions, while setting up logical and specific consequences or outcomes.
- FLEXIBILITY: Leave room for player creativity, encouraging responses that shape the unfolding story.
- PLAYER AGENCY: Reflect the player's self-described actions, intentions, emotions, and any dice roll results in the scene.
- CONSEQUENCES: Negative outcomes should have negative consequences, and vice versa. The severity of the consequences should be proportional to the player characters' described actions and dice roll results in the scene, where 1 is the worst possible outcome and >=20 is the best possible outcome.

{self._prompt(party)}
"""
        if description := party.last_scene and party.last_scene.description:
            description = BeautifulSoup(
                description,
                "html.parser",
            ).get_text()

            prompt += f"""
PREVIOUS SCENE
{description}

"""
        return prompt

    @property
    def gm(self):
        if not self.agent:
            self.agent = JSONAgent(
                name=f"TableTop RPG Game Master for {self.world.name}, in a {self.world.genre} setting",
                instructions=f"""You are highly skilled and creative AI trained to act as a Game Master for a {self.world.genre} TableTop RPG. Use the uploaded file to reference the existing world objects, such as characters, creatures, items, locations, encounters, and storylines.

                Use existing world elements and their connections to expand on existing storylines or generate a new story consistent with the existing elements and timeline of the world. While the new story should be unique, there should also be appropriate connections to one or more existing elements in the world as described by the uploaded file.""",
                description=f"You are a helpful AI assistant trained to act as the Table Top Game Master for 1 or more players. You will create consistent, mysterious, and unique homebrewed {self.world.genre} stories that will challenge, surprise, and delight players. You will also ensure that your stories are consistent with the existing world as described by the uploaded file.",
            )
            self.agent.save()
            self.update_refs()
            self.save()
        return self.agent

    def _update_response_function(self, party):
        if party.next_scene.roll_required and party.next_scene.gm_mode == "pc":
            self._gm_funcobj["parameters"]["required"] += ["requires_roll"]
            self._gm_funcobj["parameters"]["properties"]["requires_roll"] = {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "roll_formula",
                    "roll_result",
                    "roll_description",
                ],
                "properties": {
                    "roll_formula": {
                        "type": "string",
                        "description": "The roll formula used to generate the result, such as 1d20+4, 2d6 Advantage, or 3d10-1 Disadvantage.",
                    },
                    "roll_result": {
                        "type": "integer",
                        "description": "The result of your simulated dice roll",
                    },
                    "roll_description": {
                        "type": "string",
                        "description": "Description of the player's actions accompanying the roll.",
                    },
                },
            }
        elif party.next_scene.gm_mode == "pc":
            region_str = party.system._titles["region"].lower()
            city_str = party.system._titles["city"].lower()
            district_str = party.system._titles["district"].lower()
            location_str = party.system._titles["location"].lower()
            self._pc_funcobj["parameters"]["properties"]["places"]["items"][
                "properties"
            ]["location_type"] |= {
                "enum": [
                    region_str,
                    city_str,
                    district_str,
                    location_str,
                ],
                "description": f"The kind of location, such as a {region_str}, {city_str}, {district_str}, or specific {location_str} or landmark.",
            }

    def update_refs(self):
        self.gm.get_client().clear_files()
        world_data = self.world.page_data()
        ref_db = json.dumps(world_data).encode("utf-8")
        self.gm.get_client().attach_file(
            ref_db, filename=f"{self.world.slug}-gm-dbdata.json"
        )
        self.save()

    def runpc(self, party):
        if not party.next_scene:
            raise ValueError("No next scene to run.")

        if party.last_scene:
            prompt = self.get_pc_prompt(party)
        else:
            prompt = self.get_pc_prompt(party, start=True)

        prompt += """
PLAYER ACTIONS
"""
        for msg in party.next_scene.player_messages:
            if msg.message:
                prompt += f"""
- {msg.player.name}'s [with a {msg.emotion or "neutral"} demeanor]: {BeautifulSoup(msg.message, "html.parser").get_text()}
  {f"- intentions: {msg.intent}" if msg.intent else ""}
"""

        if party.next_scene and party.next_scene.roll_required:
            prompt += f"""
ROLL RESULT
{party.next_scene.roll_description}

{(party.next_scene.roll_player and party.next_scene.roll_player.name) or ""} rolled a {party.next_scene.roll_attribute} {party.next_scene.roll_type} with a result of {party.next_scene.roll_result}
"""

        self._update_response_function(party)

        log(prompt, _print=True)
        party.next_scene.prompt = prompt
        party.next_scene.save()

        response = self.gm.generate(
            prompt,
            self._pc_funcobj,
        )
        log(json.dumps(response, indent=4), _print=True)
        party.next_scene.prompt += f"\n\nRESPONSE:\n{json.dumps(response, indent=4)}"
        party.next_scene.type = response["scene_type"]

        description = (
            response["description"].replace("```markdown", "").replace("```", "")
        )
        description = markdown.markdown(description)
        party.next_scene.description = description
        party.next_scene.save()

        for q in response.get("quest_log", []):
            if party.last_scene:
                quest = [
                    quest
                    for quest in party.last_scene.quest_log
                    if quest.name == q["name"]
                ]
                if quest := quest.pop(0) if quest else None:
                    quest.description = q["description"]
                    quest.importance = q.get("importance")
                    quest.status = q["status"]
                    quest.next_steps = q["next_steps"]
                else:
                    quest = AutoGMQuest(
                        name=q["name"],
                        type=q["type"],
                        description=q["description"],
                        status=q["status"],
                        next_steps=q["next_steps"],
                        importance=q.get("importance"),
                    )
                    party.next_scene.quest_log += [quest]
                quest.save()

        party.next_scene.save()

        party.next_scene.generate_npcs(response.get("npcs"))
        party.next_scene.generate_combatants(response.get("combatants"))
        party.next_scene.generate_loot(response.get("loot"))
        party.next_scene.generate_places(response.get("places"))
        party.next_scene.generate_audio(voice="onyx")
        party.next_scene.generate_image(response["image"]["description"])

        if party.next_scene.combatants and party.next_scene.type == "combat":
            party.next_scene.start_combat()

        next_scene = party.get_next_scene(create=True)
        # sanity test
        if response.get("requires_roll") and response["requires_roll"].get(
            "roll_required"
        ):
            next_scene.roll_required = True
            next_scene.roll_type = response["requires_roll"].get("type")
            next_scene.roll_attribute = response["requires_roll"].get("attribute")
            next_scene.roll_description = response["requires_roll"].get("description")
            roll_player = response["requires_roll"].get("roll_player")
            for pc in party.players:
                # log(
                #     f"{pc.pk} == {roll_player} or {pc.name} == {roll_player}",
                #     _print=True,
                # )
                if str(pc.pk) == roll_player or pc.name == roll_player:
                    next_scene.roll_player = pc
                    break
            next_scene.save()
        self.update_refs()
        return next_scene

    def rungm(self, party):
        if not party.next_scene:
            raise ValueError("No next scene to run.")

        if party.last_scene:
            prompt = self.get_gm_prompt(party)
        else:
            prompt = self.get_gm_prompt(party, start=True)

        if party.next_scene.roll_required:
            prompt += f"""
ROLL REQUIRED
{party.next_scene.roll_player.name} must roll a {party.next_scene.roll_attribute} {party.next_scene.roll_type}
"""

        self._update_response_function(party)

        log(prompt, _print=True)
        party.next_scene.prompt = prompt
        party.next_scene.save()

        response = self.gm.generate(
            prompt,
            self._gm_funcobj,
        )
        party.next_scene.set_player_messages(response["responses"])
        party.next_scene.generate_player_audio()
        if party.next_scene.roll_required:
            party.next_scene.roll_result = response["requires_roll"]["roll_result"]
            party.next_scene.roll_description = response["requires_roll"][
                "roll_description"
            ]
            party.next_scene.roll_formula = response["requires_roll"]["roll_formula"]
        next_scene = party.get_next_scene(create=True)
        party.last_scene.generate_image(response["image"]["description"])
        self.update_refs()
        return next_scene

    def run_combat_round(self, party):
        if not party.last_scene:
            raise ValueError("No combat scene to run.")
        if not party.last_scene.combatants:
            raise ValueError("No combatants in the scene.")

        prompt = f"""
SCENE
{BeautifulSoup(party.last_scene.description, "html.parser").get_text()}

"""

        if party.last_scene.places:
            place = party.next_scene.places[0]
            prompt += f"""
LOCATION
- name: {place.name}
- desciption: {place.description_summary}

"""

        if party.last_scene.initiative.allies:
            allies = [
                a
                for a in party.last_scene.initiative.order
                if a.actor in party.allies and a.hp > 0
            ]
            prompt += f"""
ALLIED NPCS
- {"\n- ".join([f"name: {ass.actor.name}\n  - pk: {ass.actor.pk} \n  - HP: {ass.hp} \n  - Description: {ass.actor.description_summary}" for ass in allies ])}

"""

        if party.last_scene.initiative.combatants:
            combatants = [
                a
                for a in party.last_scene.initiative.order
                if a.actor in party.last_scene.combatants and a.hp > 0
            ]
            prompt += f"""
ENEMIES
- {"\n- ".join([f"name: {ass.actor.name}\n  - pk: {ass.actor.pk} \n  - HP: {ass.hp} \n  - Description: {ass.actor.description_summary}" for ass in combatants ])}

"""

        if pcs := [
            a for a in party.last_scene.initiative.order if a.actor in party.players
        ]:
            prompt += f"""
PARTY PLAYER CHARACTERS
- {"\n- ".join([f"name: {ass.actor.name}\n  - pk: {ass.actor.pk} \n  - HP: {ass.hp} \n  - Description: {ass.actor.description_summary}" for ass in pcs ])}

IT IS THE FOLLOWING ACTOR'S TURN IN COMBAT:

- NAME: {party.last_scene.initiative.current_combat_turn().actor.name}
- BACKSTORY: {party.last_scene.initiative.current_combat_turn().actor.backstory_summary}
- GOAL: {party.last_scene.initiative.current_combat_turn().actor.goal}
- ABILITIES: {party.last_scene.initiative.current_combat_turn().actor.abilities}

"""
        log(prompt, _print=True)
        response = self.gm.generate(
            prompt,
            self._combat_funcobj,
        )
        log(json.dumps(response, indent=4), _print=True)
        ondeck = party.last_scene.initiative.current_combat_turn()
        ondeck.description = response["description"]
        ondeck.movement = response["movement"]
        ondeck.add_action(**response["action"])
        ondeck.add_action(**response["bonus_action"], bonus=True)
        ondeck.save()

    ############################ End Campaign #############################
    def end(self, party):
        for p in [party, party.world, *party.players]:
            p.backstory += f"""
<br>
<h5>{party.first_scene.date}{f"- {party.last_scene.date}" if len(party.autogm_summary) > 1 else ""}</h5>
<br>
{party.last_scene.summary}
"""
            p.save()
        party.autogm_history += party.autogm_summary
        party.autogm_summary = []
        party.save()
        return party
