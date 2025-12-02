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
from models.stories.encounter import Encounter
from models.stories.quest import Quest  # for the importer
from models.stories.story import Story
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
    "/<string:model>/<string:pk>/associations", methods=("GET", "POST")
)
def associations(model, pk):
    user, obj, request_data = _loader()
    associations = obj.associations
    log(model, pk, request_data)
    if filter_str := request_data.get("filter"):
        if len(filter_str) > 2:
            associations = [
                o for o in associations if filter_str.lower() in o.name.lower()
            ]
    if type_str := request_data.get("type"):
        associations = [
            o for o in associations if o.model_name().lower() == type_str.lower()
        ]
    if rel_str := request_data.get("relationship"):
        if rel_str.lower() == "parent":
            associations = [o for o in associations if o in obj.geneology]
        elif rel_str.lower() == "child":
            associations = [o for o in associations if obj == o.parent]
        elif hasattr(obj, "lineage") and rel_str.lower() == "lineage":
            associations = [o for o in associations if o in obj.lineage]
    if sort_str := request_data.get("sorter"):
        order = request_data.get("order", "ascending")
        if sort_str.lower() == "name":
            associations.sort(
                key=lambda x: x.name, reverse=True
            ) if order == "descending" else associations
        elif sort_str.lower() == "date":
            associations = [
                a for a in associations if a.end_date and a.end_date.year > 0
            ]
            associations.sort(
                key=lambda x: x.end_date, reverse=True
            ) if order == "descending" else associations.sort(key=lambda x: x.end_date)
        elif sort_str.lower() == "type":
            associations.sort(
                key=lambda x: x.model_name(), reverse=True
            ) if order == "descending" else associations.sort(
                key=lambda x: x.model_name()
            )
    children = obj.children
    ancestry = obj.geneology
    relations = [
        a for a in [*children, *ancestry] if a.model_name() not in ["World", "Campaign"]
    ]
    associations = [a for a in associations if a not in relations]
    return get_template_attribute(f"models/_{model}.html", "associations")(
        user, obj, extended_associations=associations, direct_associations=relations
    )
