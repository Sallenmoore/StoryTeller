import json

from dmtoolkit import dmtools

from autonomous import log
from autonomous.model.automodel import AutoModel
from autonomous.tasks import AutoTasks
from models.ttrpgobject.character import Character
from models.ttrpgobject.city import City
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.district import District
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.location import Location
from models.ttrpgobject.region import Region
from models.user import User
from models.world import World

models = {
    "player": "Character",
    "player_faction": "Faction",
}  # add model names that cannot just be be titlecased from lower case, such as 'player':Character


def _import_model(model):
    model_name = models.get(model, model.title())
    if Model := AutoModel.load_model(model_name):
        return Model
    return None


####################################################################################################
# Tasks
####################################################################################################
def _generate_task(model, pk):
    if Model := World.get_model(model):
        obj = Model.get(pk)
        obj.generate()
        obj.resummarize()
        if not obj.image:
            obj.generate_image()
    return {"url": f"/api/manage/{obj.path}"}


def _generate_battlemap_task(model, pk):
    if Model := World.get_model(model):
        obj = Model.get(pk)
        obj.generate_map()
    return {"url": f"/api/{obj.path}/map"}


def _generate_history_task(model, pk):
    if Model := World.get_model(model):
        obj = Model.get(pk)
        obj.resummarize(upload=True)
    return {"url": f"/api/{obj.path}/history"}


def _generate_image_task(model, pk):
    if Model := World.get_model(model):
        obj = Model.get(pk)
        obj.resummarize()
        obj.generate_image()
    return {"url": f"/api/{obj.path}/details"}


def _generate_chat_task(pk, message):
    obj = Character.get(pk)
    obj.chat(message)
    return {"url": f"/api/{obj.path}/chats"}


def _generate_autogm_start_task(pk, message=""):
    party = Faction.get(pk)
    party.start_gm_session(scenario=message)
    return {"url": f"/api/autogm/{party.path}"}


def _generate_autogm_run_task(pk, message="", roll_dice=""):
    obj = Faction.get(pk)
    log(roll_dice, _print=True)
    if roll_dice:
        roll_result = dmtools.dice_roll(roll_dice)
        log(roll_result, _print=True)
        obj.autogm_summary[-1].roll_result = roll_result
        obj.autogm_summary[-1].save()
        message = f"""{message}

         Rolls {obj.autogm_summary[-1].roll_type}:{obj.autogm_summary[-1].roll_attribute}
         RESULT:  {roll_result}
        """
    obj.run_gm_session(message=message)
    return {"url": f"/api/autogm/{obj.path}"}


def _generate_autogm_end_task(pk, message=""):
    obj = Faction.get(pk)
    obj.end_gm_session(message=message)
    return {"url": f"/api/autogm/{obj.path}"}


def _generate_autogm_clear_task(pk):
    obj = Character.get(pk)
    for ags in obj.autogm_summary:
        if ags.image:
            ags.image.delete()
        ags.delete()
    obj.autogm_summary = []
    obj.save()
    return {"url": f"/api/autogm/{obj.path}"}
