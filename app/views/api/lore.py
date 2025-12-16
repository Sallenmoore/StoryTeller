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
from models.stories.encounter import Encounter
from models.stories.event import Event
from models.stories.lore import Lore
from models.stories.story import Story
from models.ttrpgobject.character import Character
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.vehicle import Vehicle
from models.world import World

from ._utilities import loader as _loader

lore_endpoint = Blueprint("lore", __name__)


###########################################################
##                    lore CRUD Routes                  ##
###########################################################


@lore_endpoint.route("/new", methods=("POST",))
def lore_new():
    user, obj, request_data = _loader()
    lore = Lore(
        name=request_data.get("name"), scope=request_data.get("scope"), world=obj
    )
    lore.save()
    log(lore, lore.world)
    if story := Story.get(request_data.get("storypk")):
        lore.story = story
        lore.associations = story.associations
        lore.backstory = story.summary
    lore.start_date = {
        "day": request_data.get("start_day"),
        "month": request_data.get("start_month"),
        "year": request_data.get("start_year"),
    }
    lore.current_date = {
        "day": request_data.get("start_day"),
        "month": request_data.get("start_month"),
        "year": request_data.get("start_year"),
    }
    lore.save()
    return get_template_attribute("models/_world.html", "lore")(user, lore)


@lore_endpoint.route("/<string:lore_pk>/edit", methods=("POST",))
def lore_edit(lore_pk):
    user, obj, request_data = _loader()
    log(request_data)
    lore = Lore.get(lore_pk)
    if current_day := request_data.get("current_day"):
        lore.current_date.day = int(current_day)
    current_month = request_data.get("current_month")
    if current_month is not None:
        lore.current_date.month = int(current_month)
    if current_year := request_data.get("current_year"):
        lore.current_date.year = int(current_year)
    lore.situation = request_data.get("situation", lore.situation)
    lore.guidance = request_data.get("guidance", lore.guidance)
    lore.setting = (
        obj.world.get_model(*request_data.get("setting").split("/"))
        if request_data.get("setting")
        else lore.setting
    )
    lore.save()
    return get_template_attribute("shared/_lore.html", "lore_details")(user, lore)


@lore_endpoint.route("/<string:lore_pk>/delete", methods=("POST",))
def lore_delete(lore_pk):
    user, obj, _ = _loader()
    if lore := Lore.get(lore_pk):
        lore.delete()
    return get_template_attribute("shared/_lore.html", "lore")(user, obj)


@lore_endpoint.route("/<string:lore_pk>/complete", methods=("POST",))
def lore_complete(lore_pk):
    user, obj, _ = _loader()
    if lore := Lore.get(lore_pk):
        event = Event.create_event_from_lore(lore)
        if event:
            lore.delete()
    return f"""<script>
        window.location.replace('/event/{event.pk}/manage');
    </script>
"""


###########################################################
##                   Lore Association Routes             ##
###########################################################


@lore_endpoint.route(
    "/<string:pk>/party/add/search",
    methods=("POST",),
)
def lorepartysearch(pk):
    user, obj, request_data = _loader()
    lore = Lore.get(pk)
    query = request.json.get("query")
    results = (
        [
            r
            for r in obj.world.search_autocomplete(query=query)
            if r.model_name("Character")
        ]
        if len(query) > 2
        else []
    )
    results = [a for a in results if a not in lore.party]
    return get_template_attribute("shared/_lore.html", "lore_party_dropdown")(
        user, lore, results
    )


@lore_endpoint.route(
    "/<string:pk>/party/add/<string:apk>",
    methods=("POST",),
)
def lorepartyadd(pk, apk=None):
    user, obj, request_data = _loader()
    lore = Lore.get(pk)
    if apk:
        obj = Character.get(apk)
        if obj not in lore.party:
            lore.party += [obj]
            lore.save()
    return get_template_attribute("shared/_lore.html", "lore_details")(user, lore)


@lore_endpoint.route(
    "/<string:pk>/party/remove/<string:apk>",
    methods=("POST",),
)
def lorepartyremove(pk, apk=None):
    user, obj, request_data = _loader()
    lore = Lore.get(pk)
    if apk:
        obj = Character.get(apk)
        if obj in lore.party:
            lore.party.remove(obj)
            lore.save()
    return get_template_attribute("shared/_lore.html", "lore_details")(user, lore)


@lore_endpoint.route(
    "/<string:pk>/association/add/search",
    methods=("POST",),
)
def loreassociationsearch(pk):
    user, obj, request_data = _loader()
    lore = Lore.get(pk)
    query = request.json.get("query")
    results = obj.world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [a for a in results if a not in lore.associations]
    return get_template_attribute("shared/_lore.html", "lore_association_dropdown")(
        user, lore, results
    )


@lore_endpoint.route(
    "/<string:pk>/association/add/<string:amodel>",
    methods=("POST",),
)
@lore_endpoint.route(
    "/<string:pk>/association/add/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def loreassociationadd(pk, amodel, apk=None):
    user, *_ = _loader()
    lore = Lore.get(pk)
    if apk:
        if obj := lore.world.get_model(amodel, apk):
            if obj not in lore.associations:
                lore.associations += [obj]
                lore.save()
    else:
        Model = lore.world.get_model(amodel)
        obj = Model(world=lore.world)
        obj.save()
        lore.associations += [obj]
        lore.save()
    return get_template_attribute("shared/_lore.html", "lore_details")(user, lore)


@lore_endpoint.route(
    "/<string:pk>/association/remove/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def loreassociationremove(pk, amodel, apk=None):
    user, obj, request_data = _loader()
    lore = Lore.get(pk)
    if obj := obj.world.get_model(amodel, apk):
        if obj in lore.associations:
            lore.associations.remove(obj)
            lore.save()
    return get_template_attribute("shared/_lore.html", "lore_details")(user, lore)
