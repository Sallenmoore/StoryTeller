"""
# Components API Documentation

## Components Endpoints

"""

from flask import Blueprint, get_template_attribute, request
from jinja2 import TemplateNotFound

from autonomous import log
from models.campaign import Campaign
from models.world import World

from ._utilities import loader as _loader

page_endpoint = Blueprint("page", __name__)


def get_template(obj, macro, module=None):
    module = module or f"models/_{obj.__class__.__name__.lower()}.html"
    # log(f"Module: {module}, Macro: {macro}")
    try:
        template = get_template_attribute(module, macro)
    except (TemplateNotFound, AttributeError):
        module = f"components/_{macro}.html"
        template = get_template_attribute(module, macro)
    return template


###########################################################
##                    Component Routes                   ##
###########################################################


@page_endpoint.route("/<string:model>/<string:pk>/<string:page>", methods=("POST",))
def model(model, pk, page):
    user, obj, *_ = _loader(model=model, pk=pk)
    return get_template(obj, page)(user, obj)


# MARK: Map routes
###########################################################
##                    Map Routes                    ##
###########################################################
@page_endpoint.route("/<string:model>/<string:pk>/map", methods=("POST",))
def map(model, pk):
    user, obj, *_ = _loader(model=model, pk=pk)
    return get_template_attribute("components/_map.html", "map")(user, obj)


# MARK: Timeline routes
###########################################################
##                    Timeline Routes                    ##
###########################################################
@page_endpoint.route("/<string:model>/<string:pk>/timeline", methods=("POST",))
def timeline(model, pk):
    user, obj, *_ = _loader(model=model, pk=pk)
    events = []
    for c in obj.campaigns:
        c.save()
        events += c.canon
    events.sort()
    return get_template_attribute("components/_timeline.html", "timeline")(
        user, obj, events[::-1]
    )


# MARK: Association routes
###########################################################
##                    Association Routes                 ##
###########################################################
@page_endpoint.route("/<string:model>/<string:pk>/associations", methods=("POST",))
def associations(model, pk):
    user, obj, *_ = _loader(model=model, pk=pk)
    log(request.json)
    if filter_str := request.json.get("filter"):
        associations = [
            o for o in obj.associations if filter_str.lower() in o.name.lower()
        ]
    else:
        associations = obj.associations
    if sorter := request.json.get("sorter"):
        reverse = True if request.json.get("order") == "desc" else False
        if sorter == "date_ended":
            associations.sort(key=lambda x: x.end_date, reverse=reverse)
        if sorter == "date_started":
            associations.sort(key=lambda x: x.start_date, reverse=reverse)
        if sorter == "name":
            associations.sort(key=lambda x: x.name.lower(), reverse=reverse)
    else:
        associations.sort(key=lambda x: x.name)

    if request.json.get("sortfilter") == "canon":
        associations = [o for o in obj.associations if o.check_canon()]
    if request.json.get("sortfilter") == "noncanon":
        associations = [o for o in obj.associations if o.check_canon()]
    return get_template_attribute("components/_associations.html", "associations")(
        user, obj, associations
    )


# MARK: Campaigns route
###########################################################
##                    Campaigns Routes                   ##
###########################################################
@page_endpoint.route("/<string:model>/<string:pk>/campaigns", methods=("POST",))
def campaign(model, pk):
    user, obj, *_ = _loader(model=model, pk=pk)
    campaign = Campaign.get(request.json.get("campaignpk"))
    if not campaign and obj.campaigns:
        campaign = obj.campaigns[0]
    return get_template(obj, "campaigns")(user, obj, campaign)


# MARK: Childpanel routes
###########################################################
##                    Childpanel Routes                  ##
###########################################################
@page_endpoint.route(
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
