"""
# Components API Documentation

## Components Endpoints
"""

import json
import os
import random

import requests
from autonomous.model.automodel import AutoModel
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from models.campaign import Campaign
from models.campaign.episode import Episode
from models.dungeon.dungeon import Dungeon
from models.dungeon.dungeonroom import DungeonRoom
from models.stories.encounter import Encounter
from models.stories.event import Event
from models.stories.story import Story
from models.ttrpgobject.character import Character
from models.ttrpgobject.district import District
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.location import Location
from models.ttrpgobject.vehicle import Vehicle
from models.world import World

from ._utilities import loader as _loader

dungeon_endpoint = Blueprint("dungeon", __name__)


###########################################################
##                    dungeon CRUD Routes                  ##
###########################################################


@dungeon_endpoint.route("/create", methods=("POST",))
def create_dungeon():
    user, obj, request_data = _loader()
    log(request.json)
    if obj.dungeon:
        obj.dungeon.delete()
    dungeon = Dungeon(location=obj)
    dungeon.theme = obj.traits
    dungeon.desc = obj.desc
    dungeon.save()
    obj.dungeon = dungeon
    obj.save()
    return get_template_attribute(
        f"models/_{obj.model_name().lower()}.html", "dungeon"
    )(user, obj)


@dungeon_endpoint.route("/<string:dpk>/update", methods=("POST",))
def edit_dungeon(dpk=None):
    user, obj, request_data = _loader()
    log(request.json)
    dungeon = Dungeon.get(dpk)
    dungeon.desc = request.json.get("desc", dungeon.desc)
    dungeon.theme = request.json.get("theme", dungeon.theme)
    dungeon.save()
    return get_template_attribute(
        f"models/_{obj.model_name().lower()}.html", "dungeon"
    )(user, obj)


###########################################################
##               dungeonroom CRUD Routes                 ##
###########################################################


@dungeon_endpoint.route("/create/room", methods=("POST",))
@dungeon_endpoint.route("/create/room/from/<string:lpk>", methods=("POST",))
def create_dungeonroom(lpk=None):
    user, obj, request_data = _loader()
    log(request.json)
    if not obj.dungeon:
        dungeon = Dungeon(location=obj)
        dungeon.theme = obj.traits
        dungeon.desc = obj.desc
        dungeon.save()
        obj.dungeon = dungeon
        obj.save()
    if location := Location.get(lpk):
        obj.dungeon.create_room_from_location(location)
        location.delete()
    else:
        obj.dungeon.create_room()

    return get_template_attribute(
        f"models/_{obj.model_name().lower()}.html", "dungeon"
    )(user, obj)


@dungeon_endpoint.route(
    "room/<string:roompk>",
    methods=(
        "GET",
        "POST",
    ),
)
def room(roompk):
    user, obj, request_data = _loader()
    room = DungeonRoom.get(roompk)
    return get_template_attribute("models/_dungeonroom.html", "index")(
        user,
        room,
    )


@dungeon_endpoint.route("/room/<string:roompk>/update", methods=("POST",))
def edit_room(roompk=None):
    user, obj, request_data = _loader()
    log(request.json)
    room = DungeonRoom.get(roompk)
    room.desc = request.json.get("desc", room.desc)
    room.theme = request.json.get("theme", room.theme)
    room.sensory_details = request.json.get("sensory_details", room.sensory_details)
    room.save()
    return get_template_attribute("models/_dungeonroom.html", "manage")(user, room)
