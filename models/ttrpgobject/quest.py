import random

from autonomous import log
from autonomous.model.autoattr import DictAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.base.ttrpgbase import TTRPGBase


class Quest(AutoModel):
    name = StringAttr(default="")
    description = StringAttr(default="")
    scenes = ListAttr(DictAttr(default=""))
    summary = StringAttr(default="")
    rewards = StringAttr(default="")
    contact = ReferenceAttr(choices=["Character"])
    locations = ListAttr(StringAttr(default=""))
    antagonist = StringAttr(default="")
    hook = StringAttr(default="")
    dramatic_crisis = StringAttr(default="")
    climax = StringAttr(default="")
    plot_twists = ListAttr(StringAttr(default=""))
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    status = StringAttr(
        default="available", choices=["available", "active", "completed", "failed"]
    )

    adventure_types = {
        "Exploration/Discovery Adventure": "Generate a TTRPG adventure focused on the players venturing into uncharted or forgotten territory. The core should involve navigating environmental hazards, encountering the unknown (new species, ancient ruins, unique phenomena), and culminating in a significant discovery. Include elements of wonder, mystery, and potential danger from the unfamiliar, requiring the players to overcome obstacles to reach and understand their find. **Vary the scale of the adventure, from a small-scale personal discovery impacting a few individuals or a local community, to a larger-scale find with regional or factional implications, but avoid making it a galactic or world-altering event.**",
        "Investigation/Mystery Adventure": "Generate a TTRPG adventure centered around players acting as detectives. The plot should revolve around a mysterious event (e.g., disappearance, corporate conspiracy, bizarre crime). The adventure must include gathering clues from various locations and NPCs, deducing the truth from potentially misleading information, and leading to a confrontation or revelation of the underlying conspiracy or culprit. Emphasize intrigue, deduction, and information gathering. **Vary the scale of the investigation, from uncovering a local scandal affecting a few NPCs or a specific organization, to revealing a significant but contained plot impacting a city or star system, avoiding universe-wide implications unless explicitly requested.**",
        "Combat/Conflict Adventure": "Generate a TTRPG adventure with a strong emphasis on direct confrontation and tactical combat. The scenario should involve players overcoming a clear antagonist or objective through military operations, mercenary actions, or resistance. Include an initial threat, a phase for preparation/intel gathering, multiple combat engagements with escalating stakes (e.g., reinforcements, environmental shifts), and a clear resolution of the conflict, whether victory or strategic retreat. **Ensure the conflict's scale ranges from a desperate skirmish affecting a handful of individuals or a small outpost, to a more substantial battle with consequences for a specific faction or region, rather than initiating a galactic war.**",
        "Heist/Infiltration Adventure": "Generate a TTRPG adventure where players plan and execute a daring operation to acquire something, extract someone, or sabotage a facility. The adventure should focus on stealth, meticulous planning, and specialized skills. Key phases include detailed reconnaissance, precise infiltration through security systems and patrols, execution of the primary objective, and a challenging exfiltration/escape, often under pursuit. **Adjust the scale so the heist's consequences impact specific individuals, a corporation's bottom line, or the local balance of power, rather than triggering an interstellar crisis.**",
        "Social/Diplomacy Adventure": "Generate a TTRPG adventure that revolves around complex social interactions, negotiations, and political maneuvering. The objective should involve players influencing NPCs, mediating disputes, forging alliances, or uncovering political espionage. Include elements of information gathering through networking, engaging in multi-party negotiations, navigating intrigue and potential betrayals, and resolving the diplomatic or social conflict through persuasion and understanding. **Scale the adventure's impact to affect specific factions, trade routes, or the governance of a single planet/station, rather than reshaping the entire galactic political landscape.**",
        "Survival/Endurance Adventure": "Generate a TTRPG adventure focused on players overcoming extreme environmental challenges, relentless pursuit, or severe resource scarcity. The adventure should begin with players stranded or facing an overwhelming threat, requiring them to manage limited resources, improvise solutions for survival (e.g., repairing systems, scavenging), and endure escalating difficulties. The core theme is resilience against overwhelming odds, culminating in rescue, escape, or triumph over the environment/pursuer. **The scale of survival should typically be focused on the immediate threat to the players and those directly around them (a ship's crew, a small colony, trapped miners), with consequences localized to their immediate survival or the fate of a contained group, not the survival of a species or civilization.**",
    }
