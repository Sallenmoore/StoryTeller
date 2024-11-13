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
from models.world import World

models = {
    "player": "Character",
    "player_faction": "Faction",
    "poi": "POI",
}  # add model names that cannot just be be titlecased from lower case, such as POI or 'player':Character


def _import_model(model):
    model_name = models.get(model, model.title())
    if Model := AutoModel.load_model(model_name):
        return Model
    return None


####################################################################################################
# Tasks
####################################################################################################
def _generate_task(model, pk):
    if Model := _import_model(model):
        obj = Model.get(pk)
        obj.generate()
        obj.resummarize()
    return {"url": f"/api/{obj.path}/details"}


def _generate_battlemap_task(model, pk):
    if Model := _import_model(model):
        obj = Model.get(pk)
        obj.generate_map()
    return {"url": f"/api/{obj.path}/map"}


def _generate_history_task(model, pk):
    if Model := _import_model(model):
        obj = Model.get(pk)
        obj.resummarize(upload=True)
    return {"url": f"/api/{obj.path}/history"}


def _generate_image_task(model, pk):
    if Model := _import_model(model):
        obj = Model.get(pk)
        obj.resummarize()
        obj.generate_image()
    return {"url": f"/api/{obj.path}/details"}


def _generate_chat_task(pk, message):
    obj = Character.get(pk)
    obj.chat(message)
    return {"url": f"/api/{obj.path}/chats"}


def _generate_autogm_start_task(pk, year=1):
    obj = Character.get(pk)
    year = int(year)
    obj.start_gm_session(year=year)
    return {"url": f"/api/{obj.path}/autogm"}


def _generate_autogm_run_task(pk, message="", roll_type="Ability Check", roll_dice=""):
    obj = Character.get(pk)
    if roll_dice:
        roll_result = dmtools.dice_roll(roll_dice)[0]
        message = f"""{message}

        {obj.name} rolls {roll_type} - RESULT:  {roll_result}
        """
    obj.run_gm_session(message=message)
    return {"url": f"/api/{obj.path}/autogm"}


def _generate_autogm_end_task(pk, message=""):
    obj = Character.get(pk)
    obj.end_gm_session(message=message)
    return {"url": f"/api/{obj.path}/autogm"}


def _generate_autogm_clear_task(pk):
    obj = Character.get(pk)
    obj.autogm_summary = {}
    obj.save()
    for img in obj.gm.images:
        img.remove_img_file()
        img.delete()
    obj.gm.images = []
    obj.gm.history = []
    obj.gm.save()
    return {"url": f"/api/{obj.path}/autogm"}
