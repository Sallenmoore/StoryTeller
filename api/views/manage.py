r"""
# Management API Documentation
"""

import base64
import json
import os
import random

import markdown
import requests
from bs4 import BeautifulSoup
from dmtoolkit import dmtools
from flask import Blueprint, get_template_attribute, request
from slugify import slugify

from autonomous import log
from models.images.map import Map
from models.journal import JournalEntry
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
    return get_template_attribute("shared/_associations.html", "associations")(
        user, obj, obj.associations
    )


@manage_endpoint.route("/update", methods=("POST",))
def update():
    user, obj, request_data = _loader()
    request_data.pop("user", None)
    request_data.pop("model", None)
    response_url = request_data.pop("response_path", None)
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
    obj.save()
    log(response_url.split("/"))
    path = (
        response_url.split("/")[-1] if len(response_url.split("/")) == 4 else "manage"
    )
    # log(path)
    return get_template_attribute(f"models/_{obj.model_name().lower()}.html", path)(
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
    obj = obj.world.get_model(model, pk)
    world = obj.world
    obj.delete()
    return get_template_attribute("models/_world.html", "history")(user, world)


# MARK: image route
###########################################################
##                    Image Routes                      ##
###########################################################
@manage_endpoint.route("/image", methods=("POST",))
def image():
    user, obj, request_data = _loader()
    return get_template_attribute("shared/_manage.html", "image")(user, obj)


@manage_endpoint.route("/image/gallery", methods=("POST",))
def image_gallery():
    user, obj, request_data = _loader()
    return get_template_attribute("shared/_manage.html", "imagegallery")(
        user, obj, images=obj.get_image_list()
    )


# MARK: map routes
###########################################################
##                      Map Routes                       ##
###########################################################
@manage_endpoint.route("/map", methods=("POST",))
def maps():
    user, obj, request_data = _loader()
    return get_template_attribute("shared/_map.html", "map")(user, obj)


@manage_endpoint.route("/map/gallery", methods=("POST",))
def maps_gallery():
    user, obj, request_data = _loader()
    return get_template_attribute("shared/_map.html", "mapgallery")(
        user, obj, maps=obj.get_map_list()
    )


@manage_endpoint.route(
    "/map/file/upload",
    methods=("POST",),
)
def map_file_upload():
    user, obj, request_data = _loader()
    if "map" not in request_data:
        return {"error": "No map file uploaded"}, 400
    map_file_str = request_data["map"]
    map_file = base64.b64decode(map_file_str)
    obj.map = Map.from_file(map_file)
    obj.save()
    return get_template_attribute("shared/_map.html", "map")(user, obj)


@manage_endpoint.route(
    "<string:pmodel>/<string:ppk>/map/prompt/reset",
    methods=("POST",),
)
def map_prompt_reset(pmodel, ppk):
    user, obj, request_data = _loader()
    obj = World.get_model(pmodel, ppk)
    obj.map_prompt = obj.system.map_prompt(obj)
    obj.map_prompt = (
        markdown.markdown(obj.map_prompt).replace("h1>", "h3>").replace("h2>", "h3>")
    )
    obj.save()
    return get_template_attribute("shared/_map.html", "map")(user, obj)


@manage_endpoint.route(
    "<string:pmodel>/<string:ppk>/map/pois",
    methods=("POST",),
)
def map_pois(pmodel, ppk):
    user, obj, request_data = _loader()
    obj = World.get_model(pmodel, ppk)
    response = []
    for coord in obj.map.coordinates:
        response += [
            {
                "lat": coord.x,
                "lng": coord.y,
                "id": coord.obj.path,
                "name": coord.obj.name,
                "description": coord.obj.description_summary,
                "image": coord.obj.image.url(size=50),
            }
        ]
    return response


@manage_endpoint.route(
    "<string:pmodel>/<string:ppk>/map/poi/add/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def map_poi_add(pmodel, ppk, amodel, apk):
    user, obj, request_data = _loader()
    obj = World.get_model(pmodel, ppk)
    poi = World.get_model(amodel, apk)
    if poi not in obj.associations:
        raise ValueError(
            f"POI {poi} is not an association of {obj}. Please add it first."
        )
    obj.map.add_poi(poi)
    obj.map.save()
    return get_template_attribute("shared/_map.html", "map")(user, obj)


@manage_endpoint.route(
    "<string:pmodel>/<string:ppk>/map/poi/update/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def map_poi_update(pmodel, ppk, amodel, apk):
    user, obj, request_data = _loader()
    obj = World.get_model(pmodel, ppk)
    poi = World.get_model(amodel, apk)
    if poi not in obj.associations:
        raise ValueError(
            f"POI {poi} is not an association of {obj}. Please add it first."
        )
    obj.map.update_poi(poi, request.json.get("lat"), request.json.get("lng"))
    return get_template_attribute("shared/_map.html", "map")(user, obj)


# MARK: journal route
###########################################################
##                    Journal Routes                     ##
###########################################################
@manage_endpoint.route("/journal/entry/edit", methods=("POST",))
@manage_endpoint.route("/journal/entry/edit/<string:entrypk>", methods=("POST",))
def edit_journal_entry(entrypk=None):
    user, obj, request_data = _loader()
    entry = obj.journal.get_entry(entrypk)
    if not entry:
        entry = JournalEntry(title=f"Entry #{len(obj.journal.entries) + 1}")
        entry.save()
        obj.journal.entries.append(entry)
        obj.journal.save()
    return get_template_attribute("shared/_journal.html", "journal_entry")(
        user, obj, entry
    )


@manage_endpoint.route("/journal/entry/update", methods=("POST",))
@manage_endpoint.route("/journal/entry/update/<string:entrypk>", methods=("POST",))
def update_journal_entry(entrypk=None):
    user, obj, request_data = _loader()
    associations = []
    for association in request.json.get("associations", []):
        if obj := World.get_model(association.get("model"), association.get("pk")):
            associations.append(obj)
    kwargs = {
        "title": request.json.get("name"),
        "text": request.json.get("text"),
        "importance": int(request.json.get("importance")),
        "associations": associations,
    }
    entrypk = entrypk or request.json.get("entrypk")
    # log(kwargs)
    entry = obj.journal.update_entry(pk=entrypk, **kwargs)
    return get_template_attribute("shared/_journal.html", "journal_entry")(
        user, obj, entry
    )


@manage_endpoint.route("/journal/entry/delete/<string:entrypk>", methods=("POST",))
def delete_journal_entry(entrypk):
    """
    ## Description
    Deletes the world object's journal entry based on the provided primary keys.
    """
    user, obj, request_data = _loader()
    if entry := obj.journal.get_entry(entrypk):
        obj.journal.entries.remove(entry)
        obj.journal.save()
        entry.delete()
        return "<p>success</p>"
    return "Not found"


@manage_endpoint.route("/journal/search", methods=("POST",))
def journal_search():
    """
    ## Description
    Deletes the world object's journal entry based on the provided primary keys.
    """
    user, obj, request_data = _loader()
    query = request.json.get("query")
    associations = (
        obj.world.search_autocomplete(query) if query and len(query) > 2 else []
    )
    return get_template_attribute("shared/_journal.html", "journal_dropdown")(
        user, obj, associations
    )


@manage_endpoint.route("/journal/entry/association/add", methods=("POST",))
def journal_add_association(entrypk=None):
    user, obj, request_data = _loader()
    entrypk = request.json.get("entrypk")
    if entry := obj.journal.get_entry(entrypk):
        if association := World.get_model(
            request.json.get("ass_model"), request.json.get("ass_pk")
        ):
            entry.associations.append(association)
            entry.save()
    return get_template_attribute("shared/_journal.html", "journal_entry")(
        user, obj, entry
    )


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
    return get_template_attribute("shared/_associations.html", "association_dropdown")(
        user, obj, associations
    )


@manage_endpoint.route("/association/add/<string:amodel>", methods=("POST",))
@manage_endpoint.route(
    "/association/add/<string:amodel>/<string:apk>", methods=("POST",)
)
def association_add(amodel, apk):
    user, obj, request_data = _loader()
    if child := World.get_model(amodel, apk):
        obj.add_association(child)
    params = {
        "user": user,
        "obj": obj,
        "associations": obj.associations,
    }
    return get_template_attribute("shared/_associations.html", "associations")(**params)


@manage_endpoint.route("/associations/random", methods=("POST",))
def association_random():
    user, obj, request_data = _loader()
    log(obj.parent_list)
    if "City" not in obj.parent_list:
        if cities := [o for o in obj.world.cities if o.parent is None]:
            log(cities)
            obj.add_association(random.choice(cities))
    if "District" not in obj.parent_list:
        if districts := [o for o in obj.world.districts if o.parent is None]:
            log(districts)
            obj.add_association(random.choice(districts))
    if "Creature" not in obj.parent_list:
        if creatures := [o for o in obj.world.creatures if o.parent is None]:
            log(creatures)
            obj.add_association(random.choice(creatures))
    if "Item" not in obj.parent_list:
        if items := [o for o in obj.world.items if o.parent is None]:
            log(items)
            obj.add_association(random.choice(items))
    if "Character" not in obj.parent_list:
        if characters := [o for o in obj.world.characters if o.parent is None]:
            log(characters)
            obj.add_association(random.choice(characters))
    if "Faction" not in obj.parent_list:
        if factions := [o for o in obj.world.factions if o.parent is None]:
            log(factions)
            obj.add_association(random.choice(factions))

    params = {
        "user": user,
        "obj": obj,
        "associations": obj.associations,
    }
    return get_template_attribute("shared/_associations.html", "associations")(**params)


@manage_endpoint.route(
    "/unassociate/<string:childmodel>/<string:childpk>", methods=("POST",)
)
def unassociate(childmodel, childpk):
    user, obj, request_data = _loader()
    if child := World.get_model(childmodel).get(childpk):
        associations = obj.remove_association(child)
    else:
        for association in obj.associations:
            if str(association.pk) == childpk:
                obj.remove_association(association)
                break
    associations = obj.associations
    return get_template_attribute("shared/_associations.html", "associations")(
        user, obj, associations=associations
    )


@manage_endpoint.route(
    "/parent/<string:childmodel>/<string:childpk>", methods=("POST",)
)
def parent(childmodel, childpk):
    user, obj, request_data = _loader()
    child = World.get_model(childmodel).get(childpk)
    child.parent = obj
    log(obj.parent == child)
    if obj.parent == child:
        obj.parent = None
        obj.save()
    child.save()
    return get_template_attribute("shared/_associations.html", "associations")(
        user, obj, associations=obj.associations
    )


@manage_endpoint.route("/child/<string:childmodel>/<string:childpk>", methods=("POST",))
def child(childmodel, childpk):
    user, child, request_data = _loader()
    parent = World.get_model(childmodel).get(childpk)
    child.parent = parent
    log(parent.parent == child)
    if parent.parent == child:
        parent.parent = None
        log(parent.parent)
        parent.save()
    log(parent.parent)
    child.save()
    return get_template_attribute("shared/_associations.html", "associations")(
        user, child, associations=child.associations
    )


# MARK: details route
###########################################################
##                    Abilities Routes                   ##
###########################################################


@manage_endpoint.route("/add/listitem/ability", methods=("POST",))
def addability():
    user, obj, request_data = _loader()
    ab = Ability(name="New Ability")
    ab.save()
    obj.abilities += [ab]
    obj.save()
    return get_template_attribute("manage/_details.html", "details")(user, obj)


@manage_endpoint.route("/details/ability/<string:pk>/remove", methods=("POST",))
def removeability(pk):
    if a := Ability.get(pk):
        a.delete()
    return "success"


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


@manage_endpoint.route("/character/<string:pk>/dndbeyond", methods=("POST",))
def dndbeyondapi(pk):
    # log(request.json)
    user = User.get(request.json.pop("user"))
    obj = Character.get(pk)
    results = dmtools.get_dndbeyond_character(obj.dnd_beyond_id)
    log(json.dumps(results, indent=4))
    if results:
        obj.name = results.get("name") or obj.name
        obj.age = results.get("age") or obj.age
        obj.gender = results.get("gender") or obj.gender

        if results.get("inventory"):
            inventory_list = "\n- ".join([i["name"] for i in results.get("inventory")])
            overwritten = False
            for entry in obj.journal.entries:
                if "DnD Beyond Inventory Import" in entry.title:
                    entry.text = inventory_list
                    overwritten = True
                    break
            if not overwritten:
                obj.journal.add_entry(
                    title="DnD Beyond Inventory Import", text=inventory_list
                )
            for item in results.get("inventory"):
                itemobj = Item.find(name=item["name"])
                if not itemobj:
                    itemobj = Item(world=obj.world, name=item["name"], parent=obj)
                    itemobj.save()
                if not itemobj.image:
                    requests.post(
                        f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{itemobj.path}"
                    )
                if itemobj not in obj.associations:
                    obj.add_association(itemobj)
        if features := results.get("features"):
            log(features)
            for feature in features:
                abilityobj = Ability.find(name=feature)
                if not abilityobj:
                    abilityobj = Ability(name=feature)
                    abilityobj.save()
                if abilityobj not in obj.abilities:
                    obj.abilities += [abilityobj]
        obj.archetype = results.get("class_name") or obj.occupation
        obj.hitpoints = results.get("hp") or obj.hitpoints
        obj.strength = results.get("str") or obj.strength
        obj.dexterity = results.get("dex") or obj.dexterity
        obj.constitution = results.get("con") or obj.constitution
        obj.intelligence = results.get("int") or obj.intelligence
        obj.wisdom = results.get("wis") or obj.wisdom
        obj.charisma = results.get("cha") or obj.charisma
        obj.ac = max(int(results.get("ac", 0)) + 10, int(obj.ac))

        # if results.get("wealth"):
        #     for currency, amount in results.get("wealth").items():
        #         currency = f"<h4>{currency.upper()}</h4>"
        #         text = f"{currency}<p>{amount}</p>"
        #         found = False
        #         for idx, w in enumerate(obj.wealth):
        #             if w.strip().startswith(currency):
        #                 found = True
        #                 obj.wealth[idx] = text
        #                 break
        #         if not found:
        #             obj.wealth.append(text)
        # obj.abilities = []
        # features_list = [i for i in results.get("features", [])]
        # for idx, feature in enumerate(features_list):
        #     feature_entry = f"<h5>Feature: {feature.upper()}</h5>"
        #     if feature_desc := dmtools.search_feature(slugify(feature)):
        #         feature_entry += "</p><p>".join(
        #             random.choice(feature_desc).get("desc", "")
        #         )
        #     if feature_entry not in obj.abilities:
        #         obj.abilities.append(feature_entry)
        # spells_list = [i for i in results.get("spells", [])]
        # for idx, spell in enumerate(spells_list):
        #     spell_entry = f"<h5>Feature: {spell.upper()}</h5>"
        #     if spell_desc := dmtools.search_spell(slugify(spell)):
        #         spell_entry += "</p><p>".join(random.choice(spell_desc).get("desc", ""))
        #     if spell_entry not in obj.abilities:
        #         obj.abilities.append(spell_entry)
        obj.save()
    return get_template_attribute("manage/_details.html", "details")(user, obj)


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
