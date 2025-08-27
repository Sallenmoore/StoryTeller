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


def get_template(obj, macro, module=None):
    module = module or f"models/_{obj.__class__.__name__.lower()}.html"
    # log(f"Module: {module}, Macro: {macro}")
    try:
        template = get_template_attribute(module, macro)
    except (TemplateNotFound, AttributeError) as e:
        # log(e)
        module = f"shared/_{macro}.html"
        template = get_template_attribute(module, macro)
    return template


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
    user, *_ = _loader()
    return get_template_attribute("home.html", "home")(user)


@index_endpoint.route(
    "/build",
    methods=("POST",),
)
def build():
    user, *_ = _loader()
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
    user, *_ = _loader()
    return get_template_attribute("home.html", "worldbuild")(user=user)


###########################################################
##                    World Routes                       ##
###########################################################
# @index_endpoint.route(
#     "/world/<string:pk>",
#     methods=(
#         "GET",
#         "POST",
#     ),
# )
# def world(pk):
#     user, *_ = _loader()
#     world = World.get(pk)
#     return get_template_attribute("shared/_gm.html", "home")(user, world)


@index_endpoint.route(
    "/world/<string:pk>/gm",
    methods=(
        "GET",
        "POST",
    ),
)
def world_gm(pk):
    user, world, *_ = _loader()
    world.save()
    return get_template_attribute("manage/_gm.html", "gm")(user, world)


@index_endpoint.route(
    "/world/<string:pk>/manage_screens",
    methods=(
        "GET",
        "POST",
    ),
)
def world(pk):
    user, *_ = _loader()
    world = World.get(pk)
    return get_template_attribute("manage/_gmscreen.html", "manage_gmscreens")(
        user, world
    )


@index_endpoint.route(
    "/world/<string:pk>/calendar/update",
    methods=(
        "GET",
        "POST",
    ),
)
def worldcalendar(pk):
    user, *_ = _loader()
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
    log(world.calendar.months, world.calendar.days)
    return get_template_attribute("models/_world.html", "manage_details")(user, world)


@index_endpoint.route(
    "/world/<string:pk>/stories/manage",
    methods=("GET", "POST"),
)
@index_endpoint.route(
    "/world/<string:pk>/stories/<string:storypk>",
    methods=("GET", "POST"),
)
def storymanage(pk, storypk=None):
    user, obj, world, *_ = _loader()
    if user.world_user(world):
        results = requests.post(
            f"http://api:{os.environ.get('COMM_PORT')}/stories/{storypk if storypk else ''}",
            json={"user": str(user.pk), "model": obj.model_name(), "pk": str(obj.pk)},
        )
        # log(results.text)
        return results.text
    return "Unauthorized"


@index_endpoint.route(
    "/world/<string:pk>/campaigns/manage",
    methods=("GET", "POST"),
)
@index_endpoint.route(
    "/world/<string:pk>/campaigns/manage/<string:campaignpk>",
    methods=("GET", "POST"),
)
def campaignmanage(pk, campaignpk=None):
    user, obj, world, *_ = _loader()
    if user.world_user(world):
        results = requests.post(
            f"http://api:{os.environ.get('COMM_PORT')}/campaign/{campaignpk if campaignpk else ''}",
            json={"user": str(user.pk), "model": obj.model_name(), "pk": str(obj.pk)},
        )
        # log(results.text)
        return results.text
    return "Unauthorized"


@index_endpoint.route("/world/<string:pk>/system/update", methods=("POST",))
def worldsystem(pk):
    user, obj, world, *_ = _loader()
    system = world.SYSTEMS.get(request.json.get("system"), None)
    log()
    world.set_system(system)
    return get_template_attribute("shared/_details.html", "details")(user, world)


@index_endpoint.route("/world/<string:pk>/delete", methods=("POST",))
def worlddelete(pk):
    user, *_ = _loader()
    if world := World.get(pk):
        world.delete()
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
def model(model, pk, page):
    user, obj, *_ = _loader(model=model, pk=pk)
    return get_template(obj, page)(user, obj)


@index_endpoint.route(
    "/card/<string:model>/<string:pk>",
    methods=(
        "GET",
        "POST",
    ),
)
def card(model, pk):
    user, obj, *_ = _loader(model=model, pk=pk)
    return get_template_attribute("shared/_display.html", "card")(user, obj)


