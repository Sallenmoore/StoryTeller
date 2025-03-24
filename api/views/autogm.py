"""
# Components API Documentation

## Components Endpoints
"""

import os
import random

import dmtoolkit
import requests
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from models.ttrpgobject.faction import Faction

from ._utilities import loader as _loader

autogm_endpoint = Blueprint("autogm", __name__)


###########################################################
##             Screen Manage Routes                      ##
###########################################################
@autogm_endpoint.route("/", methods=("POST",))
def index():
    user, obj, *_ = _loader()
    world = obj.get_world()
    world.autogm.save()
    return get_template_attribute("autogm/_index.html", "autogm")(user, world)


@autogm_endpoint.route("/party", methods=("POST",))
def partygenerate():
    user, obj, world, *_ = _loader()
    world.autogm.party = Faction.get(request.json.get("party_pk"))
    world.autogm.save()
    result = requests.post(
        f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{world.pk}/autogm/episode",
        json={"msg": ""},
    ).text
    log(result)
    return result


@autogm_endpoint.route("/episode/generate", methods=("POST",))
def episodegenerate():
    user, obj, world, *_ = _loader()
    result = requests.post(
        f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{world.pk}/autogm/episode",
        json={"msg": request.json.get("msg")},
    ).text
    log(result)
    return result


@autogm_endpoint.route("/episode/clear", methods=("POST",))
def episodeclear():
    user, obj, *_ = _loader()
    world = obj.get_world()
    world.autogm.episode = ""
    world.autogm.scenes = []
    world.autogm.save()
    return get_template_attribute("autogm/_index.html", "autogm")(user, world)
