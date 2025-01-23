import json
import os

import markdown
import requests
from dmtoolkit import dmtools
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from models.base.place import Place
from models.campaign.episode import SceneNote
from models.ttrpgobject.character import Character
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item

from ._utilities import loader as _loader

autogm_endpoint = Blueprint("autogm", __name__)


###########################################################
##                     Main Routes                       ##
###########################################################
@autogm_endpoint.route("/", methods=("POST",))
@autogm_endpoint.route("/<string:pk>", methods=("POST",))
def index(model=None, pk=None):
    user, obj, world, *_ = _loader(model=model, pk=pk)
    party = Faction.get(pk or request.json.get("partypk"))
    if party:
        party.save()
        log(party.current_campaign.associations)
    return get_template_attribute("autogm/_shared.html", "autogm_session")(
        user, world, party
    )


@autogm_endpoint.route("/<string:pk>/canonize", methods=("POST",))
def canonizesession(pk):
    user, obj, world, *_ = _loader()
    if party := Faction.get(pk):
        party.end_gm_session()
    return get_template_attribute("autogm/_shared.html", "autogm_session")(
        user, world, party
    )


@autogm_endpoint.route("/<string:pk>/clear", methods=("POST",))
def clearsession(pk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    party.next_scene.delete() if party.next_scene else None
    party.next_scene = None
    for ags in party.autogm_summary:
        ags.delete()
    party.autogm_summary = []
    party.save()
    party.get_next_scene()
    return get_template_attribute("autogm/_shared.html", "autogm_session")(
        user, world, party
    )


## MARK: Submission
###########################################################
##                   Submission Routes                   ##
###########################################################
@autogm_endpoint.route("/<string:pk>/start", methods=("POST",))
def start(pk=None):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    return get_template_attribute("autogm/_shared.html", "autogm_start_session")(
        user, world, party
    )


@autogm_endpoint.route("/<string:pk>/submit", methods=("POST",))
def submit(pk=None):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    if not party.next_scene.gm_ready:
        party.next_scene.gm_ready = True
        pre_text = f"{party.last_scene.summary}" if party.last_scene else ""
        res = requests.post(
            f"http://tasks:{os.environ.get('COMM_PORT')}/generate/audio/{party.next_scene.pk}",
            json={"pre_text": pre_text},
        ).text
        log(res)
    elif party.ready:
        res = requests.post(
            f"http://tasks:{os.environ.get('COMM_PORT')}/generate/autogm/{party.pk}"
        ).text
        log(res)
    else:
        res = get_template_attribute("autogm/_shared.html", "autogm_session")(
            user, world, party
        )
    party.next_scene.save()
    return res


## MARK: Update
###########################################################
##                   Update Routes                       ##
###########################################################
@autogm_endpoint.route("/<string:pk>/edit", methods=("POST",))
def scene_edit(pk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    return get_template_attribute("audogm/_shared.html", "autogm_description_edit")(
        user, world, party
    )


@autogm_endpoint.route("/<string:pk>/scene/update", methods=("POST",))
def scene_update(pk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    log(request.json)
    for sn in party.next_scene.campaign.outline:
        if str(sn.pk) == str(request.json.get("scene")):
            party.next_scene.current_scene = sn
    party.next_scene.current_scene.description = request.json.get("description")
    party.next_scene.current_scene.save()
    party.next_scene.save()
    return get_template_attribute("autogm/_shared.html", "autogm_session")(
        user, world, party
    )


@autogm_endpoint.route("/<string:pk>/scene/<string:snpk>/update", methods=("POST",))
def autogm_update(pk, snpk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    sn = SceneNote.get(snpk)
    sn.description = request.json.get("description", sn.description)
    sn.notes = request.json.get("notes", sn.notes)
    sn.save()
    return get_template_attribute("autogm/_shared.html", "autogm_session")(
        user, world, party
    )


# MARK: Associations
###########################################################
##              Association Routes                       ##
###########################################################


@autogm_endpoint.route("/<string:pk>/associations/search", methods=("POST",))
def autogm_search(pk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    objs = []
    if "npcs" in request.url:
        search = request.json.get("npc_query")
        objs = [w for w in Character.search(name=search, world=party.world)]
    elif "creatures" in request.url:
        search = request.json.get("creature_query")
        objs = [w for w in Creature.search(name=search, world=party.world)]
    elif "items" in request.url:
        search = request.json.get("item_query")
        objs = [w for w in Item.search(name=search, world=party.world)]
    elif "places" in request.url:
        search = request.json.get("place_query")
        objs = [w for w in Place.search(name=search, world=party.world)]
    else:
        search = request.json.get("query")
        objs = [
            w
            for w in world.search_autocomplete(search)
            if w not in party.current_campaign.associations
        ]
    return get_template_attribute("autogm/_shared.html", "autogm_association_search")(
        user, party, objs
    )


@autogm_endpoint.route(
    "/<string:pk>/associations/add/<string:amodel>/<string:apk>", methods=("POST",)
)
@autogm_endpoint.route(
    "/<string:pk>/associations/add/<string:amodel>", methods=("POST",)
)
def autogm_association_add(pk, amodel, apk=None):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)

    if not apk:
        ass = world.get_model(amodel)(world=party.world)
        ass.save()
        for pc in party.players:
            ass.add_association(pc)
    else:
        ass = world.get_model(amodel, apk)

    if ass:
        party.current_campaign.add_association(ass)
    return get_template_attribute("autogm/_shared.html", "autogm_session")(
        user, world, party
    )


@autogm_endpoint.route(
    "/<string:pk>/association/remove/<string:amodel>/<string:apk>", methods=("POST",)
)
@autogm_endpoint.route(
    "/<string:pk>/scene/remove/<string:amodel>/<string:apk>", methods=("POST",)
)
def autogm_association_remove(pk, amodel, apk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    if ass := world.get_model(amodel, apk):
        if "scene" in request.url:
            if amodel == "character" and ass in party.next_scene.npcs:
                party.next_scene.npcs.remove(ass)
            elif amodel == "item" and ass in party.next_scene.loot:
                party.next_scene.loot.remove(ass)
            elif amodel == "creature" and ass in party.next_scene.combatants:
                party.next_scene.combatants.remove(ass)
            elif amodel == "faction" and ass in party.next_scene.factions:
                party.next_scene.factions.remove(ass)
            elif (
                amodel in ["region", "city", "district", "location"]
                and ass in party.next_scene.places
            ):
                party.next_scene.places.remove(ass)
        else:
            party.next_scene.remove_association(ass)
        party.next_scene.save()
    return get_template_attribute("autogm/_shared.html", "autogm_session")(
        user, world, party
    )
