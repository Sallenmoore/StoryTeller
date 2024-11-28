r"""
# Management API Documentation
"""

import random

from bs4 import BeautifulSoup
from dmtoolkit import dmtools
from flask import Blueprint, get_template_attribute, request
from slugify import slugify

from autonomous import log
from models.journal import JournalEntry
from models.ttrpgobject.character import Character
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.item import Item
from models.user import User
from models.world import World

from ._utilities import loader as _loader

manage_endpoint = Blueprint("manage", __name__)


# MARK: update route
###########################################################
##                    Main Route                         ##
###########################################################
@manage_endpoint.route("/<string:model>/<string:pk>", methods=("POST",))
def index(model, pk):
    user, obj, *_ = _loader(model=model, pk=pk)
    return get_template_attribute("manage/_details.html", "details")(user, obj)


# MARK: CRUD routes
###########################################################
##                    CRUD Routes                        ##
###########################################################
@manage_endpoint.route("/add/<string:model>", methods=("POST",))
def add(model):
    user, obj, *_ = _loader()
    new_obj = World.get_model(model)(world=obj.get_world())
    new_obj.save()
    obj.add_association(new_obj)
    return get_template_attribute("shared/_associations.html", "associations")(
        user, obj, obj.associations
    )


@manage_endpoint.route("/update", methods=("POST",))
def update():
    user, obj, world, macro, module = _loader()
    macro = macro or "details"
    module = module or "manage/_details.html"
    request.json.pop("user", None)
    request.json.pop("model", None)
    for attr, value in request.json.items():
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
    return get_template_attribute(module, macro)(user, obj)


@manage_endpoint.route("/delete/<string:model>/<string:pk>", methods=("POST",))
def delete(model, pk):
    user, obj, world, *_ = _loader(model=model, pk=pk)
    obj = world.get_model(model, pk)
    obj.delete()
    return get_template_attribute("shared/_details.html", "details")(user, world)


# MARK: title route
###########################################################
##                    Title Routes                      ##
###########################################################
@manage_endpoint.route("/title", methods=("POST",))
def title():
    user, obj, world, macro, module = _loader(
        module="manage/_title.html", macro="title"
    )
    return get_template_attribute(module, macro)(user, obj)


# MARK: image route
###########################################################
##                    Image Routes                      ##
###########################################################
@manage_endpoint.route("/image", methods=("POST",))
def image():
    user, obj, *_ = _loader()
    return get_template_attribute("manage/_details.html", "image")(user, obj)


@manage_endpoint.route("/image/gallery", methods=("POST",))
def image_gallery():
    user, obj, *_ = _loader()
    return get_template_attribute("manage/_details.html", "imagegallery")(
        user, obj, images=obj.get_image_list()
    )


# MARK: History route
###########################################################
##                    History Routes                      ##
###########################################################
@manage_endpoint.route("/history", methods=("POST",))
def history():
    user, obj, *_ = _loader(module="_manage.html", macro="history")
    return get_template_attribute("manage/_history.html", "history")(user, obj)


# MARK: journal route
###########################################################
##                    Journal Routes                     ##
###########################################################
@manage_endpoint.route("/journal/entry/edit", methods=("POST",))
@manage_endpoint.route("/journal/entry/edit/<string:entrypk>", methods=("POST",))
def edit_journal_entry(entrypk=None):
    user, obj, *_ = _loader()
    entry = obj.journal.get_entry(entrypk)
    if not entry:
        entry = JournalEntry(title=f"Entry #{len(obj.journal.entries)+1}")
        entry.save()
        obj.journal.entries.append(entry)
        obj.journal.save()
    return get_template_attribute("manage/_journal.html", "journal_entry")(
        user, obj, entry
    )


@manage_endpoint.route("/journal/entry/update", methods=("POST",))
@manage_endpoint.route("/journal/entry/update/<string:entrypk>", methods=("POST",))
def update_journal_entry(entrypk=None):
    user, obj, *_ = _loader()
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
    return get_template_attribute("manage/_journal.html", "journal_entry")(
        user, obj, entry
    )


@manage_endpoint.route("/journal/entry/delete/<string:entrypk>", methods=("POST",))
def delete_journal_entry(entrypk):
    """
    ## Description
    Deletes the world object's journal entry based on the provided primary keys.
    """
    user, obj, world, macro, module = _loader()
    if entry := obj.journal.get_entry(entrypk):
        obj.journal.entries.remove(entry)
        obj.journal.save()
        entry.delete()
        return "<p>success</p>"
    return "Not found"


# MARK: Association route
###########################################################
##                 Associations Routes                   ##
###########################################################


@manage_endpoint.route("/association/add/search", methods=("POST",))
def association_search():
    user, obj, world, *_ = _loader()
    query = request.json.get("query")
    associations = world.search_autocomplete(query) if query and len(query) > 2 else []
    return get_template_attribute("shared/_associations.html", "association_dropdown")(
        user, obj, associations
    )


@manage_endpoint.route(
    "/association/add/<string:amodel>/<string:apk>", methods=("POST",)
)
def association_add(amodel, apk):
    user, obj, *_ = _loader()
    child = World.get_model(amodel, apk)
    child.add_association(obj)
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
    user, obj, *_ = _loader()
    child = World.get_model(childmodel).get(childpk)
    associations = obj.remove_association(child)
    return get_template_attribute("shared/_associations.html", "associations")(
        user, obj, associations=associations
    )


# MARK: details route
###########################################################
##                    Details Routes                     ##
###########################################################
@manage_endpoint.route("/details", methods=("POST",))
def details():
    user, obj, *_ = _loader()
    info = get_template_attribute(
        f"models/_{obj.model_name().lower()}.html", "manage_details"
    )
    response = get_template_attribute("manage/_details.html", "details")(
        user, obj, info
    )
    return response


