import random

from autonomous import log
from autonomous.model.autoattr import DictAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.base.ttrpgbase import TTRPGBase


class Scene(AutoModel):
    type = StringAttr(
        choices=[
            "social",
            "encounter",
            "combat",
            "investigation",
            "exploration",
            "stealth",
            "puzzle",
        ]
    )
    setup = StringAttr(default="")
    description = StringAttr(default="")
    task = StringAttr(default="")
    challenges = ListAttr(StringAttr(default=""))
    npcs = ListAttr(StringAttr(default=""))
    information = ListAttr(StringAttr(default=""))
    red_herring = StringAttr(default="")
    stakes = StringAttr(default="")
    resolution = StringAttr(default="")
    rewards = StringAttr(default="")
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))


class Quest(AutoModel):
    name = StringAttr(default="")
    description = StringAttr(default="")
    scenes = ListAttr(ReferenceAttr(choices=[Scene]))
    summary = StringAttr(default="")
    rewards = StringAttr(default="")
    contact = ReferenceAttr(choices=["Character"])
    locations = ListAttr(StringAttr(default=""))
    antagonist = StringAttr(default="")
    hook = StringAttr(default="")
    plot_twists = ListAttr(StringAttr(default=""))
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    status = StringAttr(
        default="available", choices=["available", "active", "completed", "failed"]
    )

    funcobj = {
        "name": "generate_quest",
        "description": "creates a morally complicated, urgent, situation that player characters can explore for or with the described character. The situation should not have immediate global consequences, but localized consequences for the NPC associated with it.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the situation, which should be intriguing and suggestive",
                },
                "rewards": {
                    "type": "string",
                    "description": "The reward for completing the situation depending on the outcome, including the specific financial compensation, items, or detailed information that the player characters will receive",
                },
                "description": {
                    "type": "string",
                    "description": "A detailed description of the situation.",
                },
                "scenes": {
                    "type": "array",
                    "description": "A detailed description of scenes the players may encounter when trying to resolve the situation. For each scene include the setup for the scene, npcs, challenges the players will face in the scene, a detailed description of the scene, and its resolution.",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "type",
                            "setup",
                            "description",
                            "npcs",
                            "challenges",
                            "information",
                            "task",
                            "stakes",
                            "red_herring",
                            "resolution",
                            "rewards",
                        ],
                        "properties": {
                            "type": {
                                "type": "string",
                                "description": "The type of scene. Must be one of the following: social, encounter, combat, investigation, exploration, stealth, or puzzle",
                            },
                            "setup": {
                                "type": "string",
                                "description": "The initial setup for the scene, including what draws players in",
                            },
                            "description": {
                                "type": "string",
                                "description": "An in depth, detailed summary of the scene, including any important details about the environment, the characters involved, and any other relevant information",
                            },
                            "task": {
                                "type": "string",
                                "description": "The next specific and concrete task given to or discovered by the players in the scene, including any important details or game mechanics associated with the task",
                            },
                            "npcs": {
                                "type": "array",
                                "description": "A list of npcs that will be involved in the scene, including their names, descriptions, and any important details about them",
                                "items": {"type": "string"},
                            },
                            "challenges": {
                                "type": "array",
                                "description": "A list of challenges that the players will face in the scene, including the gameplay mechanics (skill check, saving throw, etc.) associated with each challenge",
                                "items": {"type": "string"},
                            },
                            "information": {
                                "type": "array",
                                "description": "A list of relevant and actionable information players may gain from the scene",
                                "items": {"type": "string"},
                            },
                            "red_herring": {
                                "type": "string",
                                "description": "A possible, but relevant, red herring that could come up in the scene to throw the players characters off the trail.",
                            },
                            "stakes": {
                                "type": "string",
                                "description": "What's at risk immediately if the players characters don't act? What are the consequences of failure in this scene?",
                            },
                            "resolution": {
                                "type": "string",
                                "description": "The resolution of the scene, including any important details about how the player characters can progress to the next scene or how they can fail",
                            },
                            "rewards": {
                                "type": "string",
                                "description": "Any specific rewards, items, or information that the players will receive for completing the scene. This should be a specific, concrete reward that the players will receive for completing the scene.",
                            },
                        },
                    },
                },
                "summary": {
                    "type": "string",
                    "description": "A one sentence summary of the adventure, worded like a job posting to entice player characters to take on the adventure",
                },
                "locations": {
                    "type": "array",
                    "description": "A list of the locations involved in the adventure, including any important details about each location and its inhabitants",
                    "items": {"type": "string"},
                },
                "antagonist": {
                    "type": "string",
                    "description": "Who or what is the main antagonist? What do they want, why? What is their evil plan? Name, appearance, and motivations. ",
                },
                "hook": {
                    "type": "string",
                    "description": "Describe the complete scene that hooks the player characters into action and gives them the initial task to accomplish.",
                },
                "plot_twists": {
                    "type": "array",
                    "description": "A list of potential plot twists that may occur during the situation, in the order they should be revealed. An unexpected complication, twist, or reveal that changes the direction of the story, raises stakes and threat level, or redefines the goal.",
                    "items": {"type": "string"},
                },
            },
        },
    }

    adventure_types = {
        "Exploration/Discovery Adventure": "Generate a TTRPG adventure focused on the players venturing into uncharted or forgotten territory. The core should involve navigating environmental hazards, encountering the unknown (new species, ancient ruins, unique phenomena), and culminating in a significant discovery. Include elements of wonder, mystery, and potential danger from the unfamiliar, requiring the players to overcome obstacles to reach and understand their find. **Vary the scale of the adventure, from a small-scale personal discovery impacting a few individuals or a local community, to a larger-scale find with regional or factional implications, but avoid making it a galactic or world-altering event.**",
        "Investigation/Mystery Adventure": "Generate a TTRPG adventure centered around players acting as detectives. The plot should revolve around a mysterious event (e.g., disappearance, corporate conspiracy, bizarre crime). The adventure must include gathering clues from various locations and NPCs, deducing the truth from potentially misleading information, and leading to a confrontation or revelation of the underlying conspiracy or culprit. Emphasize intrigue, deduction, and information gathering. **Vary the scale of the investigation, from uncovering a local scandal affecting a few NPCs or a specific organization, to revealing a significant but contained plot impacting a city or star system, avoiding universe-wide implications unless explicitly requested.**",
        "Combat/Conflict Adventure": "Generate a TTRPG adventure with a strong emphasis on direct confrontation and tactical combat. The scenario should involve players overcoming a clear antagonist or objective through military operations, mercenary actions, or resistance. Include an initial threat, a phase for preparation/intel gathering, multiple combat engagements with escalating stakes (e.g., reinforcements, environmental shifts), and a clear resolution of the conflict, whether victory or strategic retreat. **Ensure the conflict's scale ranges from a desperate skirmish affecting a handful of individuals or a small outpost, to a more substantial battle with consequences for a specific faction or region, rather than initiating a galactic war.**",
        "Heist/Infiltration Adventure": "Generate a TTRPG adventure where players plan and execute a daring operation to acquire something, extract someone, or sabotage a facility. The adventure should focus on stealth, meticulous planning, and specialized skills. Key phases include detailed reconnaissance, precise infiltration through security systems and patrols, execution of the primary objective, and a challenging exfiltration/escape, often under pursuit. **Adjust the scale so the heist's consequences impact specific individuals, a corporation's bottom line, or the local balance of power, rather than triggering an interstellar crisis.**",
        "Social/Diplomacy Adventure": "Generate a TTRPG adventure that revolves around complex social interactions, negotiations, and political maneuvering. The objective should involve players influencing NPCs, mediating disputes, forging alliances, or uncovering political espionage. Include elements of information gathering through networking, engaging in multi-party negotiations, navigating intrigue and potential betrayals, and resolving the diplomatic or social conflict through persuasion and understanding. **Scale the adventure's impact to affect specific factions, trade routes, or the governance of a single planet/station, rather than reshaping the entire galactic political landscape.**",
        "Survival/Endurance Adventure": "Generate a TTRPG adventure focused on players overcoming extreme environmental challenges, relentless pursuit, or severe resource scarcity. The adventure should begin with players stranded or facing an overwhelming threat, requiring them to manage limited resources, improvise solutions for survival (e.g., repairing systems, scavenging), and endure escalating difficulties. The core theme is resilience against overwhelming odds, culminating in rescue, escape, or triumph over the environment/pursuer. **The scale of survival should typically be focused on the immediate threat to the players and those directly around them (a ship's crew, a small colony, trapped miners), with consequences localized to their immediate survival or the fate of a contained group, not the survival of a species or civilization.**",
    }
