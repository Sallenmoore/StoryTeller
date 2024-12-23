"""
# Components API Documentation

## Components Endpoints

"""

from flask import Blueprint, get_template_attribute, request
from jinja2 import TemplateNotFound

from autonomous import log

from ._utilities import loader as _loader

nav_endpoint = Blueprint("nav", __name__)


@nav_endpoint.route("/menu", methods=("POST",))
def menu():
    user, obj, *_ = _loader()
    return get_template_attribute("shared/_nav.html", "topnav")(user, obj)


@nav_endpoint.route(
    "/sidemenu/<string:model>/<string:pk>",
    methods=(
        "GET",
        "POST",
    ),
)
def sidemenudetail(model, pk):
    user, obj, *_ = _loader(model=model, pk=pk)
    try:
        template = get_template_attribute(f"models/_{model}.html", "menu")
    except (TemplateNotFound, AttributeError) as e:
        # log(e, f"no detail menu for {model}")
        return ""
    else:
        return template(user, obj)


@nav_endpoint.route(
    "/search",
    methods=("POST",),
)
def navsearch():
    user, obj, world, *_ = _loader()
    query = request.json.get("query")
    results = world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [r for r in results if r != obj]
    # log(macro, query, [r.name for r in results])
    return get_template_attribute("_nav.html", "nav_dropdown")(user, obj, results)
