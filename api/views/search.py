"""
# Components API Documentation

## Components Endpoints
"""

from dmtoolkit import dmtools
from flask import Blueprint, get_template_attribute, request
from slugify import slugify

from autonomous import log

from ._utilities import loader as _loader

search_endpoint = Blueprint("search", __name__)


###########################################################
##                    Component Routes                   ##
###########################################################
@search_endpoint.route("/", methods=("POST",))
def search():
    user, obj, world, macro, module = _loader()
    query = request.json.get("query")
    results = obj.search_autocomplete(query=query) if len(query) > 2 else []
    # log(module, macro, query, [r.name for r in results])
    return get_template_attribute(module, macro)(user, obj, results)


@search_endpoint.route("/dnd5eapi", methods=("POST",))
def dnd5eapi():
    user, obj, *_ = _loader()
    results = []
    if query := request.json.get("query"):
        query = slugify(query)
        log(query)
        if obj.model_name() == "Item":
            results = dmtools.search_item(query)
        elif obj.model_name() == "Creature":
            results = dmtools.search_monster(query)
    log([list(r.keys()) for r in results])
    return get_template_attribute(
        "components/_search.html", "apiobject_completion_select"
    )(user, obj, results)


@search_endpoint.route("/gallery/<string:imgtype>", methods=("POST",))
def imagegallery(imgtype):
    user, obj, *_ = _loader()
    results = []
    if imgtype == "image":
        results = obj.get_image_list()
        macro = "imagegallery"
    elif imgtype == "map":
        results = obj.get_map_list()
        macro = "mapgallery"
    return get_template_attribute("components/_search.html", macro)(user, obj, results)
