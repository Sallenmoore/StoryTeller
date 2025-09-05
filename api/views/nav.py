"""
# Components API Documentation

## Components Endpoints

"""

from flask import Blueprint, get_template_attribute, request, json, jsonify
from jinja2 import TemplateNotFound

from autonomous import log

from ._utilities import loader as _loader

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
    methods=("POST","GET"),
)
def navsearch():
    user, obj, request_data = _loader()
    query = request.json.get("query")
    results = obj.world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [r for r in results if r != obj]
    # log(macro, query, [r.name for r in results])
    return get_template_attribute("_nav.html", "nav_dropdown")(user, obj, results)
    #return my_list

@nav_endpoint.route(
    "/mentions",
    methods=("POST",),
)
def mentionlookupsearch():
    user, obj, world, *_ = _loader()
    query = request.json.get("query")
    results = world.search_autocomplete(query=query) if len(query) > 2 else []

    response=[]
    for item in results:
        mention = "@" + item.name
        model_name = item.model_name().lower()
        guid = str(item.pk)
        #entry = {"id": mention, "pk": item.id, "name": item.name, "type": item.model_name()}
        entry = {"id": mention, "pk": str(item.pk), "name": item.name, "type": item.model_name().lower(), "guid": guid}
        response.append(entry)
        log(item)
        log(guid)

#        {% macro nav_dropdown(user, obj, objs=[]) -%}
#{% for o in objs %}
#    <a href='/{{o.model_name() | lower}}/{{o.pk}}' target='_blank'>

    log(json.dumps(response))
    #test = "[{'id': 140486713499488, 'name': 'Bukhara Spire Gate - Cocker Mountains', 'type': 'Location'}, {'id': 140486713503296, 'name': 'The Iron Mountain', 'type': 'Location'}, {'id'"
    #responses = Response(jsonify(response), mimetype='application/json')

    return response
