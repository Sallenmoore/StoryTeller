import json

from autonomous.model.automodel import AutoModel
from autonomous.tasks import AutoTasks
from dmtoolkit import dmtools

from autonomous import log
from models.campaign.campaign import Campaign
from models.campaign.episode import Episode
from models.gmscreen.gmscreentable import GMScreenTable
from models.stories.quest import Quest
from models.stories.story import Story
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
    if obj := World.get_model(model, pk):
        obj.generate()
        if not obj.image:
            AutoTasks().task(
                _generate_image_task,
                model,
                pk,
            )
    return {"url": f"/api/{obj.path}/manage"}


def _generate_map_task(model, pk):
    if obj := World.get_model(model, pk):
        obj.generate_map()
    return {"url": f"/api/{obj.path}/map"}


def _generate_history_task(model, pk):
    if obj := World.get_model(model, pk):
        obj.resummarize()
    return {"url": f"/api/{obj.path}/history"}


def _generate_image_task(model, pk):
    if obj := AutoModel.get_model(model, pk):
        obj.generate_image()
    return {"url": f"/api/{obj.path}/manage"}


def _generate_campaign_summary_task(pk):
    if obj := Campaign.get(pk):
        obj.resummarize()
    return {"url": f"/api/{obj.path}/manage"}


def _generate_session_summary_task(pk):
    if obj := Episode.get(pk):
        obj.resummarize()
    return {"url": f"/api/episode/{obj.pk}/manage"}


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
