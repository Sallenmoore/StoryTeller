"""
# Components API Documentation

## Components Endpoints

"""

from flask import Blueprint, get_template_attribute, request
from jinja2 import TemplateNotFound

from autonomous import log

from .test_utilities import loader as _loader

nav_endpoint = Blueprint("nav", __name__)


@nav_endpoint.route("/menu", methods=("POST",))
def menu():
    user, obj, request_data = _loader()
    return get_template_attribute("shared/_nav.html", "topnav")(user, obj)


@nav_endpoint.route(
    "/sidemenu/<string:model>/<string:pk>",
    methods=(
        "GET",
        "POST",
    ),
)
def sidemenudetail(model, pk):
    user, obj, request_data = _loader()
    try:
        template = get_template_attribute(f"models/_{model}.html", "menu")
    except (TemplateNotFound, AttributeError) as e:
        log(e, f"no detail menu for {model}")
        return ""
    else:
        return template(user, obj)


@nav_endpoint.route(
    "/search",
    methods=("POST",),
)
def navsearch():
    user, obj, request_data = _loader()
    query = request.json.get("query")
    results = []
    if len(query) > 2:
        if obj:
            results = obj.world.search_autocomplete(query=query)
            results = [r for r in results if r != obj]
        else:
            results = [
                r for w in user.worlds for r in w.search_autocomplete(query=query)
            ]

    # log(macro, query, [r.name for r in results])
    return get_template_attribute("_nav.html", "nav_dropdown")(user, obj, results)


@nav_endpoint.route(
    "/mentions",
    methods=("POST",),
)
def mentionsearch():
    user, obj, request_data = _loader()
    query = request.json.get("query")
    results = obj.world.search_autocomplete(query=query) if len(query) > 2 else []

    response = []
    for item in results:
        mention = "@" + item.name
        model_name = item.model_name().lower()
        guid = str(item.pk)
        entry = {
            "id": mention,
            "pk": str(item.pk),
            "name": item.name,
            "type": item.model_name().lower(),
            "guid": guid,
        }
        response.append(entry)

    return response
