import json
import re
from datetime import datetime

import markdown
from autonomous.model.automodel import AutoModel
from autonomous.tasks import AutoTasks
from dmtoolkit import dmtools

from autonomous import log
from models.audio.audio import Audio
from models.campaign.campaign import Campaign
from models.campaign.episode import Episode
from models.dungeon.dungeon import Dungeon
from models.dungeon.dungeonroom import DungeonRoom
from models.gmscreen.gmscreentable import GMScreenTable
from models.stories.event import Event
from models.stories.lore import Lore
from models.stories.quest import Quest
from models.stories.story import Story
from models.ttrpgobject.ability import Ability
from models.ttrpgobject.character import Character
from models.ttrpgobject.city import City
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.district import District
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.location import Location
from models.ttrpgobject.region import Region
from models.ttrpgobject.vehicle import Vehicle
from models.user import User
from models.world import World


####################################################################################################
# Tasks
####################################################################################################
def _generate_task(model, pk):
    if obj := AutoModel.get_model(model, pk):
        obj.generate()
    return {"url": f"/api/{obj.path}/manage"}


def _generate_character_from_dndbeyond_task(pk):
    if not (obj := Character.get(pk)) or not obj.dnd_beyond_id:
        return {"url": "#"}

    results = dmtools.get_dndbeyond_character(obj.dnd_beyond_id)
    log(json.dumps(results, indent=4), _print=True)
    if results:
        obj.name = results.get("name") or obj.name
        obj.age = results.get("age") or obj.age
        obj.gender = results.get("gender") or obj.gender
        obj.species = results.get("race") or obj.species
        obj.archetype = results.get("class_name") or obj.archetype
        obj.hitpoints = results.get("hp") or obj.hitpoints
        obj.strength = results.get("str") or obj.strength
        obj.dexterity = results.get("dex") or obj.dexterity
        obj.constitution = results.get("con") or obj.constitution
        obj.intelligence = results.get("int") or obj.intelligence
        obj.wisdom = results.get("wis") or obj.wisdom
        obj.charisma = results.get("cha") or obj.charisma
        obj.ac = max(int(results.get("ac", 0)) + 10, int(obj.ac))
        obj.speed = (
            results.get("speed").get("walk") if results.get("speed") else obj.speed
        )
        obj.save()

        if results.get("wealth"):
            currency = "<h4>Currency</h4>"
            for currency, amount in results.get("wealth").items():
                text = f"{currency}: {amount}"

            for idx, w in enumerate(obj.wealth):
                if isinstance(w, str) and w.strip().startswith(currency):
                    obj.wealth.remove(w)
            obj.wealth.append(text)
            obj.save()

        if results.get("inventory"):
            for item in results.get("inventory"):
                # remove any +%d from item names
                name = re.sub(r"\+\d+", "", item["name"]).strip(", ")
                itemobj = Item.find(name=name, world=obj.world)
                if not itemobj:
                    itemobj = Item(
                        world=obj.world,
                        name=name,
                        parent=obj,
                        backstory=f"A {name} from D&D5e, using the same stats as in D&D Beyond.",
                    )
                    itemobj.save()
                    itemobj.generate()
                    itemobj.description = itemobj.description.replace(
                        itemobj.name, name
                    )
                    itemobj.backstory = itemobj.backstory.replace(itemobj.name, name)
                    itemobj.name = name
                    itemobj.save()
                if not itemobj.image:
                    itemobj.generate_image()
                obj.add_association(itemobj)
                obj.save()

        if features := results.get("features") | results.get("spells"):
            for name, feature in features.items():
                abilityobj = Ability.find(name=name, world=obj.world)
                if not abilityobj:
                    description = f"The {name} from D&D5e, using the same stats and mechanics as in D&D Beyond."
                    response = obj.system.generate_json(
                        f"Generate a unique {obj.genre} TTRPG ability for the following: {obj.name}: {obj.backstory}",
                        f"Given a description of an element in a {obj.genre} TTRPG world, generate a new ability that is consistent with the character described and follows these guidelines: {description}.\nProvide the ability in JSON format.",
                        Ability._funcobj,
                    )
                    if response.get("name"):
                        abilityobj = Ability(**response)
                        abilityobj.world = obj.world
                        abilityobj.description = abilityobj.description.replace(
                            abilityobj.name, name
                        )
                        abilityobj.mechanics = abilityobj.mechanics.replace(
                            abilityobj.name, name
                        )
                        abilityobj.name = name
                        abilityobj.save()
                if abilityobj and abilityobj not in obj.abilities:
                    obj.abilities += [abilityobj]
                    obj.save()
        return {"url": f"/api/{obj.path}/manage"}


