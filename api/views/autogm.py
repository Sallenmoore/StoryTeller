import json

from dmtoolkit import dmtools
from flask import Blueprint, Response, get_template_attribute, request

from autonomous import log
from models.autogm.autogm import AutoGMScene
from models.autogm.autogmquest import AutoGMQuest
from models.base.place import Place
from models.ttrpgobject.character import Character
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
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
    party = None
    if party := Faction.get(pk or request.json.get("partypk")):
        next_scene = party.get_next_scene()
        gmmode = request.json.get("gmmode")
        if gmmode and next_scene.gm_mode != gmmode:
            next_scene.gm_mode = gmmode
            next_scene.save()
        log(
            f"Party: {party}, Next Scene: {next_scene}, GM Mode: {next_scene.gm_mode}, Party Session History: {party.autogm_summary}"
        )
    return get_template_attribute("shared/_gm.html", "gm")(user, world, party)


@autogm_endpoint.route("/<string:pk>/intermission", methods=("POST",))
def party_intermission(pk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    return get_template_attribute("shared/_gm.html", "scene_intermission")(
        user, world, party, task_complete=True
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
            if not party.next_scene
            or (party.next_scene and w not in party.next_scene.associations)
        ]
    return get_template_attribute("shared/_gm.html", "autogm_association_search")(
        user, party, objs
    )


@autogm_endpoint.route(
    "/<string:pk>/associations/add/<string:amodel>/<string:apk>", methods=("POST",)
)
@autogm_endpoint.route(
    "/<string:pk>/scene/add/<string:amodel>/<string:apk>", methods=("POST",)
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
        party.next_scene.add_association(ass)
        if "scene" in request.url:
            if amodel == "character":
                party.next_scene.npcs += [ass]
            elif amodel == "item":
                party.next_scene.loot += [ass]
            elif amodel == "creature":
                party.next_scene.combatants += [ass]
            elif amodel in ["region", "city", "district", "location"]:
                party.next_scene.places += [ass]
            party.next_scene.save()
    return get_template_attribute("shared/_gm.html", "gm")(user, world, party)


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
            elif (
                amodel in ["region", "city", "district", "location"]
                and ass in party.next_scene.places
            ):
                party.next_scene.places.remove(ass)
        else:
            party.next_scene.remove_association(ass)
        party.next_scene.save()
    return get_template_attribute("shared/_gm.html", "gm")(user, world, party)


@autogm_endpoint.route("/<string:pk>/edit", methods=("POST",))
def scene_edit(pk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    return get_template_attribute("shared/_gm.html", "autogm_description_edit")(
        user, world, party
    )


@autogm_endpoint.route("/<string:pk>/update", methods=("POST",))
def scene_update(pk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)

    if desc := request.json.get("description"):
        party.next_scene.description = desc

    if scene_type := request.json.get("scene_type"):
        party.next_scene.scene_type = scene_type

    if date := request.json.get("date"):
        party.next_scene.date = date

    if message := request.json.get("message"):
        party.next_scene.set_player_message(
            message["playerpk"],
            response=message["player_message"],
            intention=message["intentions"],
            emotion=message["emotion"],
        )

    if request.json.get("pc_roll_num_dice"):
        party.next_scene.roll_required = True
        party.next_scene.roll_player = Character.get(request.json.get("pc_roll_player"))
        party.next_scene.roll_attribute = request.json.get("pc_roll_attribute")
        party.next_scene.roll_type = request.json.get("pc_roll_type")
        party.next_scene.roll_formula = f"{request.json.get("pc_roll_num_dice")}d{request.json.get("pc_roll_type_dice")}{request.json.get("pc_roll_modifier")}"
        party.next_scene.roll_result = dmtools.dice_roll(party.next_scene.roll_formula)
    else:
        party.next_scene.roll_required = False
    party.next_scene.save()
    # log(json.dumps(json.loads(party.next_scene.to_json()), indent=4))
    return get_template_attribute("shared/_gm.html", "gm")(user, world, party)


@autogm_endpoint.route(
    "/party/<string:partypk>/quest",
    methods=("POST",),
)
@autogm_endpoint.route(
    "/party/<string:partypk>/quest/current/<string:pk>",
    methods=("POST",),
)
def autogm_party_current_quest(partypk, pk=None):
    user, obj, world, *_ = _loader()
    party = Faction.get(partypk)
    if party and pk:
        for quest in party.next_scene.quest_log:
            if str(quest.pk) == pk:
                party.next_scene.current_quest = quest
                party.next_scene.save()

    return get_template_attribute("shared/_gm.html", "scene_quest_log")(
        user, world, party
    )


@autogm_endpoint.route(
    "/party/<string:partypk>/quest/delete/<string:pk>",
    methods=("POST",),
)
def autogm_party_quest_delete(partypk, pk=None):
    user, obj, world, *_ = _loader()
    party = Faction.get(partypk)
    quest = AutoGMQuest.get(pk)
    if quest in party.next_scene.quest_log:
        party.next_scene.quest_log.remove(quest)
        quest.delete()
        party.next_scene.save()
    return get_template_attribute("shared/_gm.html", "gm")(user, world)


@autogm_endpoint.route("/<string:pk>/canonize", methods=("POST",))
def canonizesession(pk):
    user, obj, world, *_ = _loader()
    if party := Faction.get(pk):
        party.end_gm_session()
    return get_template_attribute("shared/_gm.html", "gm")(user, world)


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
    return get_template_attribute("shared/_gm.html", "gm")(user, world)
