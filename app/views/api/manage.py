r"""
# Management API Documentation
"""

import base64
import json
import os
import random
import re

import markdown
import requests
from autonomous.model.automodel import AutoModel
from bs4 import BeautifulSoup
from dmtoolkit import dmtools
from flask import Blueprint, get_template_attribute, request
from slugify import slugify

from autonomous import log
from models.images.map import Map
from models.journal import JournalEntry
from models.stories.encounter import Encounter
from models.stories.event import Event
from models.stories.quest import Quest
from models.stories.story import Story
from models.ttrpgobject.ability import Ability
from models.ttrpgobject.character import Character
from models.ttrpgobject.city import City
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.district import District
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.user import User
from models.world import World

from ._utilities import loader as _loader

manage_endpoint = Blueprint("manage", __name__)


# MARK: CRUD routes
###########################################################
##                    CRUD Routes                        ##
###########################################################
@manage_endpoint.route("/add/<string:model>", methods=("POST",))
def add(model):
    user, obj, request_data = _loader()
    new_obj = World.get_model(model)(world=obj.world)
    new_obj.save()
    # log(new_obj.pk)
    obj.add_association(new_obj)
    associations = obj.associations
    relations = [a for a in associations if a in obj.children]
    relations += [
        a for a in obj.geneology if a.model_name() not in ["World", "Campaign"]
    ]
    associations = [a for a in associations if a not in relations]
    return get_template_attribute(f"models/_{model}.html", "associations")(
        user, obj, extended_associations=associations, direct_associations=relations
    )


@manage_endpoint.route("/update", methods=("POST",))
def update():
    user, obj, request_data = _loader()
    request_data.pop("user", None)
    request_data.pop("model", None)
    response_url = request_data.pop("response_path", None)
    log(response_url)
    for attr, value in request_data.items():
        ########## SECURITY: remove any javascript tags for security reasons ############
        if isinstance(value, str) and "<" in value:
            parser = BeautifulSoup(value, "html.parser")
            for script in parser.find_all("script"):
                script.decompose()
            value = parser.prettify()
        if hasattr(obj, attr):
            # log(f"setting {attr} to {value}")
            setattr(obj, attr, value)
        else:
            log(f"Attribute or property for {obj.model_name()} not found: {attr}")
        # log(f"Updated {obj.model_name()}:{obj.pk} - set {attr} to {value}", _print=True)
    obj.save()
    log(obj.model_name().lower())
    return get_template_attribute(f"models/_{obj.model_name().lower()}.html", "manage")(
        user, obj
    )


@manage_endpoint.route("/add/listitem/<string:attr>", methods=("POST",))
def addlistitem(attr):
    user, obj, request_data = _loader()
    if isinstance(getattr(obj, attr, None), list):
        item = getattr(obj, attr)
        if item is not None:
            item += [""]
        log(getattr(obj, attr))
    return get_template_attribute(f"manage/_{obj.model_name().lower()}.html", "manage")(
        user, obj
    )


@manage_endpoint.route("/delete/<string:model>/<string:pk>", methods=("POST",))
def delete(model, pk):
    user, obj, request_data = _loader()
    obj = AutoModel.get_model(model, pk)
    world = obj.world
    obj.delete()
    return get_template_attribute("models/_world.html", "history")(user, world)


# MARK: Association route
###########################################################
##                 Associations Routes                   ##
###########################################################


@manage_endpoint.route("/association/add/search", methods=("POST",))
def association_search():
    user, obj, request_data = _loader()
    query = request.json.get("query")
    associations = (
        obj.world.search_autocomplete(query) if query and len(query) > 2 else []
    )
    associations = [a for a in associations if a not in obj.associations and a != obj]
    return get_template_attribute("shared/_dropdown.html", "search_dropdown")(
        user, obj, "manage/association/add", associations
    )