def _generate_map_task(model, pk):
    if obj := World.get_model(model, pk):
        obj.generate_map()
    return {"url": f"/api/{obj.path}/map"}


def _generate_history_task(model, pk):
    if obj := World.get_model(model, pk):
        obj.resummarize()
    return {"url": f"/api/{obj.path}/history"}


def _generate_ability_task(pk):
    if obj := Ability.get(pk):
        obj.generate()
    else:
        log("Ability not found", _print=True)
    return {
        "url": f"/api/ability/{obj.pk}/manage",
        "target": f"ability_{obj.pk}",
        "select": f"ability_{obj.pk}",
        "swap": "outerHTML",
    }


def _generate_image_task(model, pk):
    if obj := AutoModel.get_model(model, pk):
        obj.generate_image()
    return {"url": f"/api/{obj.path}/manage"}


def _generate_episode_transcription_task(pk):
    if obj := Episode.get(pk):
        obj.transcribe()
    return {"url": f"/api/{obj.path}/transcribe"}


def _generate_campaign_summary_task(pk):
    if obj := Campaign.get(pk):
        obj.resummarize()
    return {"url": f"/api/{obj.path}/manage"}


def _generate_session_summary_task(pk):
    if obj := Episode.get(pk):
        obj.resummarize()
    return {"url": f"/api/{obj.path}/manage"}


def _generate_session_report_task(pk):
    if obj := Episode.get(pk):
        obj.regenerate_report()
    return {"url": f"/api/{obj.path}/manage"}


def _generate_episode_transcription_summary_task(pk):
    if obj := Episode.get(pk):
        obj.summarize_transcription()
    return {"url": f"/api/{obj.path}/details"}


def _generate_episode_graphic_task(pk):
    if obj := Episode.get(pk):
        obj.generate_graphic()
    return {"url": f"/api/{obj.path}/graphic"}


def _generate_character_chat_task(pk, chat):
    if obj := Character.get(pk) or Creature.get(pk):
        obj.chat(chat)
    return {"url": f"/api/{obj.path}/chat"}


def _generate_table_items_task(pk, worldpk, prompt):
    table = GMScreenTable.get(pk)
    table.generate_table(prompt)
    return {"url": f"/world/{worldpk}/manage_screens"}


def _generate_dungeon_map_task(pk):
    obj = Dungeon.get(pk)
    obj.generate_map()
    return {"url": f"/api/{obj.location.path}/dungeon"}


def _generate_dungeon_room_task(pk):
    obj = DungeonRoom.get(pk)
    obj.generate()
    return {"url": f"/api/dungeon/room/{obj.pk}/manage", "target": "dungeon-container"}


def _generate_dungeon_room_map_task(pk):
    obj = DungeonRoom.get(pk)
    obj.generate_map()
    return {"url": f"/api/dungeon/room/{obj.pk}/manage", "target": "dungeon-container"}


def _generate_dungeon_room_encounter_task(pk):
    obj = DungeonRoom.get(pk)
    obj.generate_encounter()
    return {"url": f"/api/dungeon/room/{obj.pk}/manage", "target": "dungeon-container"}


def _generate_quest_task(pk):
    obj = Quest.get(pk)
    obj.generate_quest()
    return {"url": f"/api/{obj.contact.path}/quests"}


def _generate_story_task(pk):
    story = Story.get(pk)
    story.generate()
    return {"url": f"/api/{story.path}/manage"}


def _generate_story_summary_task(pk):
    if obj := Story.get(pk):
        obj.summarize()
    return {"url": f"/api/{obj.path}/history"}


def _generate_event_task(pk):
    event = Event.get(pk)
    event.generate()
    return {"url": f"/api/{event.path}/manage"}


def _generate_event_from_events_task(event_ids):
    events = [Event.get(eid) for eid in event_ids if Event.get(eid)]
    if not events:
        return {"url": "#"}
    world = events[0].world
    new_event = Event(world=world)
    new_event.generate_from_events(events)
    return {"url": f"/api/{new_event.path}/timeline#{new_event.pk}"}


def _generate_event_summary_task(pk):
    event = Event.get(pk)
    event.summarize()
    return {"url": f"/api/{event.path}/manage"}


def _generate_lore_task(pk, prompt):
    lore = Lore.get(pk)
    lore.generate(prompt)
    return {"url": f"/api/world/{lore.world.pk}/lore"}
