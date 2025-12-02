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
    if request.path.endswith("fiveroom"):
        for _ in range(5):
            print("creating room")
    elif request.path.endswith("random"):
        num_rooms = random.randint(2, 7)
        for _ in range(num_rooms):
            print("creating room")
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
    user, obj, request_data = _loader()
    room = DungeonRoom.get(roompk)
    return get_template_attribute("shared/_dungeon.html", "room")(
        user,
        room,
    )


@dungeon_endpoint.route("/room/<string:dpk>/entrance", methods=("POST",))
def dungeon_entrance(dpk):
    user, obj, request_data = _loader()
    dr = DungeonRoom.get(dpk)
    dr.is_entrance = not dr.is_entrance
    dr.save()
    return get_template_attribute("shared/_dungeon.html", "dungeon")(
        user,
        obj,
    )


@dungeon_endpoint.route("/room/<string:roompk>/manage", methods=("POST",))
def edit_room(roompk=None):
    user, obj, request_data = _loader()
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


@dungeon_endpoint.route("/room/<string:roompk>/association/search", methods=("POST",))
def search_association(roompk):
    user, obj, request_data = _loader()
    log(request.json)
    room = DungeonRoom.get(roompk)
    search_term = request.json.get("query", "")
    associations = []
    for model in [Character, Creature, Item]:
        results = model.search(name=search_term)
        associations.extend(results)
    return get_template_attribute("shared/_dropdown.html", "search_dropdown")(
        user,
        room,
        f"dungeon/room/{roompk}/association/add",
        associations,
    )


@dungeon_endpoint.route(
    "/room/<string:roompk>/add/<string:associationmodel>",
    methods=("POST",),
)
def new_association(roompk, associationmodel):
    user, obj, request_data = _loader()
    log(request_data)
    room = DungeonRoom.get(roompk)
    if associationmodel == "character":
        association = Character(world=room.world, parent=room.location)
        room.characters += [association]
    elif associationmodel == "creature":
        association = Creature(world=room.world, parent=room.location)
        room.creatures += [association]
    elif associationmodel == "item":
        association = Item(world=room.world, parent=room.location)
        room.loot += [association]
    elif associationmodel == "encounter":
        association = Encounter(world=room.world, parent=room)
        room.encounters += [association]
    association.save()
    room.save()
    room.location.add_association(association)
    return get_template_attribute("shared/_dungeon.html", "manageroom")(
        user,
        room,
    )


@dungeon_endpoint.route(
    "/room/<string:roompk>/association/add/<string:associationmodel>/<string:associationpk>",
    methods=("POST",),
)
def add_association(roompk, associationmodel, associationpk):
    user, obj, request_data = _loader()
    log(request_data)
    room = DungeonRoom.get(roompk)
    if associationmodel == "character":
        if association := Character.get(associationpk):
            room.characters += [association]
    elif associationmodel == "creature":
        if association := Creature.get(associationpk):
            room.creatures += [association]
    elif associationmodel == "item":
        if association := Item.get(associationpk):
            room.items += [association]
    room.save()
    return get_template_attribute("shared/_dungeon.html", "manageroom")(user, room)


@dungeon_endpoint.route(
    "/room/<string:roompk>/association/remove/<string:associationmodel>/<string:associationpk>",
    methods=("POST",),
)
def remove_association(roompk, associationmodel, associationpk):
    user, obj, request_data = _loader()
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
    user, obj, request_data = _loader()
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
    user, obj, request_data = _loader()
    log(request.json)
    room = DungeonRoom.get(roompk)
    room.delete()
    return get_template_attribute("shared/_dungeon.html", "dungeon")(
        user,
        obj,
    )
