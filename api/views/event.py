"""
# Components API Documentation

## Components Endpoints
"""

import json
import os
import random

import requests
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from autonomous.model.automodel import AutoModel
from models.campaign import Campaign
from models.campaign.episode import Episode
from models.stories.event import Event
from models.stories.story import Story
from models.ttrpgobject.character import Character
from models.ttrpgobject.encounter import Encounter
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.vehicle import Vehicle
from models.world import World

from ._utilities import loader as _loader

event_endpoint = Blueprint("event", __name__)


###########################################################
##                    Event Routes                    ##
###########################################################
@event_endpoint.route("/", methods=("POST",))
@event_endpoint.route("/<string:pk>", methods=("POST",))
def index(pk=None):
    user, obj, request_data = _loader()
    event = Event.get(pk or request.json.get("eventpk"))
    return get_template_attribute("shared/_event.html", "event")(
        user,
        event,
    )


###########################################################
##                    Event CRUD Routes                  ##
###########################################################


@event_endpoint.route("/<string:pk>/update", methods=("POST",))
def edit_event(pk=None):
    user, obj, request_data = _loader()
    log(request.json)
    event = Event.get(pk)
    event.name = request.json.get("name", event.name)
    event.scope = request.json.get("scope", event.scope)
    event.impact = request.json.get("impact", event.impact)
    event.outcome = request.json.get("outcome", event.outcome)
    event.backstory = request.json.get("backstory", event.backstory)
    event.start_date = request.json.get("start_date", event.start_date)
    event.end_date = request.json.get("end_date", event.end_date)
    event.save()

    return get_template_attribute("manage/_event.html", "event")(
        user,
        event,
    )


@event_endpoint.route("/<string:pk>/delete", methods=("POST",))
def delete_event(pk=None):
    user, obj, request_data = _loader()
    log(request.json)
    event = Event.get(pk)
    world = event.world
    event.delete()
    return get_template_attribute("models/_world.html", "timeline")(
        user,
        world,
    )


###########################################################
##             Event Association Routes                  ##
###########################################################


@event_endpoint.route(
    "<string:pk>/associations/add/search",
    methods=("POST",),
)
def eventassociationsearch(pk):
    user, obj, request_data = _loader()
    event = Event.get(pk)
    query = request.json.get("query")
    results = event.world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [r for r in results if r not in event.associations]
    return get_template_attribute("manage/_event.html", "associations_dropdown")(
        user, event, results
    )


@event_endpoint.route(
    "<string:pk>/associations/add/<string:amodel>",
    methods=("POST",),
)
@event_endpoint.route(
    "<string:pk>/associations/add/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def eventassociationadd(pk, amodel, apk=None):
    user, obj, request_data = _loader()
    event = Event.get(pk)
    if apk:
        obj = event.world.get_model(amodel, apk)
    else:
        Model = event.world.get_model(amodel)
        obj = Model(world=event.world)
        obj.save()
    if obj not in event.associations:
        event.associations += [obj]
        event.save()
    return get_template_attribute("manage/_event.html", "events")(user, event)
