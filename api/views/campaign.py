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
from models.ttrpgobject.character import Character
from models.ttrpgobject.encounter import Encounter
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.vehicle import Vehicle
from models.world import World

from ._utilities import loader as _loader

campaign_endpoint = Blueprint("campaign", __name__)
module = "manage/_campaign.html"
macro = "campaigns"


###########################################################
##                    Campaign Routes                    ##
###########################################################
@campaign_endpoint.route(
    "/",
    methods=(
        "GET",
        "POST",
    ),
)
@campaign_endpoint.route(
    "/<string:pk>",
    methods=(
        "GET",
        "POST",
    ),
)
def index(pk=None):
    user, obj, request_data = _loader()
    campaign = Campaign.get(pk or request_data.get("campaignpk"))
    return get_template_attribute("models/_campaign.html", "index")(
        user,
        campaign,
    )


@campaign_endpoint.route("/manage", methods=("POST",))
@campaign_endpoint.route("/<string:pk>/manage", methods=("POST",))
def manage(pk=None):
    user, obj, request_data = _loader()
    pk = pk or request_data.get("campaignpk")
    campaign = Campaign.get(pk or request.json.get("campaignpk"))

    return get_template_attribute("models/_campaign.html", "manage")(user, campaign)


@campaign_endpoint.route("/<string:pk>/delete", methods=("POST",))
def campaigndelete(pk):
    user, obj, request_data = _loader()
    if campaign := Campaign.get(pk):
        obj.world.campaigns.remove(
            campaign
        ) if campaign in obj.world.campaigns else None
        obj.world.save()
        campaign.delete()
    return get_template_attribute(module, macro)(
        user,
        obj,
        campaign_list=obj.world.campaigns,
        campaign=obj.world.current_campaign,
    )


@campaign_endpoint.route("/<string:pk>/update", methods=("POST",))
def campaignupdate(pk):
    user, obj, request_data = _loader()
    if campaign := Campaign.get(pk):
        campaign.name = request.json.get("name") or campaign.name
        campaign.description = request.json.get("description") or campaign.description
        campaign.save()
    return get_template_attribute(module, macro)(
        user, obj, campaign_list=obj.world.campaigns, campaign=campaign
    )


@campaign_endpoint.route("/<string:pk>/add/party", methods=("POST",))
def addparty(pk):
    user, obj, request_data = _loader()
    campaign = Campaign.get(pk)
    campaign.party = Faction.get(request.json.get("party"))
    campaign.save()
    return get_template_attribute("manage/_campaign.html", "campaign_details")(
        user, obj, campaign=campaign
    )


@campaign_endpoint.route("/<string:pk>/removeplayer", methods=("POST",))
def removeparty(pk, partypk):
    user, obj, request_data = _loader()
    campaign = Campaign.get(pk)
    campaign.party = None
    campaign.save()
    return get_template_attribute(module, macro)(
        user, obj, campaign_list=obj.world.campaigns, campaign=campaign
    )


###########################################################
##                    Episode Routes                    ##
###########################################################


@campaign_endpoint.route("/<string:pk>/episode/new", methods=("POST",))
def episodenew(pk):
    user, obj, request_data = _loader()
    campaign = Campaign.get(pk)
    episode = campaign.add_episode()
    campaign.current_episode = episode
    return get_template_attribute("manage/_campaign.html", "manage")(
        user,
        obj,
        campaign_list=obj.world.campaigns,
        campaign=campaign,
        episode=campaign.current_episode,
    )


@campaign_endpoint.route("/episode/<string:episodepk>/delete", methods=("POST",))
def episodedelete(episodepk):
    user, obj, request_data = _loader()
    episode = Episode.get(episodepk)
    campaign = episode.campaign
    campaign.delete_episode(episodepk)
    # log(module, macro)
    return get_template_attribute(module, macro)(
        user,
        obj,
        campaign_list=obj.world.campaigns,
        campaign=campaign,
        episode=campaign.episodes[-1] if campaign.episodes else None,
    )


@campaign_endpoint.route("/episode/<string:pk>/report", methods=("POST",))
def episodereportpanel(pk):
    user, obj, request_data = _loader()
    episode = Episode.get(pk)
    return get_template_attribute("manage/_campaign.html", "episode_report")(
        user, obj, episode
    )


@campaign_endpoint.route("/episode/<string:pk>/associations", methods=("POST",))
def episodeassociationslist(pk):
    user, obj, request_data = _loader()
    episode = Episode.get(pk)
    return get_template_attribute("manage/_campaign.html", "episode_associations")(
        user, obj, episode
    )


@campaign_endpoint.route(
    "episode/<string:pk>/associations/add/<string:amodel>/<string:apk>",
    methods=("POST",),
)
@campaign_endpoint.route(
    "episode/<string:pk>/associations/add/<string:amodel>",
    methods=("POST",),
)
def epsiodeassociationentry(pk, amodel, apk=None):
    user, obj, request_data = _loader()
    episode = Episode.get(pk)
    if amodel == "campaignassociations":
        for a in episode.campaign.associations:
            episode.add_association(a)
    elif amodel == "episodeassociations":
        if len(episode.campaign.episodes) > 1:
            for ep in episode.campaign.episodes:
                if ep.episode_num == episode.episode_num - 1:
                    for a in ep.associations:
                        episode.add_association(a)
        else:
            log("no previous episodes")
    elif amodel == "players":
        for p in episode.campaign.players:
            episode.add_association(p)
    elif apk:
        obj = obj.world.get_model(amodel, apk)
        # log(obj)
        episode.add_association(obj)
        if request.json.get("subobjects"):
            for sub in obj.children:
                episode.add_association(sub)
    else:
        new_ass = obj.world.get_model(amodel)(parent=obj, world=obj.world)
        new_ass.save()
        episode.add_association(new_ass)
    return get_template_attribute("manage/_campaign.html", "associations")(
        user, obj, episode
    )


@campaign_endpoint.route(
    "episode/<string:pk>/associations/add/search",
    methods=("POST",),
)
def episodeassociationsearch(pk):
    user, obj, request_data = _loader()
    episode = Episode.get(pk)
    query = request.json.get("query")
    results = obj.world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [r for r in results if r not in episode.associations]
    # log(macro, query, [r.name for r in results])
    return get_template_attribute("manage/_campaign.html", "association_dropdown")(
        user, obj, episode, results
    )


@campaign_endpoint.route(
    "/episode/<string:pk>/association/<string:amodel>/<string:apk>/delete",
    methods=("POST",),
)
def episodeassociationentrydelete(pk, amodel, apk):
    user, obj, request_data = _loader()
    episode = Episode.get(pk)
    if a := obj.world.get_model(amodel, apk):
        episode = episode.remove_association(a)
        a.save()
    return "<p>success</p>"
