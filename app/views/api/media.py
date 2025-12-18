r"""
# Management API Documentation
"""

import base64

import markdown
from autonomous.model.automodel import AutoModel
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from models.images.map import Map
from models.world import World

from ._utilities import loader as _loader

media_endpoint = Blueprint("media", __name__)


# MARK: image route
###########################################################
##                    Image Routes                      ##
###########################################################
@media_endpoint.route("/image", methods=("POST",))
def image():
    user, obj, request_data = _loader()
    return get_template_attribute("shared/_manage.html", "image")(user, obj)


@media_endpoint.route("/image/gallery", methods=("POST",))
def image_gallery():
    user, obj, request_data = _loader()
    return get_template_attribute("shared/_manage.html", "imagegallery")(
        user, obj, images=obj.get_image_list()
    )


# MARK: map routes
###########################################################
##                      Map Routes                       ##
###########################################################
@media_endpoint.route("/map/gallery", methods=("POST",))
def maps_gallery():
    user, obj, request_data = _loader()
    return get_template_attribute("shared/_map.html", "mapgallery")(
        user, obj, maps=obj.get_map_list()
    )


@media_endpoint.route(
    "/map/file/upload",
    methods=("POST",),
)
def map_file_upload():
    user, obj, request_data = _loader()
    if "map" not in request_data:
        return {"error": "No map file uploaded"}, 400
    map_file_str = request_data["map"]
    map_file = base64.b64decode(map_file_str)
    obj.map = Map.from_file(map_file)
    obj.save()
    return get_template_attribute("shared/_map.html", "map")(user, obj)


@media_endpoint.route(
    "<string:pmodel>/<string:ppk>/map/prompt/reset",
    methods=("POST",),
)
def map_prompt_reset(pmodel, ppk):
    user, obj, request_data = _loader()
    obj = World.get_model(pmodel, ppk)
    obj.map_prompt = obj.system.map_prompt(obj)
    obj.map_prompt = (
        markdown.markdown(obj.map_prompt).replace("h1>", "h3>").replace("h2>", "h3>")
    )
    obj.save()
    return get_template_attribute("shared/_map.html", "map")(user, obj)


@media_endpoint.route(
    "<string:pmodel>/<string:ppk>/map/pois",
    methods=("POST",),
)
def map_pois(pmodel, ppk):
    user, obj, request_data = _loader()
    obj = AutoModel.get_model(pmodel, ppk)
    response = []
    for coord in obj.map.coordinates:
        response += [
            {
                "lat": coord.x,
                "lng": coord.y,
                "id": coord.obj.path,
                "name": coord.obj.name,
                "description": coord.obj.description_summary,
                "image": coord.obj.image.url(size=50),
            }
        ]
    return response


@media_endpoint.route(
    "<string:pmodel>/<string:ppk>/map/poi/add/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def map_poi_add(pmodel, ppk, amodel, apk):
    user, obj, request_data = _loader()
    obj = AutoModel.get_model(pmodel, ppk)
    poi = AutoModel.get_model(amodel, apk)
    if poi not in obj.associations:
        raise ValueError(
            f"POI {poi} is not an association of {obj}. Please add it first."
        )
    obj.map.add_poi(poi)
    obj.map.save()
    return get_template_attribute("shared/_map.html", "map")(user, obj)


@media_endpoint.route(
    "<string:pmodel>/<string:ppk>/map/poi/update/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def map_poi_update(pmodel, ppk, amodel, apk):
    user, obj, request_data = _loader()
    obj = AutoModel.get_model(pmodel, ppk)
    poi = AutoModel.get_model(amodel, apk)
    if poi not in obj.associations:
        raise ValueError(
            f"POI {poi} is not an association of {obj}. Please add it first."
        )
    obj.map.update_poi(poi, request.json.get("lat"), request.json.get("lng"))
    return get_template_attribute("shared/_map.html", "map")(user, obj)
