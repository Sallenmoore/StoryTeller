"""
# Components API Documentation

## Components Endpoints
"""

from autonomous.model.automodel import AutoModel
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from models.campaign import Campaign
from models.campaign.episode import Episode
from models.stories.encounter import Encounter
from models.ttrpgobject.character import Character
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


@campaign_endpoint.route("/<string:pk>/delete", methods=("POST",))
def campaigndelete(pk):
    user, obj, request_data = _loader()
    if campaign := Campaign.get(pk):
        obj.world.campaigns.remove(
            campaign
        ) if campaign in obj.world.campaigns else None
        obj.world.save()
        campaign.delete()
    return get_template_attribute("models/_campaign.html")(
        user,
        campaign=obj.world.current_campaign,
    )


@campaign_endpoint.route("/<string:pk>/update", methods=("POST",))
def campaignupdate(pk):
    user, obj, request_data = _loader()
    if campaign := Campaign.get(pk):
        campaign.name = request.json.get("name") or campaign.name
        campaign.description = request.json.get("description") or campaign.description
        campaign.one_shot = request.json.get("one_shot") or campaign.one_shot
        campaign.save()
    return get_template_attribute("models/_campaign.html", "manage")(user, campaign)


@campaign_endpoint.route("/<string:pk>/add/party", methods=("POST",))
def addparty(pk):
    user, obj, request_data = _loader()
    campaign = Campaign.get(pk)
    campaign.party = Faction.get(request.json.get("party"))
    campaign.save()
    return get_template_attribute("models/_campaign.html", "manage")(user, campaign)


@campaign_endpoint.route("/<string:pk>/removeplayer/<string:cpk>", methods=("POST",))
def removeplayer(pk, cpk):
    user, obj, request_data = _loader()
    campaign = Campaign.get(pk)
    character = Character.get(cpk)
    character.faction = None
    character.save()
    return get_template_attribute("models/_campaign.html", "manage")(user, campaign)


###########################################################
##                    Episode Routes                    ##
###########################################################


@campaign_endpoint.route("/<string:pk>/episode/new", methods=("POST",))
def episodenew(pk):
    user, obj, request_data = _loader()
    campaign = Campaign.get(pk)
    episode = campaign.add_episode()
    log(
        "Episode Created",
        f"Episode {episode.name} ({episode.episode_num}) created in campaign {episode.campaign.name}",
    )
    campaign.save()
    return get_template_attribute("models/_campaign.html", "episodes")(
        user,
        campaign,
    )
