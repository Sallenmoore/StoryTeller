import json

from dmtoolkit import dmtools

from autonomous import log
from autonomous.model.automodel import AutoModel
from autonomous.tasks import AutoTasks
from models.autogm.autogmscene import AutoGMScene
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


def _generate_audio_task(pk):
    ags = AutoGMScene.get(pk)
    ags.generate_audio()
    return {"url": f"/api/autogm/{ags.party.pk}"}


def _generate_autogm_task(pk):
    party = Faction.get(pk)
    # log(messagestr)
    party.autogm_session()
    return {"url": f"/api/autogm/{party.pk}"}


def _generate_autogm_combat_task(pk):
    party = Faction.get(pk)
    # log(messagestr)
    party.autogm_combat()
    return {"url": f"/api/autogm/{party.pk}"}
