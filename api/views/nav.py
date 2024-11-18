"""
# Components API Documentation

## Components Endpoints

"""

from flask import Blueprint, get_template_attribute
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
