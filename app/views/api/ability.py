r"""
# Ability API Documentation
"""

import os

import requests
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from models.ttrpgobject.ability import Ability

from ._utilities import loader as _loader

ability_endpoint = Blueprint("abiliyt", __name__)


# MARK: CRUD routes
###########################################################
##                    CRUD Routes                        ##
###########################################################


@ability_endpoint.route("/new", methods=("POST",))
def addnewability():
    user, obj, request_data = _loader()
    ab = Ability(world=obj.world, name="New Ability")
    ab.save()
    obj.abilities += [ab]
    obj.save()
    return get_template_attribute("shared/_abilities.html", "manage")(user, obj)


@ability_endpoint.route("/add", methods=("POST",))
def addability():
    user, obj, request_data = _loader()
    log(request_data)
    ab = Ability.get(request_data.get("apk"))
    if ab not in obj.abilities:
        log(obj.abilities)
        obj.abilities += [ab]
        log(obj.abilities)
        obj.save()
        log(obj.abilities)
    return get_template_attribute("shared/_abilities.html", "manage")(user, obj)


@ability_endpoint.route("/<string:pk>/edit", methods=("GET",))
def getability(pk):
    user, obj, request_data = _loader()
    a = Ability.get(pk)
    return get_template_attribute("models/_ability.html", "ability_edit")(user, a)


@ability_endpoint.route("/<string:pk>/update", methods=("POST",))
def updateability(pk):
    user, obj, request_data = _loader()
    if a := Ability.get(pk):
        a.name = request.json.get("name", a.name)
        a.action = request.json.get("action", a.action)
        a.category = request.json.get("category", a.category)
        a.description = request.json.get("description", a.description)
        a.effects = request.json.get("effects", a.effects)
        a.duration = request.json.get("duration", a.duration)
        a.dice_roll = request.json.get("dice_roll", a.dice_roll)
        a.mechanics = request.json.get("mechanics", a.mechanics)
        a.save()
    return get_template_attribute("models/_ability.html", "ability_edit")(user, a)


@ability_endpoint.route("/<string:pk>/generate", methods=("POST",))
def generateability(pk):
    user, obj, *_ = _loader()
    ability = Ability.get(pk)
    if not ability.description.strip():
        ability.description = f"An ability or feature appropriate for a {ability.type} with the following description: {obj.backstory_summary}."
        ability.save()
    response = requests.post(
        f"http://{os.environ.get('TASKS_SERVICE_NAME')}:{os.environ.get('COMM_PORT')}/generate/ability/{pk}",
    ).text
    return response


@ability_endpoint.route("/<string:apk>/remove", methods=("POST",))
def removeability(apk):
    user, obj, *_ = _loader()
    if a := Ability.get(apk):
        if a in obj.abilities:
            obj.abilities.remove(a)
            obj.save()
        a.world = obj.world
        a.save()
    return get_template_attribute("shared/_abilities.html", "manage")(user, obj)


@ability_endpoint.route("/<string:apk>/delete", methods=("POST",))
def deleteability(apk):
    if a := Ability.get(apk):
        a.delete()
    return "success"
