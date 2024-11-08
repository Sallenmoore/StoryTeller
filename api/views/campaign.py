"""
# Components API Documentation

## Components Endpoints
"""

import json
import random

from flask import Blueprint, get_template_attribute, request

from autonomous import log
from models.campaign import Campaign
from models.campaign.episode import Session
from models.character import Character
from models.events.event import Event

from ._utilities import loader as _loader

campaign_endpoint = Blueprint("campaign", __name__)
module = "manage/_campaign.html"
macro = "campaigns"


###########################################################
##                    Campaign Routes                    ##
###########################################################
@campaign_endpoint.route("/manager", methods=("POST",))
@campaign_endpoint.route("/manager/<string:pk>", methods=("POST",))
@campaign_endpoint.route(
    "/manager/<string:pk>/session/<string:sessionpk>", methods=("POST",)
)
def campaigns(pk=None, sessionpk=None):
    user, obj, world, *_ = _loader()
    pk = pk or request.json.get("campaignpk")
    sessionpk = sessionpk or request.json.get("sessionpk")
    if campaign := Campaign.get(pk) or world.current_campaign:
        campaign.current_episode = (
            Session.get(sessionpk) if sessionpk else campaign.current_episode
        )
        campaign.save()
    return get_template_attribute(module, macro)(
        user,
        obj,
        campaign_list=world.campaigns,
        campaign=campaign,
        episode=campaign.current_episode if campaign else None,
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
def campaignupdate(pk=None):
    user, obj, world, *_ = _loader()
    if campaign := Campaign.get(pk):
        campaign.name = request.json.get("name") or campaign.name
        campaign.description = request.json.get("description") or campaign.description
        campaign.save()
        world.current_campaign = (
            campaign if request.json.get("current_campaign") else None
        )
        world.save()
    return get_template_attribute(module, macro)(
        user, obj, campaign_list=world.campaigns, campaign=campaign
    )


@campaign_endpoint.route("/<string:pk>/addplayer", methods=("POST",))
def addplayer(pk):
    user, obj, world, *_ = _loader()
    campaign = Campaign.get(pk)
    for playerpk in request.json.get("players"):
        player = Character.get(playerpk)
        log(player.name, campaign.players)
        if player and player not in campaign.players:
            log("appended player", player.name, "to", campaign.players)
            campaign.players += [player]
            log("appended player", campaign.players)
            campaign.save()
    return get_template_attribute(module, macro)(
        user, obj, campaign_list=world.campaigns, campaign=campaign
    )


@campaign_endpoint.route(
    "/<string:pk>/removeplayer/<string:playerpk>", methods=("POST",)
)
def removeplayer(pk, playerpk):
    user, obj, world, *_ = _loader()
    campaign = Campaign.get(pk)
    player = Character.get(playerpk)
    if player in campaign.players:
        campaign.players.remove(player)
        campaign.save()
    return get_template_attribute(module, macro)(
        user, obj, campaign_list=world.campaigns, campaign=campaign
    )


@campaign_endpoint.route("/<string:pk>/episode/<string:sessionpk>", methods=("POST",))
@campaign_endpoint.route("/<string:pk>/session/<string:sessionpk>", methods=("POST",))
def session(pk, sessionpk=None):
    user, obj, world, *_ = _loader()
    campaign = Campaign.get(pk)
    episode = Session.get(sessionpk)
    return get_template_attribute(module, macro)(
        user, obj, campaign_list=world.campaigns, campaign=campaign, episode=episode
    )


@campaign_endpoint.route(
    "/<string:pk>/episode/<string:sessionpk>/manage", methods=("POST",)
)
@campaign_endpoint.route("/<string:pk>/episode/manage", methods=("POST",))
@campaign_endpoint.route(
    "/<string:pk>/session/<string:sessionpk>/manage", methods=("POST",)
)
@campaign_endpoint.route("/<string:pk>/session/manage", methods=("POST",))
def sessionmanage(pk, sessionpk=None):
    user, obj, world, *_ = _loader()
    campaign = Campaign.get(pk)
    sessionpk = sessionpk or request.json.get("sessionpk")
    if episode := Session.get(sessionpk):
        episode.name = request.json.get("name", episode.name)
        if description := request.json.get("description"):
            if description != episode.description:
                episode.description = description
                episode.summary = ""
        episode.episode_num = request.json.get("episode_num", episode.episode_num)
        episode.start_date = request.json.get("start_date", episode.start_date)
        episode.end_date = request.json.get("end_date", episode.end_date)
        episode.session_report = request.json.get(
            "session_report", episode.session_report
        )
        episode.save()
        campaign.current_episode = episode
        campaign.save()
    return get_template_attribute(module, macro)(
        user,
        obj,
        campaign_list=world.campaigns,
        campaign=campaign,
        episode=campaign.current_episode,
    )


@campaign_endpoint.route("/<string:pk>/episode/new", methods=("POST",))
@campaign_endpoint.route("/<string:pk>/session/new", methods=("POST",))
def sessionnew(pk):
    user, obj, world, *_ = _loader()
    campaign = Campaign.get(pk)
    episode = campaign.add_session()
    campaign.current_episode = episode
    return get_template_attribute(module, macro)(
        user,
        obj,
        campaign_list=world.campaigns,
        campaign=campaign,
        episode=campaign.current_episode,
    )


@campaign_endpoint.route("/episode/<string:episodepk>/delete", methods=("POST",))
@campaign_endpoint.route("/session/<string:episodepk>/delete", methods=("POST",))
def sessiondelete(episodepk):
    user, obj, world, *_ = _loader()
    episode = Session.get(episodepk)
    campaign = episode.campaign
    campaign.delete_session(episodepk)
    log(module, macro)
    return get_template_attribute(module, macro)(
        user,
        obj,
        campaign_list=world.campaigns,
        campaign=campaign,
        episode=campaign.sessions[-1] if campaign.sessions else None,
    )


@campaign_endpoint.route("/episode/<string:pk>/report", methods=("POST",))
def sessionreportpanel(pk):
    user, obj, world, *_ = _loader()
    episode = Session.get(pk)
    return get_template_attribute("manage/_campaign.html", "episode_report")(
        user, obj, episode
    )


@campaign_endpoint.route("/episode/<string:pk>/gmplanner", methods=("POST",))
def sessiongmplannerpanel(pk):
    user, obj, world, *_ = _loader()
    episode = Session.get(pk)
    return get_template_attribute("manage/_campaign.html", "episode_gmplanner")(
        user, obj, episode
    )


@campaign_endpoint.route(
    "episode/<string:pk>/associations",
    methods=("POST",),
)
def episodeassociations(pk):
    user, obj, world, *_ = _loader()
    episode = Session.get(pk)
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
    episode = Session.get(pk)
    if amodel == "campaignassociations":
        for a in episode.campaign.associations:
            episode.add_association(a)
    elif amodel == "episodeassociations":
        if episode != episode.campaign.episodes[-1]:
            index = episode.campaign.episodes.index(episode)
            prev_episode = episode.campaign.episodes[index + 1]
            for a in prev_episode.associations:
                episode.add_association(a)
        else:
            log("no previous episodes")
    elif amodel == "players":
        for p in episode.campaign.players:
            episode.add_association(p)
    elif apk:
        obj = world.get_model(amodel, apk)
        log(obj)
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
    episode = Session.get(pk)
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
    episode = Session.get(pk)
    if a := world.get_model(amodel, apk):
        episode = episode.remove_association(a)
    return "<p>success</p>"


@campaign_endpoint.route(
    "/episode/<string:pk>/event",
    methods=("POST",),
)
def episodeevent(pk):
    user, obj, world, *_ = _loader()
    episode = Session.get(pk)
    if scene := episode.get_scene(request.json.get("scenepk")):
        if not scene.events:
            log("updating events")
            scene.save()
        events = scene.get_scene_events()
    else:
        events = episode.events
    if event := Event.get(request.json.get("eventpk")):
        episode.campaign.set_as_canon(event)
    # log(events, episode.campaign.events)
    return get_template_attribute("manage/_campaign.html", "episode_events")(
        user, obj, episode, scene, events
    )