@manage_endpoint.route("/details/add/listitem/<string:attr>", methods=("POST",))
def addlistitem(attr):
    user, obj, *_ = _loader()
    if isinstance(getattr(obj, attr, None), list):
        getattr(obj, attr).append("New Entry")
        obj.save()
    result = get_template_attribute("shared/_form.html", "listeditor")(user, obj, attr)
    # log(attr, elemid, result)
    return result


# MARK: scene routes
###########################################################
##                    Scene Routes                       ##
###########################################################
@manage_endpoint.route(
    "/scenes/<string:connectedmodel>/<string:connectedpk>", methods=("POST",)
)
def scenes(connectedmodel, connectedpk):
    user, obj, *_ = _loader()
    connect_obj = World.get_model(connectedmodel, connectedpk)
    obj.add_scene(connect_obj)
    # log([d.obj.name for d in obj.scenes if d])
    params = {
        "user": user,
        "obj": obj,
        "associations": obj.get_associations(),
    }
    return get_template_attribute("shared/_associations.html", "associations")(**params)


# MARK: Character routes
###########################################################
##                Character Routes                    ##
###########################################################
@manage_endpoint.route("/character/lineage/<string:pk>", methods=("POST",))
def characterlineage(pk):
    user, obj, world, macro, module = _loader()
    character = Character.get(pk)
    if macro == "lineage_form":
        obj = character
    elif request.json.get("relationship"):
        obj.add_lineage(character, request.json.get("relationship"))
    return get_template_attribute("models/_character.html", macro)(user, obj)


@manage_endpoint.route("/character/lineage/remove/<string:pk>", methods=("POST",))
def removecharacterlineage(pk):
    user, obj, world, macro, module = _loader()
    character = Character.get(pk)
    obj.remove_lineage(character)
    return "<p>Success</p>"


@manage_endpoint.route("/character/hitpoints", methods=("POST",))
def characterhitpoints():
    user, obj, world, macro, module = _loader()
    obj.current_hitpoints = int(request.json.get("current_hitpoints", obj.hitpoints))
    obj.save()
    return get_template_attribute("models/_character.html", "info")(user, obj)


@manage_endpoint.route("/character/dndbeyond", methods=("POST",))
def dndbeyondapi():
    log(request.json)
    user = User.get(request.json.pop("user"))
    obj = Character.get(request.json.pop("pk"))
    results = dmtools.get_dndbeyond_character(obj.dnd_beyond_id)
    if results:
        obj.name = results.get("name") or obj.name
        obj.age = results.get("age") or obj.age
        obj.gender = results.get("gender") or obj.gender
        if results.get("desc") not in obj.desc:
            obj.desc += (
                f"\n\n***From DndBeyond Description: \n{results.get('desc', obj.desc)}"
            )
        if results.get("backstory"):
            overwritten = False
            for entry in obj.journal.entries:
                if "DnD Beyond Backstory Import" in entry.title:
                    entry.text = results.get("backstory")
                    overwritten = True
                    break
            if not overwritten:
                obj.journal.add_entry(
                    title="DnD Beyond Backstory Import", text=results.get("backstory")
                )
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
                if item := Item.find(name=item["name"]):
                    if not any(i for i in obj.items if i.name == item.name):
                        copy_item = item.copy()
                        obj.items.append(copy_item)
        obj.race = results.get("race") or obj.race
        obj.occupation = results.get("class_name") or obj.occupation
        obj.hitpoints = results.get("hp") or obj.hitpoints
        obj.strength = results.get("str") or obj.strength
        obj.dexterity = results.get("dex") or obj.dexterity
        obj.constitution = results.get("con") or obj.constitution
        obj.intelligence = results.get("int") or obj.intelligence
        obj.wisdom = results.get("wis") or obj.wisdom
        obj.charisma = results.get("cha") or obj.charisma
        obj.ac = max(int(results.get("ac", 0)), int(obj.ac))

        if results.get("wealth"):
            for currency, amount in results.get("wealth").items():
                currency = f"<h4>{currency.upper()}</h4>"
                text = f"{currency}<p>{amount}</p>"
                found = False
                for idx, w in enumerate(obj.wealth):
                    if w.strip().startswith(currency):
                        found = True
                        obj.wealth[idx] = text
                        break
                if not found:
                    obj.wealth.append(text)
        obj.abilities = []
        features_list = [i for i in results.get("features", [])]
        for idx, feature in enumerate(features_list):
            feature_entry = f"<h5>Feature: {feature.upper()}</h5>"
            if feature_desc := dmtools.search_feature(slugify(feature)):
                feature_entry += "</p><p>".join(
                    random.choice(feature_desc).get("desc", "")
                )
            if feature_entry not in obj.abilities:
                obj.abilities.append(feature_entry)
        spells_list = [i for i in results.get("spells", [])]
        for idx, spell in enumerate(spells_list):
            spell_entry = f"<h5>Feature: {spell.upper()}</h5>"
            if spell_desc := dmtools.search_spell(slugify(spell)):
                spell_entry += "</p><p>".join(random.choice(spell_desc).get("desc", ""))
            if spell_entry not in obj.abilities:
                obj.abilities.append(spell_entry)
        obj.save()
    return get_template_attribute("models/_character.html", "manage_details")(user, obj)


# MARK: Faction routes
###########################################################
##                Faction Routes                    ##
###########################################################
@manage_endpoint.route("/faction/leader/<string:leader_pk>", methods=("POST",))
def factionleader(leader_pk):
    user, obj, *_ = _loader()
    if character := Character.get(leader_pk):
        obj.leader = character
        obj.save()
    return get_template_attribute("models/_faction.html", "info")(user, obj)
