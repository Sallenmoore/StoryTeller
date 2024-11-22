from flask import Blueprint, Response, get_template_attribute, request

from autonomous import log
from models.ttrpgobject.character import Character
from models.ttrpgobject.faction import Faction
from models.user import User
from models.world import World

from ._utilities import loader as _loader

autogm_endpoint = Blueprint("autogm", __name__)


###########################################################
##                    World Routes                       ##
###########################################################
@autogm_endpoint.route("/", methods=("POST",))
@autogm_endpoint.route("/<string:model>/<string:pk>", methods=("POST",))
def index(model=None, pk=None):
    user, obj, world, *_ = _loader(model=model, pk=pk)
    log(model, pk)
    party = None
    if "faction" in request.url or request.json.get("partypk"):
        pk = pk or request.json.get("partypk")
        party = Faction.get(pk)
    return get_template_attribute("shared/_gm.html", "gm")(user, world, party)


@autogm_endpoint.route("/associations/search", methods=("POST",))
def autogm_search():
    user, obj, world, *_ = _loader()
    search = request.json.get("query")
    if search and len(search) > 2:
        objs = [
            w
            for w in world.search_autocomplete(search)
            if "party" not in request.url or w.player
        ]
    return get_template_attribute("shared/_gm.html", "party")(user, world, objs)


@autogm_endpoint.route("/party/<string:pk>/input", methods=("POST",))
def party_input(pk):
    user, obj, world, *_ = _loader()
    party_member = Character.get(request.json.get("party_member"))
    party = Faction.get(pk)
    party.add_association(party_member)
    return get_template_attribute("shared/_gm.html", "autogm_start_session")(
        user, world, party
    )


@autogm_endpoint.route(
    "/<string:partypk>/party/add/<string:pk>",
    methods=("POST",),
)
def autogm_party_add(partypk, pk):
    user, obj, world, *_ = _loader()
    party = Faction.get(partypk)
    party_member = Character.get(pk)
    party.add_association(party_member)


@autogm_endpoint.route(
    "/<string:model>/<string:pk>/description/edit", methods=("POST",)
)
def descriptionedit(model, pk):
    user, obj, world, *_ = _loader(model=model, pk=pk)
    return get_template_attribute("shared/_gm.html", "autogm_description_edit")(
        user, world, obj
    )


@autogm_endpoint.route(
    "/<string:model>/<string:pk>/description/update", methods=("POST",)
)
def descriptionupdate(model, pk):
    user, obj, world, *_ = _loader(model=model, pk=pk)
    obj.autogm_summary[-1].description = request.json.get("description")
    obj.autogm_summary[-1].save()
    return get_template_attribute("shared/_gm.html", "gm")(user, world, obj)


@autogm_endpoint.route("/<string:model>/<string:pk>/clear", methods=("POST",))
def clearsession(model, pk):
    user, obj, world, *_ = _loader(model=model, pk=pk)
    for ags in obj.autogm_summary:
        ags.delete()
    obj.autogm_summary = []
    obj.save()
    return get_template_attribute("shared/_gm.html", "gm")(user, world, obj)
