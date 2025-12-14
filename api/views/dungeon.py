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
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.district import District
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.location import Location
from models.ttrpgobject.vehicle import Vehicle
from models.utility import tasks as utility_tasks
from models.world import World

from ._utilities import loader as _loader

dungeon_endpoint = Blueprint("dungeon", __name__)


###########################################################
##                    dungeon CRUD Routes                  ##
###########################################################


@dungeon_endpoint.route("/create/fiveroom", methods=("POST",))
@dungeon_endpoint.route("/create/random", methods=("POST",))
@dungeon_endpoint.route("/create", methods=("POST",))
def create_dungeon():
    user, obj, *_ = _loader()
    log(request.json)
    if obj.dungeon:
        obj.dungeon.delete()
    dungeon = Dungeon(location=obj)
    dungeon.theme = obj.traits
    dungeon.desc = obj.desc
    dungeon.save()
    obj.dungeon = dungeon
    obj.save()
    if request.path.endswith("fiveroom"):
        for _ in range(5):
            obj.dungeon.create_room()
    elif request.path.endswith("random"):
        for _ in range(random.randint(3, 10)):
            obj.dungeon.create_room()
    utility_tasks.start_task(f"/generate/dungeon/{obj.dungeon.pk}/rooms")
    return get_template_attribute("shared/_dungeon.html", "dungeon")(user, obj)


@dungeon_endpoint.route("/<string:dpk>/update", methods=("POST",))
def edit_dungeon(dpk=None):
    user, obj, request_data = _loader()
    log(request.json)
    dungeon = Dungeon.get(dpk)
    dungeon.desc = request.json.get("desc", dungeon.desc)
    dungeon.theme = request.json.get("theme", dungeon.theme)
    dungeon.save()
    return get_template_attribute("shared/_dungeon.html", "dungeon")(user, obj)


@dungeon_endpoint.route("/create/room", methods=("POST",))
def create_dungeonroom():
    user, obj, request_data = _loader()
    if not obj.dungeon or isinstance(obj.dungeon, str):
        dungeon = Dungeon(location=obj)
        dungeon.theme = obj.traits
        dungeon.desc = obj.desc
        dungeon.save()
        obj.dungeon = dungeon
        obj.save()
    room = obj.dungeon.create_room()

    return get_template_attribute("shared/_dungeon.html", "room")(
        user,
        room,
    )


###########################################################
##               dungeonroom CRUD Routes                 ##
###########################################################


@dungeon_endpoint.route(
    "room/<string:roompk>",
    methods=(
        "GET",
        "POST",
    ),
)
def room(roompk):
    user, *_ = _loader()
    room = DungeonRoom.get(roompk)
    return get_template_attribute("shared/_dungeon.html", "room")(
        user,
        room,
    )


@dungeon_endpoint.route("/room/<string:dpk>/entrance", methods=("POST",))
def dungeon_entrance(dpk):
    user, obj, *_ = _loader()
    dr = DungeonRoom.get(dpk)
    dr.is_entrance = not dr.is_entrance
    dr.save()
    return get_template_attribute("shared/_dungeon.html", "dungeon")(
        user,
        obj,
    )


@dungeon_endpoint.route("/room/<string:roompk>/manage", methods=("POST",))
def edit_room(roompk=None):
    user, _, request_data = _loader()
    log(request_data)
    room = DungeonRoom.get(roompk)
    room.name = request_data.get("name", room.name)
    room.desc = request_data.get("desc", room.desc)
    room.theme = request_data.get("theme", room.theme)
    room.structure_type = request_data.get("structure_type", room.structure_type)
    room.dimensions = request_data.get("dimensions", room.dimensions)
    room.shape = request_data.get("shape", room.shape)
    room.sensory_details = request_data.get("sensory_details", room.sensory_details)
    room.features = request_data.get("features", room.features)
    room.map_prompt = request_data.get("map_prompt", room.map_prompt)
    room.save()
    return get_template_attribute("shared/_dungeon.html", "manageroom")(
        user,
        room,
    )


@dungeon_endpoint.route(
    "/room/<string:roompk>/add/association",
    methods=("POST",),
)
def new_association(roompk):
    user, _, request_data = _loader()
    log(request_data)
    room = DungeonRoom.get(roompk)
    model_path = request_data.get("apath")
    model_name = model_path.split("/")[0]
    pk = model_path.split("/")[1]
    association = AutoModel.get_model(model_name, pk)
    if model_name.lower() == "character" and association not in room.characters:
        room.characters += [association]
    elif model_name.lower() == "creature" and association not in room.creatures:
        room.creatures += [association]
    elif model_name.lower() == "item" and association not in room.loot:
        room.loot += [association]
    elif model_name.lower() == "encounter" and association not in room.encounters:
        room.encounters += [association]
    association.add_association(room.location)
    room.save()
    return get_template_attribute("shared/_dungeon.html", "manageroom")(
        user,
        room,
    )


@dungeon_endpoint.route(
    "/room/<string:roompk>/add/encounter",
    methods=("POST",),
)
def new_encounter(roompk):
    return utility_tasks.start_task(f"/generate/dungeon/room/{roompk}/encounter")


@dungeon_endpoint.route(
    "/room/<string:roompk>/association/remove/<string:associationmodel>/<string:associationpk>",
    methods=("POST",),
)
def remove_association(roompk, associationmodel, associationpk):
    user, _, request_data = _loader()
    log(request_data)
    room = DungeonRoom.get(roompk)
    if associationmodel == "character":
        if association := Character.get(associationpk):
            room.characters = [a for a in room.characters if a.pk != association.pk]
    elif associationmodel == "creature":
        if association := Creature.get(associationpk):
            room.creatures = [a for a in room.creatures if a.pk != association.pk]
    elif associationmodel == "item":
        if association := Item.get(associationpk):
            room.items = [a for a in room.items if a.pk != association.pk]
    room.save()
    return get_template_attribute("shared/_dungeon.html", "manageroom")(
        user,
        room,
    )


@dungeon_endpoint.route(
    "/room/<string:roompk>/connect/<string:connected_roompk>", methods=("POST",)
)
def connect_room(roompk=None, connected_roompk=None):
    user, *_ = _loader()
    log(request.json)
    room = DungeonRoom.get(roompk)
    connected_room = DungeonRoom.get(connected_roompk)
    room.disconnect(connected_room) if room.is_connected(
        connected_room
    ) else room.connect(connected_room)
    return get_template_attribute("shared/_dungeon.html", "manageroom")(
        user,
        room,
    )


@dungeon_endpoint.route("/room/<string:roompk>/delete", methods=("POST",))
def delete_room(roompk=None):
    user, obj, *_ = _loader()
    log(request.json)
    room = DungeonRoom.get(roompk)
    room.delete()
    return get_template_attribute("shared/_dungeon.html", "dungeon")(
        user,
        obj,
    )