@manage_endpoint.route("/association/add/<string:amodel>", methods=("POST",))
@manage_endpoint.route(
    "/association/add/<string:amodel>/<string:apk>", methods=("POST",)
)
def association_add(amodel, apk=None):
    user, obj, request_data = _loader()
    if not apk:
        model = AutoModel.get_model(amodel)
        child = model(world=obj.world, name="New " + obj.world.get_title(model))
        child.save()
    else:
        child = World.get_model(amodel, apk)
    if child:
        obj.add_association(child)
    if hasattr(obj, "split_associations"):
        relations, associations = obj.split_associations(associations=obj.associations)
    else:
        relations = []
        associations = obj.associations
    return get_template_attribute(
        f"models/_{obj.model_name().lower()}.html", "associations"
    )(user, obj, extended_associations=associations, direct_associations=relations)


@manage_endpoint.route(
    "/unassociate/<string:childmodel>/<string:childpk>", methods=("POST",)
)
def unassociate(childmodel, childpk):
    user, obj, _ = _loader()
    associations = []
    if child := World.get_model(childmodel, childpk):
        obj.remove_association(child)
        associations = obj.associations
    else:
        for association in obj.associations:
            if str(association.pk) == childpk:
                obj.remove_association(association)
            else:
                associations += [association]

    if hasattr(obj, "split_associations"):
        relations, associations = obj.split_associations(associations=associations)
    else:
        relations = []
    return get_template_attribute(
        f"models/_{obj.model_name().lower()}.html", "associations"
    )(user, obj, extended_associations=associations, direct_associations=relations)


@manage_endpoint.route(
    "/parent/<string:childmodel>/<string:childpk>", methods=("POST",)
)
def makeparentof(childmodel, childpk):
    user, obj, _ = _loader()
    child = World.get_model(childmodel).get(childpk)
    child.parent = obj
    if obj.parent == child:
        obj.parent = child.parent
        obj.save()
    child.save()
    if hasattr(obj, "split_associations"):
        relations, associations = obj.split_associations()
    else:
        relations = []
    return get_template_attribute(
        f"models/_{obj.model_name().lower()}.html", "associations"
    )(user, obj, extended_associations=associations, direct_associations=relations)


@manage_endpoint.route("/child/<string:childmodel>/<string:childpk>", methods=("POST",))
def makechildof(childmodel, childpk):
    user, child, request_data = _loader()
    parent = World.get_model(childmodel).get(childpk)
    child.parent = parent
    if parent.parent == child:
        parent.parent = child.parent
        parent.save()
    child.save()
    if hasattr(child, "split_associations"):
        relations, associations = child.split_associations()
    else:
        relations = []
    return get_template_attribute(
        f"models/_{child.model_name().lower()}.html", "associations"
    )(user, child, extended_associations=associations, direct_associations=relations)


# MARK: Owner routes
###########################################################
##                Owner Routes                    ##
###########################################################
@manage_endpoint.route("/owner/add/search", methods=("POST",))
def owner_search():
    user, obj, request_data = _loader()
    query = request.json.get("query")
    associations = (
        obj.world.search_autocomplete(query) if query and len(query) > 2 else []
    )
    associations = [a for a in associations if a.model_name() == "Character"]
    return get_template_attribute("models/_shop.html", "owner_dropdown")(
        user, obj, associations
    )


