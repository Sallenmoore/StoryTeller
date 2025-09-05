"""
# Components API Documentation

## Components Endpoints

"""

import os
import random

import requests
from flask import Blueprint, get_template_attribute, request
from jinja2 import TemplateNotFound

from autonomous import log
from models.campaign.campaign import Campaign
from models.campaign.episode import Episode
from models.stories.quest import Quest  # for the importer
from models.stories.story import Story
from models.ttrpgobject.encounter import Encounter
from models.world import World

from ._utilities import loader as _loader

index_endpoint = Blueprint("page", __name__)


###########################################################
##                    Component Routes                   ##
###########################################################
@index_endpoint.route(
    "/auth/login",
    methods=(
        "GET",
        "POST",
    ),
)
def login():
    worlds = World.all()
    worlds = random.sample(worlds, 4) if len(worlds) > 4 else worlds
    return get_template_attribute("login.html", "login")(worlds=worlds)


@index_endpoint.route(
    "/home",
    methods=(
        "GET",
        "POST",
    ),
)
def home():
    user, obj, request_data = _loader()
    return get_template_attribute("home.html", "home")(user)


@index_endpoint.route(
    "/build",
    methods=("POST",),
)
def build():
    user, obj, request_data = _loader()
    World.build(
        system=request.json.get("system"),
        user=user,
        name=request.json.get("name"),
        desc=request.json.get("desc"),
        backstory=request.json.get("backstory"),
    )

    return get_template_attribute("home.html", "home")(user)


@index_endpoint.route("/build/form", methods=("POST",))
def buildform():
    user, obj, request_data = _loader()
    return get_template_attribute("home.html", "worldbuild")(user=user)


###########################################################
##                    Model Routes                       ##
###########################################################
@index_endpoint.route(
    "/<string:model>/<string:pk>/<string:page>",
    methods=(
        "GET",
        "POST",
    ),
)
@index_endpoint.route(
    "/<string:model>/<string:pk>",
    methods=(
        "GET",
        "POST",
    ),
)
def model(model, pk, page=""):
    user, obj, request_data = _loader()
    page = page or "index"
    return get_template_attribute(
        f"models/_{obj.__class__.__name__.lower()}.html", page
    )(user, obj)


###########################################################


# MARK: Association routes
###########################################################
##                    Association Routes                 ##
###########################################################
@index_endpoint.route(
    "/<string:model>/<string:pk>/associations/<string:modelstr>",
    methods=("GET", "POST"),
)
@index_endpoint.route(
    "/<string:model>/<string:pk>/associations", methods=("GET", "POST")
)
def associations(model, pk, modelstr=None):
    user, obj, request_data = _loader()
    associations = [
        o
        for o in obj.associations
        if not modelstr or modelstr.lower() == o.model_name().lower()
    ]
    args = dict(request.args) if request.method == "GET" else request.json
    if filter_str := args.get("filter"):
        associations = [o for o in associations if filter_str.lower() in o.name.lower()]
    if sort_str := args.get("sorter"):
        if sort_str.lower() == "name":
            associations.sort(key=lambda x: x.name)
        elif sort_str.lower() == "date":
            associations.sort(key=lambda x: x.start_date)
        elif sort_str.lower() == "type":
            associations.sort(key=lambda x: x.model_name())
        elif sort_str.lower() == "parent":
            associations = [o for o in associations if not o.parent]

    return get_template_attribute(f"models/_{model}.html", "associations")(
        user, obj, associations
    )
