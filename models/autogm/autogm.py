import json

import markdown
from bs4 import BeautifulSoup

from autonomous import log
from autonomous.ai.jsonagent import JSONAgent
from autonomous.model.autoattr import (
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.autogm.autogmquest import AutoGMQuest
from models.autogm.autogmscene import AutoGMScene


class AutoGM(AutoModel):
    world = ReferenceAttr(choices=["World"], required=True)
    agent = ReferenceAttr(choices=[JSONAgent])
    voice = StringAttr(default="echo")

    _funcobj = {
        "name": "run_scene",
        "description": "Creates a TTRPG scene that advances the story, maintains narrative consistency, and integrates elements from the uploaded world file.",
        "parameters": {
            "type": "object",
            "properties": {
                "scene_type": {
                    "type": "string",
                    "enum": ["social", "combat", "exploration", "stealth"],
                    "description": "Type of scene to generate (e.g., social, combat, exploration, or stealth).",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed Markdown description of the scene, driving the story forward and providing relevant information.",
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
                    "required": ["roll_required", "type", "attribute", "description"],
                    "properties": {
                        "roll_required": {
                            "type": "boolean",
                            "description": "Whether a roll is required for the player's next action.",
                        },
                        "type": {
                            "type": "string",
                            "enum": [
                                "savingthrow",
                                "attack",
                                "damage",
                                "skillcheck",
                                "abilitycheck",
                                "initiative",
                                "none",
                            ],
                            "description": "Type of roll needed.",
                        },
                        "attribute": {
                            "type": "string",
                            "description": "Attribute to roll against (e.g., WIS, DEX, Stealth).",
                        },
                        "description": {
                            "type": "string",
                            "description": "Markdown description of the event requiring a roll.",
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

    ##################### PROPERTY METHODS ####################

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
        region_str = party.system._titles["region"].lower()
        city_str = party.system._titles["city"].lower()
        district_str = party.system._titles["district"].lower()
        location_str = party.system._titles["location"].lower()
        self._funcobj["parameters"]["properties"]["places"]["items"]["properties"][
            "location_type"
        ] |= {
            "enum": [
                region_str,
                city_str,
                district_str,
                location_str,
            ],
            "description": f"The kind of location, such as a {region_str}, {city_str}, {district_str}, or specific {location_str} or landmark.",
        }
        # log(self._funcobj, _print=True)

    def update_refs(self):
        self.gm.get_client().clear_files()
        world_data = self.world.page_data()
        ref_db = json.dumps(world_data).encode("utf-8")
        self.gm.get_client().attach_file(
            ref_db, filename=f"{self.world.slug}-gm-dbdata.json"
        )
        self.save()

    def parse_scene(self, party, response):
        from models.world import World

        if scene_type := response["scene_type"]:
            summary = response["description"]
            if party.autogm_summary:
                prompt = (
                    party.autogm_summary[10].summary
                    if len(party.autogm_summary) > 10
                    else ""
                )
                prompt += ". ".join(
                    ags.description for ags in party.autogm_summary[:10]
                )
                primer = "Generate a summary of less than 250 words of the following events in MARKDOWN format."
                summary = party.world.system.generate_summary(prompt, primer)
            summary = summary.replace("```markdown", "").replace("```", "")
            summary = markdown.markdown(summary)
            description = (
                response["description"].replace("```markdown", "").replace("```", "")
            )
            description = markdown.markdown(description)

            associations = []
            if party.last_scene:
                for ass in [*party.players, *party.last_scene.associations]:
                    if ass not in associations:
                        associations += [ass]

            scene = AutoGMScene(
                type=scene_type,
                party=party,
                description=description,
                date=party.current_date,
                summary=summary,
                associations=associations,
            )
            scene.save()

            if party.last_scene:
                scene.current_quest = party.last_scene.current_quest
                scene.quest_log = party.last_scene.quest_log
                scene.save()

            for q in response.get("quest_log", []):
                try:
                    quest = [
                        quest
                        for quest in party.last_scene.quest_log
                        if quest.name == q["name"]
                    ].pop(0)
                    quest.description = q["description"]
                    quest.importance = q.get("importance")
                    quest.status = q["status"]
                    quest.next_steps = q["next_steps"]
                except IndexError:
                    quest = AutoGMQuest(
                        name=q["name"],
                        type=q["type"],
                        description=q["description"],
                        status=q["status"],
                        next_steps=q["next_steps"],
                        importance=q.get("importance"),
                    )
                    scene.quest_log += [quest]
                else:
                    quest.status = q["status"]
                    quest.next_steps = q["next_steps"]
                quest.save()
            scene.save()

            # handle rolls
            if response.get("requires_roll") and response["requires_roll"].get(
                "roll_required"
            ):
                scene.roll_required = True
                scene.roll_type = response["requires_roll"].get("type")
                scene.roll_attribute = response["requires_roll"].get("attribute")
                scene.roll_description = response["requires_roll"].get("description")
            else:
                scene.roll_required = False
            scene.generate_image(response["image"])
            scene.generate_audio(voice="onyx")
            party.autogm_summary += [scene]
            party.save()
            scene.generate_npcs(response.get("npcs"))
            scene.generate_combatants(response.get("combatants"))
            scene.generate_loot(response.get("loot"))
            scene.generate_places(response.get("places"))
            for ags in party.autogm_summary:
                for assoc in [
                    *ags.npcs,
                    *ags.loot,
                    *ags.combatants,
                    *ags.places,
                    *ags.associations,
                ]:
                    assoc.add_associations(ags.associations)
            self.update_refs()
            return scene

    def start(self, party, scenario=None):
        if party.autogm_summary:
            self.end(party)
        scenario = (
            scenario
            or "Build on an existing storyline or encounter from the world to surprise and challenge players' expectations."
        )
        prompt = f"You are an expert AI Game Master for a new {self.world.genre} TableTop RPG campaign within the established world of {self.world.name}, described in the uploaded file. Your job is to start the first session by describing the world, campaign setting, and a plot hook for the players in a vivid and captivating way. The first session should also explain what brought these characters together and what their initial goal is. The party consists of the following characters:"
        for pc in party.players:
            prompt += f"""
PARTY MEMBER: {pc.name} [{pc.pk}]
{pc.backstory_summary}
"""
        prompt += f"""

SCENARIO: {scenario}

IN-GAME DATE: {party.current_date}
"""
        self._update_response_function(party)
        response = self.gm.generate(prompt, self._funcobj)
        scene = self.parse_scene(party, response)
        scene.save()
        return scene

    def run(self, party, message):
        prompt = f"""You are an expert AI Game Master for a {self.world.genre} tabletop roleplaying game. Your task is to craft an evocative and immersive description for the next event, scene, or combat round that moves the story forward in surprising yet logical ways. The scene should:
- Build suspense, tension, or excitement.
- Incorporate elements from the player's most recent message, past events, and established lore.
- Reflect the player's self-described actions and intentions.
- Be influenced by any provided roll results or narrative outcomes.
- Remain consistent with the tone and pacing of the game.

Provide your response in a way that:
1. Evokes vivid imagery and atmosphere.
2. Introduces unexpected challenges or opportunities to keep the players engaged.
3. Clearly outlines the consequences or setup for player actions, leaving room for creative responses.

PREVIOUS EVENTS SUMMARY
{party.last_scene.summary or party.last_scene.description}

STORY ELEMENTS
{"\n- ".join([f"name: {ass.name}\n  - type: {ass.title}\n  - backstory: {ass.backstory_summary}" for ass in party.last_scene.associations if ass not in party.players]) if party.autogm_summary else "None yet"}

PARTY
{"".join([f"\n- {pc.name} : {pc.backstory_summary}\n" for pc in party.players])}

PLAYER'S ACTIONS
{message}
"""
        # log(prompt, _print=True)
        self._update_response_function(party)
        response = self.gm.generate(prompt, function=self._funcobj)
        scene = self.parse_scene(party, response)
        scene.save()
        return scene

    def regenerate(self, party, message):
        if party.autogm_summary:
            redo = party.autogm_summary.pop(-1)
            redo.delete()
        return (
            self.run(party, message)
            if party.autogm_summary
            else self.start(party, message)
        )

    def rungm(self, party):
        if not party.next_scene:
            raise ValueError("No next scene to run.")

        res_function = {
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

        prompt = f"""You are the AI roleplayer for a TTRPG campaign. Your task is to generate a structured JSON response where each party member reacts to the GM's described scene.

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

CAMPAIGN SUMMARY
{(party.last_scene and party.last_scene.summary) or "The campaign has just begun."}

PLACES
- {"\n- ".join([f"name: {ass.name}\n  - backstory: {ass.backstory_summary}" for ass in party.next_scene.places]) if party.next_scene.places else "None"}

NPCS
- {"\n- ".join([f"name: {ass.name}\n  - backstory: {ass.backstory_summary}" for ass in party.next_scene.npcs]) if party.next_scene.npcs else "None"}

ENEMIES
- {"\n- ".join([f"name: {ass.name}\n  - backstory: {ass.backstory_summary}" for ass in party.next_scene.combatants]) if party.next_scene.combatants else "None"}

ITEMS
- {"\n- ".join([f"name: {ass.name}\n  - backstory: {ass.backstory_summary}" for ass in party.next_scene.loot]) if party.next_scene.loot else "None"}

PARTY PLAYER CHARACTERS:
"""

        for pc in party.players:
            backstory_summary = BeautifulSoup(
                pc.backstory_summary, "html.parser"
            ).get_text()
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
  - Goal: {pc.goal}
  - Backstory: {backstory_summary}
  - Abilities:
    - {"\n    - ".join(abilities)}
"""
        description = BeautifulSoup(
            party.next_scene.description, "html.parser"
        ).get_text()
        prompt += f"""

SCENE DESCRIPTION
{description}

"""

        if party.next_scene.roll_required:
            # log(roll_result, _print=True)
            res_function["parameters"]["required"] += ["requires_roll"]
            res_function["parameters"]["properties"]["requires_roll"] = {
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
            log(json.dumps(res_function, indent=4), _print=True)

            prompt += f"""
ROLL REQUIRED
{party.next_scene.roll_player.name} must roll a {party.next_scene.roll_attribute} {party.next_scene.roll_type}
"""
        log(prompt, _print=True)

        response = self.gm.generate(
            prompt,
            res_function,
        )
        party.next_scene.set_player_messages(response["responses"])
        if party.next_scene.roll_required:
            party.next_scene.roll_result = response["requires_roll"]["roll_result"]
            party.next_scene.roll_description = response["requires_roll"][
                "roll_description"
            ]
            party.next_scene.roll_formula = response["requires_roll"]["roll_formula"]
        party.next_scene.generate_image()
        party.next_scene.generate_player_audio()
        next_scene = party.get_next_scene(create=True)

        # sanity test
        if next_scene != party.next_scene:
            raise ValueError("Scene not saved")
        return next_scene

    def end(self, party):
        for p in [party, party.world, *party.players]:
            p.backstory += f"""
<h5>{party.first_scene.date}{f"- {party.last_scene.date}" if len(party.autogm_summary) > 1 else ""}</h5>
{party.last_scene.summary}
"""
            p.save()
        party.autogm_history += party.autogm_summary
        party.autogm_summary = []
        party.save()
        self.update_refs()
        return party
