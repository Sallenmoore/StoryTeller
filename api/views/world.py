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
from models.stories.lore import Lore
from models.stories.quest import Quest  # for the importer
from models.stories.story import Story
from models.ttrpgobject.character import Character
from models.world import World

from ._utilities import loader as _loader

world_endpoint = Blueprint("world", __name__)


@world_endpoint.route(
    "/build",
    methods=("POST",),
)
def build():
    user, obj, request_data = _loader()
    World.build(
        system=request_data.get("system"),
        user=user,
        name=request_data.get("name"),
        tone=request_data.get("tone") or random.choice(list(World.TONES.keys())),
        backstory=request_data.get("backstory"),
    )

    return get_template_attribute("home.html", "home")(user)


@world_endpoint.route("/build/form", methods=("POST",))
def buildform():
    user, obj, request_data = _loader()
    return get_template_attribute("home.html", "worldbuild")(user=user)


@world_endpoint.route("/campaign/new", methods=("POST",))
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


@world_endpoint.route("/lore/new", methods=("POST",))
def lore_new():
    user, obj, request_data = _loader()
    lore = Lore(name="New Lore", world=obj)
    lore.save()
    if story := Story.get(request_data.get("story_pk")):
        lore.story = story
        lore.associations = [a for a in story.associations]
        lore.backstory = story.summary
    lore.start_date = {
        "day": request_data.get("start_day"),
        "month": request_data.get("start_month"),
        "year": request_data.get("start_year"),
    }
    lore.save()
    obj.lore_entries += [lore]
    obj.save()
    return get_template_attribute("models/_world.html", "lore")(
        user,
        obj,
    )


@world_endpoint.route("/lore/<string:lore_pk>/edit", methods=("POST",))
def lore_edit(lore_pk):
    user, obj, request_data = _loader()
    lore = Lore.get(lore_pk)
    if name := request_data.get("name"):
        lore.name = name
    if scope := request_data.get("scope"):
        lore.scope = scope.title()
    if story := Story.get(request_data.get("storypk")):
        lore.story = story
        lore.associations += [a for a in story.associations]
        lore.backstory = story.summary
    lore.save()
    return get_template_attribute("models/_world.html", "lore_details")(user, lore)


@world_endpoint.route("/lore/<string:lore_pk>/delete", methods=("POST",))
def lore_delete(lore_pk):
    user, obj, request_data = _loader()
    if lore := Lore.get(lore_pk):
        lore.story = None
        lore.delete()
    return get_template_attribute("models/_world.html", "lore")(user, obj)


###########################################################
##             World Lore Association Routes             ##
###########################################################


@world_endpoint.route(
    "/lore/<string:pk>/party/add/search",
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
    return get_template_attribute("models/_world.html", "lore_party_dropdown")(
        user, lore, results
    )


@world_endpoint.route(
    "/lore/<string:pk>/party/add/<string:apk>",
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
    return get_template_attribute("models/_world.html", "lore_details")(user, lore)


@world_endpoint.route(
    "/lore/<string:pk>/party/remove/<string:apk>",
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
    return get_template_attribute("models/_world.html", "lore_details")(user, lore)


@world_endpoint.route(
    "/lore/<string:pk>/association/add/search",
    methods=("POST",),
)
def loreassociationsearch(pk):
    user, obj, request_data = _loader()
    lore = Lore.get(pk)
    query = request.json.get("query")
    results = obj.world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [a for a in results if a not in lore.associations]
    return get_template_attribute("models/_world.html", "lore_association_dropdown")(
        user, lore, results
    )


@world_endpoint.route(
    "/lore/<string:pk>/association/add/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def loreassociationadd(pk, amodel, apk=None):
    user, obj, request_data = _loader()
    lore = Lore.get(pk)
    if obj := obj.world.get_model(amodel, apk):
        if obj not in lore.associations:
            lore.associations += [obj]
            lore.save()
    return get_template_attribute("models/_world.html", "lore_details")(user, lore)


@world_endpoint.route(
    "/lore/<string:pk>/association/remove/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def loreassociationremove(pk, amodel, apk=None):
    user, obj, request_data = _loader()
    lore = Lore.get(pk)
    if obj := obj.world.get_model(amodel, apk):
        if obj in lore.associations:
            lore.associations.remove(obj)
            lore.save()
    return get_template_attribute("models/_world.html", "lore_details")(user, lore)