@manage_endpoint.route(
    "<string:pmodel>/<string:ppk>/owner/add/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def owner_add(pmodel, ppk, amodel, apk):
    user, obj, request_data = _loader()
    obj = World.get_model(pmodel, ppk)
    owner = World.get_model(amodel, apk)
    obj.owner = owner
    obj.save()
    log(obj.owner)
    if owner not in obj.associations:
        obj.add_association(owner)
    return get_template_attribute("manage/_details.html", "details")(user, obj)


# MARK: Character routes
###########################################################
##                Character Routes                    ##
###########################################################
@manage_endpoint.route(
    "/character/hitpoints",
    methods=(
        "GET",
        "POST",
    ),
)
def characterhitpoints():
    user, obj, request_data = _loader()
    log(request.args.get("current_hitpoints", obj.hitpoints))
    obj.current_hitpoints = int(request.args.get("current_hitpoints", obj.hitpoints))
    obj.save()
    return get_template_attribute("models/_character.html", "details")(user, obj)


@manage_endpoint.route("/character/addlineage", methods=("POST",))
def lineage():
    user, obj, request_data = _loader()
    role = request_data.get("role")
    # log(request_data)
    if character := Character.get(request_data.get("character")):
        if role == "parent" and character not in obj.parent_lineage:
            obj.parent_lineage += [character]
            if obj not in character.children_lineage:
                character.children_lineage += [obj]
        elif role == "sibling" and character not in obj.sibling_lineage:
            obj.sibling_lineage += [character]
            if obj not in character.sibling_lineage:
                character.sibling_lineage += [obj]
        elif role == "child" and character not in obj.children_lineage:
            obj.children_lineage += [character]
            if obj not in character.parent_lineage:
                character.parent_lineage += [obj]
        character.save()
        obj.save()
        obj.add_association(character)
    return get_template_attribute("models/_character.html", "lineage")(user, obj)


@manage_endpoint.route("/character/removelineage/<string:character>", methods=("POST",))
def removelineage(character):
    user, obj, request_data = _loader()
    if character := Character.get(character):
        if character in obj.parent_lineage:
            obj.parent_lineage.remove(character)
            if obj in character.children_lineage:
                character.children_lineage.remove(obj)
        elif character in obj.sibling_lineage:
            obj.sibling_lineage.remove(character)
            if obj in character.sibling_lineage:
                character.sibling_lineage.remove(obj)
        elif character in obj.children_lineage:
            obj.children_lineage.remove(character)
            if obj in character.parent_lineage:
                character.parent_lineage.remove(obj)
        character.save()
        obj.save()
    return get_template_attribute("models/_character.html", "lineage")(user, obj)


# MARK: quest route
###########################################################
##                    Quest Routes                     ##
###########################################################
@manage_endpoint.route("/<string:characterpk>/quest/create", methods=("POST",))
def create_quest_entry(characterpk):
    user, obj, request_data = _loader()
    character = Character.get(characterpk)
    storyline = Story.get(request.json.get("storyline"))
    entry = Quest(
        name=f"Quest #{len(obj.quests) + 1}",
        storyline=storyline,
        contact=character,
        associations=storyline.associations,
    )
    entry.save()
    obj.quests += [entry]
    obj.save()
    return get_template_attribute("manage/_quest.html", "manage")(user, entry)


@manage_endpoint.route("/quest/edit", methods=("POST",))
@manage_endpoint.route("/quest/<string:entrypk>/edit", methods=("POST",))
def edit_quest_entry(entrypk=None):
    user, obj, request_data = _loader()
    entry = Quest.get(entrypk)
    return get_template_attribute("manage/_quest.html", "manage")(user, entry)


@manage_endpoint.route("/quest/update", methods=("POST",))
@manage_endpoint.route("/quest/<string:entrypk>/update", methods=("POST",))
def update_quest_entry(entrypk=None):
    user, obj, request_data = _loader()
    log(request.json)
    quest = Quest.get(entrypk)
    quest.name = request.json.get("name", quest.name)
    quest.description = request.json.get("description", quest.description)
    quest.rewards = request.json.get("rewards", quest.rewards)
    quest.hook = request.json.get("hook", quest.hook)
    quest.summary = request.json.get("summary", quest.summary)
    quest.status = request.json.get("status", quest.status)
    quest.plot_twist = request.json.get("plot_twist", quest.plot_twist)
    quest.antagonist = request.json.get("antagonist", quest.antagonist)
    quest.save()
    return get_template_attribute("manage/_quest.html", "manage")(user, quest)


@manage_endpoint.route("/quest/<string:entrypk>/delete", methods=("POST",))
def delete_quest_entry(entrypk):
    user, obj, request_data = _loader()
    if quest := Quest.get(entrypk):
        quest.delete()
        return "<p>success</p>"
    return "Not found"


@manage_endpoint.route("/quest/search", methods=("POST",))
def quest_search():
    user, obj, request_data = _loader()
    query = request.json.get("query")
    associations = (
        obj.world.search_autocomplete(query) if query and len(query) > 2 else []
    )
    return get_template_attribute("manage/_quest.html", "quest_dropdown")(
        user, obj, associations
    )


@manage_endpoint.route("/quest/entry/association/add", methods=("POST",))
def quest_add_association(entrypk=None):
    user, obj, request_data = _loader()
    entrypk = request.json.get("entrypk")
    if quest := Quest.get(entrypk):
        if association := World.get_model(
            request.json.get("ass_model"), request.json.get("ass_pk")
        ):
            quest.associations += [association]
            quest.save()
        log(association)
    return get_template_attribute("manage/_quest.html", "manage")(user, quest)


@manage_endpoint.route(
    "/quest/<string:questpk>/association/<string:assmodel>/<string:asspk>/remove",
    methods=("POST",),
)
def quest_remove_association(questpk, assmodel, asspk):
    user, obj, request_data = _loader()
    if quest := Quest.get(questpk):
        if association := World.get_model(assmodel, asspk):
            if association in quest.associations:
                quest.associations.remove(association)
                quest.save()
    return get_template_attribute("manage/_quest.html", "manage")(user, quest)


# MARK: Faction routes
###########################################################
##                Faction Routes                    ##
###########################################################
@manage_endpoint.route("/faction/leader/<string:leader_pk>", methods=("POST",))
def factionleader(leader_pk):
    user, obj, request_data = _loader()
    if character := Character.get(leader_pk):
        obj.leader = character
        obj.save()
    return get_template_attribute("models/_faction.html", "info")(user, obj)


# MARK: Encounter routes
###########################################################
##                Encounter Routes                    ##
###########################################################
@manage_endpoint.route("/<string:model>/<string:pk>/add/encounter", methods=("POST",))
@manage_endpoint.route(
    "/<string:model>/<string:pk>/add/encounter/<string:epk>",
    methods=("POST",),
)
def encountercreate(model, pk, epk=None):
    user, place, request_data = _loader()

    if place:
        place.save()
        if place.model_name() not in [
            "Location",
            "City",
            "District",
            "Shop",
            "Vehicle",
            "Region",
        ]:
            raise ValueError(
                "Encounters can only be added to Locations, Cities, District, Shop, Vehicle, or Region"
            )
        encounter = Encounter.get(epk)
        if not encounter:
            encounter = Encounter(world=place.world, parent=place, name="New Encounter")
        encounter.parent = place
        encounter.world = place.world
        if encounter not in place.encounters:
            place.encounters += [encounter]
        encounter.associations = [place]
        encounter.associations += place.associations
        encounter.save()
        log(place.encounters)
        place.save()
        log(place.encounters)
    return get_template_attribute(f"models/_{model.lower()}.html", "gmnotes")(
        user, place
    )


@manage_endpoint.route("/encounter/search", methods=("POST",))
def encountersearch():
    user, obj, request_data = _loader()
    query = request.json.get("query")
    encounters = (
        obj.world.search_autocomplete(query, model="Encounter")
        if query and len(query) > 2
        else []
    )
    url = f"manage/{obj.model_name().lower()}/{obj.pk}/add"
    return get_template_attribute("shared/_dropdown.html", "search_dropdown")(
        user, obj, url, encounters
    )


@manage_endpoint.route("/encounter/toevent", methods=("POST",))
def encountertoevent():
    user, obj, request_data = _loader()
    event = Event.create_event_from_encounter(obj)
    obj.delete()
    return f"""<script>
        window.location.replace('/event/{event.pk}/manage');
    </script>
"""


@manage_endpoint.route("/encounter/story", methods=("POST",))
def encounterstory():
    user, obj, request_data = _loader()
    if story := Story.get(request.json.get("storypk")):
        obj.story = story
        obj.save()
    return get_template_attribute("manage/_encounter.html", "manage")(user, obj)
