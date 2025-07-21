import io

from bs4 import BeautifulSoup
from dmtoolkit import dmtools

from autonomous import log
from autonomous.ai.audioagent import AudioAgent
from autonomous.model.autoattr import (
    DictAttr,
    FileAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.gm.playerresponse import PlayerAction, PlayerResponse


class GameMaster(AutoModel):
    party = ReferenceAttr(choices=["Faction"])
    party_responses = ListAttr(ReferenceAttr(choices=["PlayerResponse"]))
    history = StringAttr(default="")
    current_party_objective = StringAttr(default="")
    last_roll = StringAttr(default="")
    last_roll_result = StringAttr(default="")
    audio_ = FileAttr()
    audio_transcription = StringAttr(default="")
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))

    ################### Properties #####################
    @property
    def world(self):
        return self.party.world if self.party else None

    ################### Crud Methods #####################
    @property
    def audio(self):
        if self.audio_:
            self.audio_.seek(0)
            return self.audio_.read()
        else:
            log("No audio file found.", _print=True)
            return None

    @audio.setter
    def audio(self, value):
        if isinstance(value, bytes):
            log("Setting audio file:", type(value), _print=True)
            if self.audio_:
                self.audio_.delete()
            self.audio_.put(value, content_type="audio/mpeg")
            self.save()
        else:
            raise ValueError("Audio must be bytes.")

    def delete(self):
        if self.audio_:
            self.audio_.delete()
        if self.party_responses:
            for response in self.party_responses:
                response.delete()
        return super().delete()

    ################### General Methods #####################

    def transcribe(self):
        if not self.audio:
            log("No audio file to transcribe.", _print=True)
            return
        agent = AudioAgent()
        try:
            audio = io.BytesIO(self.audio)
            audio.name = "audio_file.webm"  # Set a name for the BytesIO object
            self.audio_transcription = agent.generate_text(audio)
            log("Audio transcription completed successfully.", _print=True)
        except Exception as e:
            log(f"Error during audio transcription: {e}", _print=True)
            self.audio_transcription = "Transcription failed."
        finally:
            self.save()

    def add_association(self, obj):
        if obj not in self.associations:
            self.associations += [obj]
            self.save()

    def remove_association(self, obj):
        if obj in self.associations:
            self.associations.remove(obj)
            self.save()

    def get_response(self, player):
        if not self.party_responses:
            log("No party responses available.", _print=True)
            return None
        for response in self.party_responses:
            if response.player == player:
                return response
        log(f"No response found for player: {player.name}", _print=True)
        return None

    def roll_dice(self, dice_expression):
        if not dice_expression:
            log("No dice expression provided.", _print=True)
            return None
        try:
            result = dmtools.dice_roll(dice_expression)
            self.last_roll = dice_expression
            self.last_roll_result = str(result)
            return result
        except Exception as e:
            log(f"Error rolling dice: {e}", _print=True)
            return None

    def generate_scene(self):
        if not self.audio_transcription:
            log("No audio transcription available for scene generation.", _print=True)
            return

        funcobj = {
            "name": "generate_responses",
            "description": "Creates responses and intended actions for each player character in a TTRPG adventuring party based on the GM's descriptions and prompts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_party_objective": {  # NEW: To guide coordinated actions
                        "type": "string",
                        "description": "The primary objective or goal the party is currently pursuing, if any. This helps align individual actions.",
                    },
                    "responses": {
                        "type": "array",
                        "description": "A list of responses and intended actions for each player character based on the GM's descriptions and prompts.",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "name",
                                "response",
                                "action",
                                "observed_details",
                                "reaction_to_party",
                            ],
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "The PC's full name.",
                                },
                                "response": {
                                    "type": "string",
                                    "description": "The player's in-character response to the Game Master's prompt, including any relevant details about their character's thoughts, feelings, and motivations.",
                                },
                                "observed_details": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Key details or observations the character specifically notices from the GM's description or the environment.",
                                },
                                "reaction_to_party": {
                                    "type": "string",
                                    "description": "An optional in-character reaction or direct address to another party member's statement or action.",
                                },
                                "action": {
                                    "type": "object",
                                    "description": "The intended action the player character will take.",
                                    "additionalProperties": False,
                                    "required": [
                                        "description",
                                        "target",
                                        "method",
                                        "focus_on_coordination",
                                    ],
                                    "properties": {
                                        "description": {
                                            "type": "string",
                                            "description": "A general description of the action the character intends to take.",
                                        },
                                        "target": {
                                            "type": "string",
                                            "description": "The specific target of the action (e.g., 'goblin', 'door', 'self', 'party member X').",
                                        },
                                        "method": {
                                            "type": "string",
                                            "description": "The method or skill used for the action (e.g., 'attack with sword', 'cast detect magic', 'attempt to persuade').",
                                        },
                                        "focus_on_coordination": {  # NEW: Explicit coordination flag
                                            "type": "boolean",
                                            "description": "Set to true if this action is explicitly designed to coordinate with another party member's action or a shared strategy.",
                                            "default": False,
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        }

        prompt = f"""You are to play the role of each character in an adventuring party for a {self.world.genre} TTRPG. You will be given the player's information and relevant world details. Generate an in character response and intended action, in JSON, for each player based on the Game Master's prompt.

WORLD DETAILS:

{BeautifulSoup(self.world.backstory, "html.parser").get_text()}

additional world details:

- {"\n\n- ".join([f"{a.name} [{a.title}]: {BeautifulSoup(a.backstory, 'html.parser').get_text()}" for a in self.associations])}

PARTY'S INFORMATION:

- {"\n\n- ".join([f"{p.name} [{p.age} years old/{p.gender}]: {BeautifulSoup(p.backstory, 'html.parser').get_text()}\n  - GOAL: {BeautifulSoup(p.goal, 'html.parser').get_text()}" for p in self.party.players])}

{f"CURRENT SUMMARY of EVENTS:\n{self.history}" if self.history else ""}

CURRENT OBJECTIVE:
{self.current_party_objective if self.current_party_objective else "No current objective set."}

GM PROMPT:

{self.audio_transcription}
"""

        log("Scene generation prompt:", prompt, _print=True)
        responses = self.world.system.generate_json(
            prompt,
            "As an expert AI TTRPG player character simulator, you will create responses to the GM's descriptions in character for each member of the party.",
            funcobj=funcobj,
        )
        if not self.history:
            self.history = self.audio_transcription
        else:
            self.history += "\n\n" + self.audio_transcription
        if len(self.history) > 1000:
            self.history = self.world.system.generate_summary(
                self.history,
                "Summarize the Game Master's audio transcription history for the TTRPG session as an exciting narrative.",
            )
        self.last_roll = ""
        self.last_roll_result = ""
        self.current_party_objective = responses.get("current_party_objective", "")
        if self.party_responses:
            log(
                "Clearing previous party responses before generating new ones.",
                _print=True,
            )
            for response in self.party_responses:
                response.delete()
            self.party_responses = []
            self.save()
        log("Scene generation responses:", responses, _print=True)
        for response in responses["responses"]:
            if not isinstance(response, dict):
                log(f"Invalid response format: {response}", _print=True)
                continue

            name = response.get("name")
            if not name:
                log("Response missing 'name' field.", _print=True)
                continue

            player = next(
                (p for p in self.party.players if p.name.lower() == name.lower()), None
            )
            if not player:
                log(f"No player found with name: {name}", _print=True)
                continue

            player_response = PlayerResponse(
                player=player,
                response=response.get("response", ""),
                observed_details=response.get("observed_details", []),
                reaction_to_party=response.get("reaction_to_party", ""),
            )

            if action_data := response.get("action", {}):
                player_response.add_action(
                    description=action_data.get("description", ""),
                    target=action_data.get("target", ""),
                    method=action_data.get("method", ""),
                    focus_on_coordination=action_data.get(
                        "focus_on_coordination", False
                    ),
                )
            log(
                f"""\nAdding response for {name}: {player_response.response}
    Observed Details: {player_response.observed_details}
    Response to Party: {player_response.reaction_to_party}
    Action: {player_response.action.description if player_response.action else "None"}
    Target: {player_response.action.target if player_response.action else "None"}
    Method: {player_response.action.method if player_response.action else "None"}
    Focus on Coordination: {player_response.action.focus_on_coordination if player_response.action else "None"}
""",
                _print=True,
            )
            self.party_responses += [player_response]
        self.save()