###########################################################
##                    Model Routes                       ##
###########################################################


@index_endpoint.route(
    "/campaigns/<string:campaignpk>",
    methods=(
        "GET",
        "POST",
    ),
)
@index_endpoint.route(
    "/<string:model>/<string:pk>/campaigns",
    methods=(
        "GET",
        "POST",
    ),
)
def campaigns(model, pk, campaignpk=None):
    user, obj, *_ = _loader(model=model, pk=pk)
    campaign = Campaign.get(campaignpk or request.args.get("campaignpk"))
    return get_template_attribute("shared/_campaigns.html", "campaigns")(
        user, obj, campaign
    )


@index_endpoint.route(
    "/<string:model>/<string:pk>/episodes/<string:episodepk>",
    methods=(
        "GET",
        "POST",
    ),
)
def getepisode(model, pk, episodepk):
    user, obj, *_ = _loader(model=model, pk=pk)
    episode = Episode.get(episodepk)
    log(episode)
    return get_template_attribute("shared/_episode.html", "episode")(
        user, obj, obj.campaigns, episode.campaign, episode
    )


@index_endpoint.route(
    "/<string:model>/<string:pk>/stories/<string:storypk>",
    methods=(
        "GET",
        "POST",
    ),
)
@index_endpoint.route(
    "/<string:model>/<string:pk>/stories",
    methods=(
        "GET",
        "POST",
    ),
)
def stories(
    model,
    pk,
    storypk=None,
):
    user, obj, *_ = _loader(model=model, pk=pk)
    story = None
    if storypk:
        story = Story.get(storypk)
    elif request.method == "POST":
        story = Story.get(request.json.get("storypk"))
    return get_template_attribute("shared/_stories.html", "stories")(user, obj, story)


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
    user, obj, *_ = _loader(model=model, pk=pk)
    log(modelstr)
    associations = [
        o
        for o in obj.associations
        if not modelstr or modelstr.lower() == o.model_name().lower()
    ]
    log(associations)
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

    return get_template_attribute("shared/_associations.html", "associations")(
        user, obj, associations
    )


###########################################################
##                    Timeline Routes                 ##
###########################################################
@index_endpoint.route("/<string:model>/<string:pk>/timeline", methods=("GET", "POST"))
def timeline(model, pk):
    user, obj, *_ = _loader(model=model, pk=pk)
    associations = (
        obj.associations if obj.model_name() == "World" else [obj, *obj.associations]
    )
    events = []
    for a in associations:
        if a.start_date and a.start_date.year > 0:
            if a.model_name() in ["Character", "Creature"]:
                start = "Born"
            elif a.model_name() in ["Item", "Vehicle"]:
                start = "Created"
            elif a.model_name() in ["Location", "City"]:
                start = "Built"
            elif a.model_name() in ["Encounter"]:
                start = "Started"
            else:
                start = "Founded"
            if a.model_name() not in ["Character", "Creature"] or getattr(
                a, "is_player", None
            ):
                event = {
                    "date": a.start_date,
                    "name": a.name,
                    "event": start,
                    "description": a.backstory_summary,
                    "icon": a.get_icon(),
                    "image": a.image.url() if a.image else None,
                    "obj": a,
                }
                events += [event]
        if a.end_date and a.end_date.year > 0:
            if a.model_name() in ["Character", "Creature"]:
                end = "Died"
            elif a.model_name() in ["Item", "Vehicle"]:
                end = "Lost"
            elif a.model_name() in ["Location"]:
                end = "Destroyed"
            elif a.model_name() in ["Encounter"]:
                end = "Ended"
            elif a.model_name() in ["Faction"]:
                end = "Disbanded"
            else:
                end = "Abandoned"
            if a.model_name() not in ["Character", "Creature"] or getattr(
                a, "is_player", None
            ):
                event = {
                    "date": a.end_date,
                    "name": a.name,
                    "event": end,
                    "description": a.backstory_summary,
                    "icon": a.get_icon(),
                    "image": a.image.url() if a.image else None,
                    "obj": a,
                }
                events += [event]
    log(events)
    events.sort(key=lambda x: x["date"], reverse=True)
    return get_template_attribute("shared/_timeline.html", "timeline")(
        user, obj, events
    )
