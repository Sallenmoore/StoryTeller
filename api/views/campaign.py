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
@campaign_endpoint.route("/", methods=("POST",))
@campaign_endpoint.route("/<string:pk>", methods=("POST",))
@campaign_endpoint.route("/<string:pk>/episode/<string:episodepk>", methods=("POST",))
def index(pk=None, episodepk=None):
    user, obj, world, *_ = _loader()
    campaign = None
    episode = None
    if episode := Episode.get(episodepk or request.json.get("episodepk")):
        campaign = episode.campaign
        campaign.current_episode = episode
        campaign.save()
    elif campaign := Campaign.get(pk or request.json.get("campaignpk")):
        episode = campaign.current_episode
    return get_template_attribute("manage/_campaign.html", "campaigns")(
        user,
        obj,
        campaign_list=world.campaigns,
        campaign=campaign,
        episode=episode,
    )


@campaign_endpoint.route("/<string:pk>/details", methods=("POST",))
def campaigndetails(pk):
    user, obj, *_ = _loader()
    campaign = Campaign.get(pk)
    campaign.save()
    return get_template_attribute("manage/_campaign.html", "campaign_details")(
        user, obj, campaign=campaign
    )


@campaign_endpoint.route("/new", methods=("POST",))
def campaignnew():
    user, obj, world, *_ = _loader()
    campaign = Campaign(world=world, name="New Campaign")
    campaign.save()
    world.campaigns.append(campaign)
    world.save()
    return get_template_attribute(module, macro)(
        user, obj, campaign_list=world.campaigns, campaign=campaign
    )


@campaign_endpoint.route("/<string:pk>/delete", methods=("POST",))
def campaigndelete(pk):
    user, obj, world, *_ = _loader()
    if campaign := Campaign.get(pk):
        world.campaigns.remove(campaign) if campaign in world.campaigns else None
        world.save()
        campaign.delete()
    return get_template_attribute(module, macro)(
        user, obj, campaign_list=world.campaigns, campaign=world.current_campaign
    )


@campaign_endpoint.route("/<string:pk>/update", methods=("POST",))
def campaignupdate(pk):
    user, obj, world, *_ = _loader()
    if campaign := Campaign.get(pk):
        campaign.name = request.json.get("name") or campaign.name
        campaign.description = request.json.get("description") or campaign.description
        campaign.save()
    return get_template_attribute(module, macro)(
        user, obj, campaign_list=world.campaigns, campaign=campaign
    )


@campaign_endpoint.route("/<string:pk>/add/party", methods=("POST",))
def addparty(pk):
    user, obj, *_ = _loader()
    campaign = Campaign.get(pk)
    campaign.party = Faction.get(request.json.get("party"))
    campaign.save()
    return get_template_attribute("manage/_campaign.html", "campaign_details")(
        user, obj, campaign=campaign
    )


@campaign_endpoint.route("/<string:pk>/removeplayer", methods=("POST",))
def removeparty(pk, partypk):
    user, obj, world, *_ = _loader()
    campaign = Campaign.get(pk)
    campaign.party = None
    campaign.save()
    return get_template_attribute(module, macro)(
        user, obj, campaign_list=world.campaigns, campaign=campaign
    )


###########################################################
##                    Episode Routes                    ##
###########################################################
@campaign_endpoint.route("/<string:pk>/episode/details", methods=("POST",))
@campaign_endpoint.route(
    "/<string:pk>/episode/<string:episodepk>/details", methods=("POST",)
)
def episode(pk, episodepk=None):
    user, obj, *_ = _loader()
    campaign = Campaign.get(pk)
    episode = Episode.get(episodepk)
    # log(
    #     "episode details",
    #     episode.name,
    #     episode.episode_num,
    #     episode.start_date,
    #     episode.end_date,
    # )
    return get_template_attribute("manage/_campaign.html", "episode_details")(
        user, obj, campaign=campaign, episode=episode
    )


@campaign_endpoint.route(
    "/<string:pk>/episode/<string:episodepk>/manage", methods=("POST",)
)
@campaign_endpoint.route("/<string:pk>/episode/manage", methods=("POST",))
@campaign_endpoint.route(
    "/<string:pk>/episode/<string:episodepk>/manage", methods=("POST",)
)
@campaign_endpoint.route("/<string:pk>/episode/manage", methods=("POST",))
def episodemanage(pk, episodepk=None):
    user, obj, *_ = _loader()
    campaign = Campaign.get(pk)
    episodepk = episodepk or request.json.get("episodepk")
    if episode := Episode.get(episodepk):
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
        episode.episode_report = request.json.get(
            "episode_report", episode.episode_report
        )
        episode.loot = request.json.get("loot", episode.loot)
        episode.hooks = request.json.get("hooks", episode.hooks)
        episode.save()
        campaign.current_episode = episode
        campaign.save()
    return get_template_attribute("manage/_campaign.html", "episode_details")(
        user, obj, campaign=campaign, episode=episode
    )


@campaign_endpoint.route("/<string:pk>/episode/new", methods=("POST",))
def episodenew(pk):
    user, obj, world, *_ = _loader()
    campaign = Campaign.get(pk)
    episode = campaign.add_episode()
    campaign.current_episode = episode
    return get_template_attribute(module, macro)(
        user,
        obj,
        campaign_list=world.campaigns,
        campaign=campaign,
        episode=campaign.current_episode,
    )


@campaign_endpoint.route("/episode/<string:episodepk>/delete", methods=("POST",))
def episodedelete(episodepk):
    user, obj, world, *_ = _loader()
    episode = Episode.get(episodepk)
    campaign = episode.campaign
    campaign.delete_episode(episodepk)
    # log(module, macro)
    return get_template_attribute(module, macro)(
        user,
        obj,
        campaign_list=world.campaigns,
        campaign=campaign,
        episode=campaign.episodes[-1] if campaign.episodes else None,
    )


@campaign_endpoint.route("/episode/<string:pk>/report", methods=("POST",))
def episodereportpanel(pk):
    user, obj, *_ = _loader()
    episode = Episode.get(pk)
    return get_template_attribute("manage/_campaign.html", "episode_report")(
        user, obj, episode
    )


@campaign_endpoint.route("/episode/<string:pk>/associations", methods=("POST",))
def episodeassociationslist(pk):
    user, obj, *_ = _loader()
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
    user, obj, world, *_ = _loader()
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
        obj = world.get_model(amodel, apk)
        # log(obj)
        episode.add_association(obj)
        if request.json.get("subobjects"):
            for sub in obj.children:
                episode.add_association(sub)
    else:
        new_ass = world.get_model(amodel)(parent=obj, world=world)
        new_ass.save()
        episode.add_association(new_ass)
    return get_template_attribute("manage/_campaign.html", "episode_associations")(
        user, obj, episode
    )


@campaign_endpoint.route(
    "episode/<string:pk>/associations/add/search",
    methods=("POST",),
)
def episodeassociationsearch(pk):
    user, obj, world, *_ = _loader()
    episode = Episode.get(pk)
    query = request.json.get("query")
    results = world.search_autocomplete(query=query) if len(query) > 2 else []
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
    user, obj, world, *_ = _loader()
    episode = Episode.get(pk)
    if a := world.get_model(amodel, apk):
        episode = episode.remove_association(a)
        a.save()
    return "<p>success</p>"
