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
from models.stories.event import Event
from models.stories.story import Story
from models.ttrpgobject.character import Character
from models.ttrpgobject.encounter import Encounter
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.vehicle import Vehicle
from models.world import World

from ._utilities import loader as _loader

story_endpoint = Blueprint("story", __name__)


###########################################################
##                    Story Routes                    ##
###########################################################
@story_endpoint.route("/", methods=("POST",))
@story_endpoint.route("/<string:pk>", methods=("POST",))
def index(pk=None):
    user, obj, request_data = _loader()
    obj.world.save()
    story = Story.get(pk or request.json.get("storypk"))
    return get_template_attribute("models/_story.html", "index")(
        user,
        story,
    )


@story_endpoint.route("/manage", methods=("POST",))
@story_endpoint.route("/<string:pk>/manage", methods=("POST",))
def manage(pk=None):
    user, obj, request_data = _loader()
    obj.world.save()
    story = Story.get(pk or request.json.get("storypk"))
    return get_template_attribute("models/_story.html", "manage")(
        user,
        story,
    )


###########################################################
##                    Story CRUD Routes                  ##
###########################################################
@story_endpoint.route("/new", methods=("POST",))
def add_story():
    user, obj, request_data = _loader()
    story = Story(world=obj.world)
    if obj.model_name() != "World":
        story.associations += [obj]
    story.save()
    obj.world.stories += [story]
    obj.world.save()
    return f"""<script>
        window.location.replace('/story/{story.pk}/manage');
    </script>
"""


@story_endpoint.route("/<string:pk>/update", methods=("POST",))
def edit_story(pk):
    user, obj, request_data = _loader()
    log(request.json)
    story = Story.get(pk)
    story.name = request.json.get("name", story.name)
    story.scope = request.json.get("scope", story.scope)
    story.situation = request.json.get("situation", story.situation)
    story.current_status = request.json.get("current_status", story.current_status)
    story.backstory = request.json.get("backstory", story.backstory)
    story.rumors = request.json.get("rumors", story.rumors)
    story.information = request.json.get("information", story.information)
    story.tasks = request.json.get("tasks", story.tasks)
    story.save()
    if story not in obj.world.stories:
        obj.world.stories += [story]
    obj.world.save()
    return get_template_attribute("manage/_story.html", "manage")(
        user,
        story,
    )


@story_endpoint.route("/<string:pk>/merge", methods=("POST",))
def merge_story(pk):
    user, obj, request_data = _loader()
    story = Story.get(pk)

    if pk == request_data.get("mergepk"):
        return get_template_attribute("manage/_story.html", "manage")(
            user,
            story,
        )

    if mergestory := Story.get(request_data.get("mergepk")):
        story.name = request.json.get("name", story.name)
        story.scope = request.json.get("scope", story.scope)
        story.situation = request.json.get("situation", story.situation)
        story.current_status = (
            f"{story.current_status}" + f"<br> <br> {mergestory.current_status}"
        )
        story.backstory = f"{story.backstory}" + f"<br> <br> {mergestory.backstory}"
        story.rumors += mergestory.rumors
        story.information += mergestory.information
        story.tasks += mergestory.tasks
        for assoc in mergestory.associations:
            story.add_association(assoc)
        for event in mergestory.events:
            if story not in event.stories:
                event.stories += [story]
                event.save()
        if mergestory.bbeg and not story.bbeg:
            story.bbeg = mergestory.bbeg
        mergestory.delete()
        story.save()
    return get_template_attribute("manage/_story.html", "manage")(
        user,
        story,
    )


@story_endpoint.route("/<string:pk>/add/listitem/<string:attr>", methods=("POST",))
def addlistitem(pk, attr):
    user, obj, *_ = _loader()
    story = Story.get(pk)
    if isinstance(getattr(story, attr, None), list):
        item = getattr(story, attr)
        item += [""]
    return get_template_attribute("manage/_story.html", "manage")(user, story)


