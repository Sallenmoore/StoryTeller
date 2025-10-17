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

world_endpoint = Blueprint("world", __name__)


@world_endpoint.route("/new", methods=("POST",))
def campaignnew():
    user, obj, request_data = _loader()
    campaign = Campaign(world=obj.world, name="New Campaign")
    campaign.save()
    obj.world.campaigns.append(campaign)
    obj.world.save()
    return get_template_attribute("models/_world.html", "campaigns")(
        user,
        obj,
    )


@world_endpoint.route(
    "/<string:pk>/calendar/update",
    methods=(
        "GET",
        "POST",
    ),
)
def worldcalendar(pk):
    user, obj, request_data = _loader()
    world = World.get(pk)
    if not world.calendar:
        world.pre_save_current_date()
        world.save()
    world.calendar.age = request.json.get("age")
    if request.json.get("month_names") == "12" and not request.json.get(
        "month_names_list"
    ):
        world.calendar.months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
    else:
        world.calendar.months = request.json.get("month_names_list")
    if request.json.get("day_names") == "7" and not request.json.get("day_names_list"):
        world.calendar.days = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
    else:
        world.calendar.days = request.json.get("day_names_list")
    world.calendar.days_per_year = request.json.get("num_days_per_year")
    world.calendar.save()
    # log(world.calendar.months, world.calendar.days)
    return get_template_attribute("models/_world.html", "manage_details")(user, world)


@world_endpoint.route("/<string:pk>/system/update", methods=("POST",))
def worldsystem(pk):
    user, obj, request_data = _loader()
    world = World.get(pk)
    system = world.SYSTEMS.get(request.json.get("system"), None)
    world.set_system(system)
    return get_template_attribute("shared/_details.html", "details")(user, world)


@world_endpoint.route("/<string:pk>/delete", methods=("POST",))
def worlddelete(pk):
    user, obj, request_data = _loader()
    if world := World.get(pk):
        world.delete()
    return get_template_attribute("home.html", "home")(user)


##################### Lore Endpoints #####################


@world_endpoint.route("/<string:pk>/lore/new", methods=("POST",))
def lore_new(pk):
    user, obj, request_data = _loader()
    lore = Story(name="New Story", world=obj)
    lore.save()
    obj.stories.append(lore)
    obj.save()
    return get_template_attribute("models/_world.html", "stories")(
        user,
        obj,
    )


###########################################################
##             World Lore Association Routes                  ##
###########################################################


@world_endpoint.route(
    "<string:pk>/lore/party/add/search",
    methods=("POST",),
)
def loreassociationsearch(pk):
    user, obj, request_data = _loader()
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
    return get_template_attribute("models/_world.html", "lore_association_dropdown")(
        user, obj, results
    )


@world_endpoint.route(
    "<string:pk>/associations/add/<string:amodel>",
    methods=("POST",),
)
@world_endpoint.route(
    "<string:pk>/associations/add/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def loreassociationadd(pk, amodel, apk=None):
    user, obj, request_data = _loader()
    story = Story.get(pk)
    if apk:
        obj = obj.world.get_model(amodel, apk)
    else:
        Model = obj.world.get_model(amodel)
        obj = Model(world=obj.world)
        obj.save()
    if obj not in story.associations:
        story.associations += [obj]
        story.save()
    return get_template_attribute("manage/_story.html", "manage")(user, story)


@world_endpoint.route("/<string:pk>/lore/<string:lore_pk>/delete", methods=("POST",))
def lore_delete(pk, lore_pk):
    user, obj, request_data = _loader()
    if lore := Story.get(lore_pk):
        lore.delete()
    if lore in obj.stories:
        obj.stories.remove(lore)
        obj.save()
    return get_template_attribute("models/_world.html", "stories")(user, obj)
