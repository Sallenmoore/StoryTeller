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
from models.stories.story import Story
from models.ttrpgobject.character import Character
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.vehicle import Vehicle
from models.world import World

from ._utilities import loader as _loader

episode_endpoint = Blueprint("episode", __name__)


###########################################################
##                    episode CRUD Routes                  ##
###########################################################


@episode_endpoint.route("/update", methods=("POST",))
@episode_endpoint.route("/<string:pk>/update", methods=("POST",))
def edit_episode(pk=None):
    user, obj, request_data = _loader()
    pk = pk or request.json.get("episodepk")
    if episode := Episode.get(pk):
        episode.name = request.json.get("name", episode.name)
        episode.episode_num = request.json.get("episode_num", episode.episode_num)
        start_date = request.json.get("start_date", episode.start_date)
        if (
            start_date
            and start_date["day"]
            and start_date["month"]
            and start_date["year"]
        ):
            episode.start_date = start_date
        end_date = request.json.get("end_date", episode.end_date)
        if end_date and end_date["day"] and end_date["month"] and end_date["year"]:
            episode.end_date = end_date
        episode.description = request.json.get("description", episode.description)
        episode.episode_report = request.json.get(
            "episode_report", episode.episode_report
        )
        episode.loot = request.json.get("loot", episode.loot)
        episode.hooks = request.json.get("hooks", episode.hooks)
        episode.save()
    return get_template_attribute("manage/_episode.html", "manage")(
        user,
        episode,
    )


@episode_endpoint.route("/<string:episodepk>/delete", methods=("POST",))
def delete(episodepk):
    user, obj, request_data = _loader()
    episode = Episode.get(episodepk)
    campaign = episode.campaign
    campaign.delete_episode(episodepk)
    # log(module, macro)
    return get_template_attribute("models/_campaign.html", "index")(
        user,
        campaign,
    )


###########################################################
##             episode Story Routes                  ##
###########################################################
# /api/{{episode.path}}/stories/{{story.pk}}/delete


@episode_endpoint.route("/<string:episodepk>/stories/add", methods=("POST",))
def addstory(episodepk):
    user, obj, request_data = _loader()
    episode = Episode.get(episodepk)
    story = Story.get(request_data.get("storypk"))
    if story not in episode.stories:
        episode.stories += [story]
    episode.save()
    return get_template_attribute("manage/_episode.html", "manage")(
        user,
        episode,
    )


@episode_endpoint.route(
    "/<string:episodepk>/stories/<string:storypk>/delete", methods=("POST",)
)
def removestory(episodepk, storypk):
    user, obj, request_data = _loader()
    episode = Episode.get(episodepk)
    story = Story.get(storypk)
    if story in episode.stories:
        episode.stories.remove(story)
        episode.save()
    # log(module, macro)
    return get_template_attribute("manage/_episode.html", "manage")(
        user,
        episode,
    )


###########################################################
##             episode Association Routes                  ##
###########################################################


@episode_endpoint.route(
    "<string:pk>/associations/add/search",
    methods=("POST",),
)
def episodeassociationsearch(pk):
    user, obj, request_data = _loader()
    episode = Episode.get(pk)
    query = request.json.get("query")
    results = episode.world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [r for r in results if r not in episode.associations]
    return get_template_attribute("shared/_dropdown.html", "search_dropdown")(
        user, episode, f"{episode.path}/associations/add", objs=results
    )


@episode_endpoint.route("/<string:pk>/associations", methods=("POST",))
def episodeassociationslist(pk):
    user, obj, request_data = _loader()
    episode = Episode.get(pk)
    return get_template_attribute("manage/_episode.html", "associations")(
        user, obj, episode
    )


@episode_endpoint.route(
    "<string:pk>/associations/add/<string:amodel>/<string:apk>",
    methods=("POST",),
)
@episode_endpoint.route(
    "<string:pk>/associations/add/<string:amodel>",
    methods=("POST",),
)
def episodeassociationentry(pk, amodel, apk=None):
    user, obj, request_data = _loader()
    episode = Episode.get(pk)
    if amodel == "campaignassociations":
        for a in episode.campaign.associations:
            episode.add_association(a)
    elif amodel == "episodeassociations":
        if pep := episode.previous_episode:
            for a in pep.associations:
                episode.add_association(a)
        else:
            log("no previous episodes")
    elif amodel == "players":
        players = (
            episode.previous_episode.players
            if episode.previous_episode
            else episode.campaign.players
        )
        for p in players:
            episode.add_association(p)
    elif apk:
        obj = obj.world.get_model(amodel, apk)
        # log(obj)
        episode.add_association(obj)
        if request.json.get("subobjects"):
            for sub in obj.children:
                episode.add_association(sub)
    else:
        new_ass = obj.world.get_model(amodel)(world=obj.world)
        new_ass.save()
        episode.add_association(new_ass)
    return get_template_attribute("manage/_episode.html", "manage")(user, episode)


@episode_endpoint.route(
    "/<string:pk>/association/<string:amodel>/<string:apk>/delete",
    methods=("POST",),
)
def episodeassociationentrydelete(pk, amodel, apk):
    user, obj, request_data = _loader()
    episode = Episode.get(pk)
    if a := obj.world.get_model(amodel, apk):
        episode = episode.remove_association(a)
        a.save()
    return "<p>success</p>"


###########################################################
##             Episode Event Routes                      ##
###########################################################


@episode_endpoint.route(
    "/<string:pk>/event/generate",
    methods=("POST",),
)
def episodegenerateevent(pk):
    user, obj, request_data = _loader()
    episode = Episode.get(pk)
    Event.create_event_from_episode(episode)
    return get_template_attribute("manage/_episode.html", "manage")(
        user,
        episode,
    )


@episode_endpoint.route(
    "/<string:pk>/add/event/<string:eventpk>",
    methods=("POST",),
)
def episodeeventadd(pk, eventpk):
    user, obj, request_data = _loader()
    episode = Episode.get(pk)
    event = Event.get(eventpk)
    episode.add_event(event)
    log(len(episode.events))
    return get_template_attribute("manage/_episode.html", "manage")(
        user,
        episode,
    )


@episode_endpoint.route(
    "<string:pk>/events/add/search",
    methods=("POST",),
)
def episodeeventsearch(pk):
    user, obj, request_data = _loader()
    episode = Episode.get(pk)
    query = request.json.get("event_query")
    log(query)
    results = Event.search(name=query, world=episode.world) if len(query) > 2 else []
    log(results)
    results = [r for r in results if r not in episode.events]
    log(results)
    return get_template_attribute("shared/_dropdown.html", "search_dropdown")(
        user, episode, f"{episode.path}/add", objs=results
    )


###########################################################
##             episode Graphic Routes                    ##
###########################################################
@episode_endpoint.route(
    "/<string:pk>/graphic/generate",
    methods=("POST",),
)
def episodegenerategraphic(pk):
    user, obj, request_data = _loader()
    episode = Episode.get(pk)
    return requests.post(
        f"http://{os.environ.get('TASKS_SERVICE_NAME')}:{os.environ.get('COMM_PORT')}/generate/{episode.path}/graphic"
    ).text
