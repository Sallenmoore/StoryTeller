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
from models.stories.story import Story
from models.ttrpgobject.character import Character
from models.ttrpgobject.encounter import Encounter
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.vehicle import Vehicle
from models.world import World

from ._utilities import loader as _loader

stories_endpoint = Blueprint("stories", __name__)


###########################################################
##                    Story Routes                    ##
###########################################################
@stories_endpoint.route("/", methods=("POST",))
@stories_endpoint.route("/<string:pk>", methods=("POST",))
def index(pk=None):
    user, world, *_ = _loader()
    world.save()
    story = Story.get(pk or request.json.get("storypk"))
    return get_template_attribute("manage/_stories.html", "stories")(
        user,
        world,
        story=story,
    )


###########################################################
##                    Story CRUD Routes                  ##
###########################################################
@stories_endpoint.route("/new", methods=("POST",))
def add_story():
    user, world, *_ = _loader()
    story = Story()
    story.save()
    world.stories += [story]
    world.save()
    return get_template_attribute("manage/_stories.html", "stories")(
        user,
        world,
        story=story,
    )


@stories_endpoint.route("/<string:pk>/update", methods=("POST",))
def edit_story(pk=None):
    user, world, *_ = _loader()
    log(request.json)
    story = Story.get(pk)
    story.name = request.json.get("name", story.name)
    story.scope = request.json.get("scope", story.scope)
    story.situation = request.json.get("situation", story.situation)
    story.current_status = request.json.get("current_status", story.current_status)
    story.backstory = request.json.get("backstory", story.backstory)
    story.rumors = request.json.get("rumors", story.rumors)
    story.information = request.json.get("information", story.information)
    story.tasks = request.json.get("information", story.tasks)
    story.save()
    if story not in world.stories:
        world.stories += [story]
    world.save()
    return get_template_attribute("manage/_stories.html", "stories")(
        user,
        world,
        story=story,
    )


@stories_endpoint.route("/<string:pk>/add/listitem/<string:attr>", methods=("POST",))
def addlistitem(pk, attr):
    user, obj, *_ = _loader()
    story = Story.get(pk)
    if isinstance(getattr(story, attr, None), list):
        item = getattr(story, attr)
        if item is not None:
            item += [""]
    return get_template_attribute("manage/_stories.html", "story_details")(
        user, obj, story
    )


@stories_endpoint.route("/<string:pk>/delete", methods=("POST",))
def remove_story(pk):
    user, world, *_ = _loader()
    story = Story.get(pk)
    if story in world.stories:
        world.stories.remove(story)
        world.save()
    story.delete()
    return get_template_attribute("manage/_stories.html", "stories")(
        user,
        world,
        story=story,
    )


###########################################################
##             Story Association Routes                  ##
###########################################################


@stories_endpoint.route(
    "<string:pk>/associations/add/search",
    methods=("POST",),
)
def storyassociationsearch(pk):
    user, world, *_ = _loader()
    story = Story.get(pk)
    query = request.json.get("query")
    results = world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [r for r in results if r not in story.associations]
    return get_template_attribute("manage/_stories.html", "associations_dropdown")(
        user, world, story, results
    )


@stories_endpoint.route(
    "<string:pk>/encounters/add/search",
    methods=("POST",),
)
def storyencounterssearch(pk):
    user, world, *_ = _loader()
    story = Story.get(pk)
    query = request.json.get("query")
    results = world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [
        r for r in results if isinstance(r, Encounter) and r not in story.encounters
    ]
    return get_template_attribute("manage/_stories.html", "encounters_dropdown")(
        user, world, story, results
    )


@stories_endpoint.route(
    "<string:pk>/bbeg/add/search",
    methods=("POST",),
)
def storybbegsearch(pk):
    user, world, *_ = _loader()
    story = Story.get(pk)
    query = request.json.get("query")
    results = world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [r for r in results if isinstance(r, Character) and r != story.bbeg]
    return get_template_attribute("manage/_stories.html", "bbeg_dropdown")(
        user, world, story, results
    )


@stories_endpoint.route(
    "<string:pk>/associations/add/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def storyassociationadd(pk, amodel, apk):
    user, world, *_ = _loader()
    story = Story.get(pk)
    obj = world.get_model(amodel, apk)
    if obj not in story.associations:
        story.associations += [obj]
        story.save()
    return get_template_attribute("manage/_stories.html", "stories")(user, world, story)


@stories_endpoint.route(
    "<string:pk>/encounters/add/<string:epk>",
    methods=("POST",),
)
def storyencountersadd(pk, epk):
    user, world, *_ = _loader()
    story = Story.get(pk)
    obj = Encounter.get(epk)
    if obj not in story.encounters:
        story.encounters += [obj]
        story.save()
    return get_template_attribute("manage/_stories.html", "stories")(user, world, story)


@stories_endpoint.route(
    "<string:pk>/bbeg/add/<string:cpk>",
    methods=("POST",),
)
def storybbegadd(pk, cpk):
    user, world, *_ = _loader()
    story = Story.get(pk)
    obj = Character.get(cpk)
    story.bbeg = obj
    story.save()
    return get_template_attribute("manage/_stories.html", "stories")(user, world, story)