@story_endpoint.route("/<string:pk>/delete", methods=("POST",))
def remove_story(pk):
    user, obj, request_data = _loader()
    story = Story.get(pk)
    if story in obj.world.stories:
        obj.world.stories.remove(story)
        obj.world.save()
    story.delete()
    return get_template_attribute("manage/_story.html", "manage")(
        user,
        story,
    )


###########################################################
##             Story Association Routes                  ##
###########################################################


@story_endpoint.route(
    "<string:pk>/associations/add/search",
    methods=("POST",),
)
def storyassociationsearch(pk):
    user, obj, request_data = _loader()
    story = Story.get(pk)
    query = request.json.get("query")
    results = obj.world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [r for r in results if r not in story.associations]
    return get_template_attribute("manage/_story.html", "associations_dropdown")(
        user, story, results
    )


@story_endpoint.route(
    "<string:pk>/associations/add/<string:amodel>",
    methods=("POST",),
)
@story_endpoint.route(
    "<string:pk>/associations/add/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def storyassociationadd(pk, amodel, apk=None):
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


###########################################################
##              Associated Story Routes                  ##
###########################################################


@story_endpoint.route(
    "<string:pk>/story/add/search",
    methods=("POST",),
)
def associated_story_search(pk):
    user, obj, request_data = _loader()
    story = Story.get(pk)
    query = request.json.get("story_query")
    results = Story.search(name=query) if len(query) > 2 else []
    results = [r for r in results if r not in story.associated_stories and r != story]
    url = f"story/{pk}/add"
    return get_template_attribute("shared/_dropdown.html", "search_dropdown")(
        user, story, url, results
    )


@story_endpoint.route(
    "<string:pk>/add/story/<string:apk>",
    methods=("POST",),
)
def associated_story_add(pk, apk):
    user, obj, request_data = _loader()
    story = Story.get(pk)
    obj = Story.get(apk)
    story.add_story(obj)
    return get_template_attribute("manage/_story.html", "manage")(user, story)


###########################################################
##             Story Event Routes                        ##
###########################################################
@story_endpoint.route(
    "<string:pk>/event/add",
    methods=("POST",),
)
@story_endpoint.route(
    "<string:pk>/event/add/<string:eventpk>",
    methods=("POST",),
)
def storyeventadd(pk, eventpk=None):
    user, obj, request_data = _loader()
    story = Story.get(pk)
    if eventpk:
        event = Event.get(eventpk)
    else:
        event = Event(world=story.world)
    if story not in event.stories:
        event.stories += [story]
    event.save()
    log(event.stories)
    return get_template_attribute("manage/_story.html", "manage")(user, story)


@story_endpoint.route(
    "<string:pk>/event/add/search",
    methods=("POST",),
)
def storyeventaddsearch(pk):
    user, obj, request_data = _loader()
    story = Story.get(pk)
    query = request.json.get("query")
    results = (
        obj.world.search_autocomplete(query=query, model=Event)
        if len(query) > 2
        else []
    )
    return get_template_attribute("manage/_story.html", "events_dropdown")(
        user, story, results
    )


###########################################################
##             Story BBEG Routes                         ##
###########################################################
@story_endpoint.route(
    "<string:pk>/bbeg/add/search",
    methods=("POST",),
)
def storybbegsearch(pk):
    user, obj, request_data = _loader()
    story = Story.get(pk)
    query = request.json.get("query")
    results = obj.world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [
        r for r in results if isinstance(r, (Character, Faction)) and r != story.bbeg
    ]
    return get_template_attribute("manage/_story.html", "bbeg_dropdown")(
        user, obj.world, story, results
    )


@story_endpoint.route(
    "<string:pk>/bbeg/add/<string:cpk>",
    methods=("POST",),
)
def storybbegadd(pk, cpk):
    user, obj, request_data = _loader()
    story = Story.get(pk)
    obj = Character.get(cpk) or Faction.get(cpk)
    story.bbeg = obj
    story.save()
    return get_template_attribute("manage/_story.html", "manage")(user, story)
