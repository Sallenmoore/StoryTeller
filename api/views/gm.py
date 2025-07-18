# Built-In Modules
import os
from datetime import datetime

import requests

# external Modules
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from autonomous.auth.autoauth import AutoAuth
from autonomous.tasks.autotask import AutoTasks
from models.campaign.campaign import Campaign
from models.campaign.episode import Episode
from models.gm.gm import GameMaster
from models.images.image import Image
from models.systems.fantasy import FantasySystem
from models.systems.hardboiled import HardboiledSystem
from models.systems.historical import HistoricalSystem
from models.systems.horror import HorrorSystem
from models.systems.postapocalyptic import PostApocalypticSystem
from models.systems.scifi import SciFiSystem
from models.systems.western import WesternSystem
from models.ttrpgobject.character import Character
from models.ttrpgobject.city import City
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.encounter import Encounter
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.location import Location
from models.ttrpgobject.region import Region
from models.user import User
from models.world import World

from ._utilities import loader as _loader

gm_endpoint = Blueprint("gm", __name__)


@gm_endpoint.route("/", methods=("POST",))
def index():
    user, world, *_ = _loader()
    if not world.gm:
        world.gm = GameMaster()
        world.gm.save()
        world.save()
    return get_template_attribute("manage/_gm.html", "gm")(user, world)


@gm_endpoint.route("/add/party", methods=("POST",))
def create():
    user, world, *_ = _loader()
    if not world.gm:
        index()
        user, world, *_ = _loader()
    partypk = request.json.get("party")
    log(world.gm, partypk)
    world.gm.party = Faction.get(partypk)
    world.gm.save()
    return index()


@gm_endpoint.route(
    "associations/add/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def associationentry(pk, amodel, apk=None):
    user, obj, world, *_ = _loader()
    obj = world.get_model(amodel, apk)
    world.gm.add_association(obj)
    return index()


@gm_endpoint.route(
    "associations/add/search",
    methods=("POST",),
)
def associationsearch():
    user, obj, world, *_ = _loader()
    query = request.json.get("query")
    results = world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [r for r in results if r not in world.gm.associations]
    # log(macro, query, [r.name for r in results])
    return get_template_attribute("manage/_gm.html", "gm_dropdown")(user, obj, results)


@gm_endpoint.route(
    "association/<string:amodel>/<string:apk>/delete",
    methods=("POST",),
)
def episodeassociationentrydelete(amodel, apk):
    user, obj, world, *_ = _loader()
    obj = world.get_model(amodel, apk)
    world.gm.remove_association(obj)
    return "<p>success</p>"
