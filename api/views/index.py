"""
# Components API Documentation

## Components Endpoints

"""

import random

from flask import Blueprint, get_template_attribute, request
from jinja2 import TemplateNotFound

from autonomous import log
from models.world import World

from ._utilities import loader as _loader

index_endpoint = Blueprint("page", __name__)


def get_template(obj, macro, module=None):
    module = module or f"models/_{obj.__class__.__name__.lower()}.html"
    # log(f"Module: {module}, Macro: {macro}")
    try:
        template = get_template_attribute(module, macro)
    except (TemplateNotFound, AttributeError):
        module = f"shared/_{macro}.html"
        template = get_template_attribute(module, macro)
    return template


###########################################################
##                    Component Routes                   ##
###########################################################
@index_endpoint.route(
    "/auth/login",
    methods=(
        "GET",
        "POST",
    ),
)
def login():
    worlds = World.all()
    worlds = random.sample(worlds, 4) if len(worlds) > 4 else worlds
    return get_template_attribute("login.html", "login")(worlds=worlds)


@index_endpoint.route(
    "/home",
    methods=(
        "GET",
        "POST",
    ),
)
def home():
    user, *_ = _loader()
    return get_template_attribute("home.html", "home")(user)


@index_endpoint.route(
    "/build",
    methods=("POST",),
)
def build():
    user, *_ = _loader()
    World.build(
        system=request.json.get("system"),
        user=user,
        name=request.json.get("name"),
        desc=request.json.get("desc"),
        backstory=request.json.get("backstory"),
    )

    return get_template_attribute("home.html", "home")(user)


@index_endpoint.route("/build/form", methods=("POST",))
def buildform():
    user, *_ = _loader()
    return get_template_attribute("home.html", "worldbuild")(user=user)


@index_endpoint.route(
    "/<string:model>/<string:pk>/<string:page>",
    methods=(
        "GET",
        "POST",
    ),
)
def model(model, pk, page):
    log(request.args)
    user, obj, *_ = _loader(model=model, pk=pk)
    return get_template(obj, page)(user, obj)


# MARK: Map routes
###########################################################
##                    Map Routes                    ##
###########################################################
@index_endpoint.route("/<string:model>/<string:pk>/map", methods=("POST",))
def map(model, pk):
    user, obj, *_ = _loader(model=model, pk=pk)
    return get_template_attribute("components/_map.html", "map")(user, obj)


# MARK: Association routes
###########################################################
##                    Association Routes                 ##
###########################################################
@index_endpoint.route("/<string:model>/<string:pk>/associations", methods=("POST",))
def associations(model, pk):
    user, obj, *_ = _loader(model=model, pk=pk)
    log(request.json)
    if filter_str := request.json.get("filter"):
        associations = [
            o for o in obj.associations if filter_str.lower() in o.name.lower()
        ]
    else:
        associations = obj.associations
    associations.sort(key=lambda x: x.name)

    return get_template_attribute("components/_associations.html", "associations")(
        user, obj, associations
    )


# MARK: Childpanel routes
###########################################################
##                    Childpanel Routes                  ##
###########################################################
@index_endpoint.route(
    "/<string:model>/<string:pk>/childpanel/<string:childmodel>",
    methods=("POST",),
)
def childpanel(model, pk, childmodel):
    user, obj, *_ = _loader(model=model, pk=pk)
    childmodel = obj.get_model(childmodel).__name__
    query = request.json.get("query") or None
    children = []
    associations = []
    for child in obj.get_associations(childmodel):
        if not query or query.lower() in child.name.lower():
            children.append(child) if child.parent == obj else associations.append(
                child
            )
    return get_template(obj, "childpanel")(
        user, obj, childmodel, children=children, associations=associations
    )
