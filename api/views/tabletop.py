import random

import dmtoolkit
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from models.campaign import Campaign
from models.campaign.session import Session
from models.character import Character
from models.city import City
from models.creature import Creature
from models.encounter import Encounter
from models.item import Item
from models.location import Location
from models.poi import POI
from models.region import Region
from models.user import User
from models.world import World

from ._utilities import loader as _loader

tabletop_endpoint = Blueprint("tabletop", __name__)
macro = "tabletop"
module = "manage/_tabletop.html"


###########################################################
##                    Component Routes                   ##
###########################################################
@tabletop_endpoint.route("/", methods=("POST",))
def index():
    user, _, world, *_ = _loader()
    campaign = None
    if episode := Session.get(request.json.get("episodepk")):
        campaign = episode.set_as_current()
    else:
        campaign = Campaign.get(request.json.get("campaignpk"))
    return get_template_attribute(module, macro)(user, world, campaign)


# @tabletop_endpoint.route("/<string:pk>/sceneorder", methods=("POST",))
# def sceneorder(pk):
#     user, _, world, *_ = _loader()
#     episode = Session.get(pk)
#     # episode.scenes = [Location.get(scenepk) or POI.get(scenepk) for scenepk in request.json.get("scenes")]
#     # episode.save()
#     return get_template_attribute(module, macro)(user, world, episode.campaign)


@tabletop_endpoint.route("/<string:episodepk>/show/clear", methods=("POST",))
def showclear(episodepk, model=None, pk=None):
    user, obj, *_ = _loader()
    episode = Session.get(episodepk)
    episode.show = None
    episode.is_updated = True
    episode.save()
    return get_template_attribute(module, "managescene")(
        user, obj, episode, episode.current_scene
    )


@tabletop_endpoint.route(
    "/<string:episodepk>/show/<string:model>/<string:pk>", methods=("POST",)
)
def show(episodepk, model, pk):
    user, obj, *_ = _loader()
    episode = Session.get(episodepk)
    episode.show = World.get_model(model, pk)
    episode.is_updated = True
    episode.save()
    return get_template_attribute(module, "managescene")(
        user, obj, episode, episode.current_scene
    )


@tabletop_endpoint.route("/<string:episodepk>/show/search", methods=("POST",))
def showsearch(episodepk, model=None, pk=None):
    user, obj, *_ = _loader()
    query = request.json.get("query")
    episode = Session.get(episodepk)
    results = obj.search_autocomplete(query=query) if len(query) > 2 else []
    # log(macro, query, [r.name for r in results])
    return get_template_attribute(module, "map_show_dropdown")(
        user, obj, episode, results
    )


@tabletop_endpoint.route(
    "/<string:episodepk>/scene/<string:model>/<string:pk>/set", methods=("POST",)
)
def sceneselect(episodepk, model, pk):
    user, obj, *_ = _loader()
    scene = World.get_model(model, pk)
    episode = Session.get(episodepk)
    episode.current_scene = scene
    episode.is_updated = True
    scene.save()
    episode.save()
    return get_template_attribute(module, "managescene")(user, obj, episode, scene)


@tabletop_endpoint.route(
    "/<string:episodepk>/scene/<string:model>/<string:pk>/set", methods=("POST",)
)
def geographyselect(episodepk, model, pk):
    user, obj, *_ = _loader()
    scene = World.get_model(model, pk)
    episode = Session.get(episodepk)
    episode.is_updated = True
    episode.save()
    return get_template_attribute(module, "managescene")(user, obj, episode, scene)


@tabletop_endpoint.route(
    "/<string:episodepk>/scene/<string:pk>/update", methods=("POST",)
)
def sceneupdate(episodepk, pk):
    user, obj, *_ = _loader()
    episode = Session.get(episodepk)
    scene = episode.get_scene(pk)

    if encounter := Encounter.get(request.json.get("encounterpk")):
        scene.current_encounter = encounter

    if actor := Character.get(request.json.get("actorpk")) or Creature.get(
        request.json.get("actorpk")
    ):
        scene.current_actor = actor

    if item := Item.get(request.json.get("itempk")):
        scene.current_item = item

    if last_roll := request.json.get("roll"):
        log(last_roll)
        episode.last_roll = last_roll
        episode.last_roll_result = dmtoolkit.dmtools.dice_roll(last_roll)[0]

    if request.json.get("grid") is not None:
        scene.grid = request.json.get("grid")
        scene.grid_color = request.json.get("grid_color")
        scene.grid_size = int(request.json.get("grid_size"))

    if request.json.get("fow") is not None:
        scene.fow = request.json.get("fow")

    if request.json.get("music") is not None:
        scene.music = request.json.get("music")

    scene.save()
    episode.current_scene = scene
    episode.is_updated = True
    episode.save()
    # log(scene.current["encounter"], scene.current["actor"], scene.current["item"])
    return get_template_attribute(module, "managescene")(
        user, obj, episode, episode.current_scene
    )


@tabletop_endpoint.route(
    "/<string:episodepk>/scene/<string:pk>/map/rotate", methods=("POST",)
)
def rotateimage(episodepk, pk):
    user, obj, *_ = _loader()
    episode = Session.get(episodepk)
    scene = episode.get_scene(pk)
    scene.map.rotate()
    scene.save()
    episode.is_updated = True
    episode.save()
    return get_template_attribute(module, "managescene")(
        user, obj, episode, episode.current_scene
    )


@tabletop_endpoint.route(
    "/<string:episodepk>/scene/<string:pk>/map/flip", methods=("POST",)
)
def flipimage(episodepk, pk):
    user, obj, *_ = _loader()
    episode = Session.get(episodepk)
    scene = episode.get_scene(pk)
    scene.map.flip()
    scene.save()
    episode.is_updated = True
    episode.save()
    return get_template_attribute(module, "managescene")(
        user, obj, episode, episode.current_scene
    )


@tabletop_endpoint.route(
    "/<string:episodepk>/scene/<string:scenepk>/data", methods=("GET",)
)
def scenedata(episodepk, scenepk):
    episode = Session.get(episodepk)
    scene = episode.get_scene(scenepk)
    scene_data = {
        "is_updated": episode.is_updated,
        "img": scene.map.url(),
        "grid": scene.grid,
        "fow": scene.fow,
        "show": {
            "name": episode.show.name if episode.show else "",
            "img": episode.show.image.url()
            if episode.show and episode.show.image
            else "",
            "map": episode.show.map.url()
            if isinstance(episode.show, (World, Region, City)) and episode.show.map
            else "",
            "summary": episode.show.backstory_summary if episode.show else "",
        },
        "music": scene.music,
    }
    episode.is_updated = False
    episode.save()
    log(scene_data)
    return scene_data
