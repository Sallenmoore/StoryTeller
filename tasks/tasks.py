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
                itemobj = Item.find(name=name)
                if not itemobj:
                    itemobj = Item(
                        world=obj.world,
                        name=name,
                        parent=obj,
                        backstory=f"A {name} from D&D5e, using the same stats as in D&D Beyond.",
                    )
                    itemobj.save()
                    itemobj.generate()
                if not itemobj.image:
                    itemobj.generate_image()
                obj.add_association(itemobj)
                obj.save()

        if features := results.get("features") | results.get("spells"):
            for name, feature in features.items():
                abilityobj = Ability.find(name=name)
                if not abilityobj:
                    description = f"The {name} from D&D5e, using the same stats and mechanics as in D&D Beyond."
                    response = obj.system.generate_json(
                        f"Generate a unique {obj.genre} TTRPG ability for the following: {obj.name}: {obj.backstory}",
                        f"Given a description of an element in a {obj.genre} TTRPG world, generate a new ability that is consistent with the character described and follows these guidelines: {description}.\nProvide the ability in JSON format.",
                        Ability._funcobj,
                    )
                    if response.get("name"):
                        abilityobj = Ability(**response)
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
        transcription = Audio.transcribe(
            obj.audio,
            prompt=f"""Reinterpret the audio recording of a live TTRPG session as a screenplay-style transcript for an episodic adventure. Leave out any discussion of game mechanics, or side conversations not relevant to the narrative. Ignore any 'umms' or 'ahs' or similar filler words. Identify and separate distinct speakers as much as possible using the provided information. The party characters are: {", ".join([f"{c.name}:{c.backstory_summary}]" for c in obj.players])}.

            Additonal associations that may appear in the transcription include: {", ".join([f"{a.name}:{a.backstory_summary}" for a in obj.associations if a not in obj.players])}.

            Keep the narrative consistent with the following setting: {obj.world.backstory}.

            Format the transcription in Markdown.
""",
            display_name="episode.mp3",
        )
        log(transcription, _print=True)
        if not transcription:
            obj.transcription = "Transcription failed or was empty."
        else:
            obj.transcription = f"""
<h2>TRANSCRIPTION: {datetime.now().strftime("%B %d, %Y - %I:%M %p")} {"=" * 20}</h2>
<br><br>
{markdown.markdown(transcription)}
"""
        obj.save()
    return {
        "url": f"/api/{obj.path}/transcribe",
        "target": "output-area",
        "select": "output-area",
        "swap": "outerHTML",
    }


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


def _generate_dungeon_task(model, pk):
    obj = World.get_model(model, pk)
    obj.generate_dungeon()
    return {"url": f"/api/{obj.path}/map"}


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
