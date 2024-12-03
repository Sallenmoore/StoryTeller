from flask import Blueprint, Response, get_template_attribute, request

from autonomous import log
from models.autogm.autogm import AutoGMScene
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
    if "faction" in request.url or request.json.get("partypk"):
        party = Faction.get(pk or request.json.get("partypk"))
        if gmmode := request.json.get("gmmode"):
            # log(party and party.gm_mode, gmmode)
            if gmmode and party and party.gm_mode != gmmode:
                party.clear_autogm()
                party.gm_mode = gmmode
                party.save()

        party.get_next_scene()
        if party.last_scene:
            log(party.last_scene.player_messages)
    return get_template_attribute("shared/_gm.html", "gm")(user, world, party)


@autogm_endpoint.route("/<string:pk>/intermission", methods=("POST",))
def party_intermission(pk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    return get_template_attribute("shared/_gm.html", "scene_intermission")(
        user, world, party, task_complete=True
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


@autogm_endpoint.route("/<string:pk>/update", methods=("POST",))
@autogm_endpoint.route("/<string:pk>/edit", methods=("POST",))
def scene_update(pk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    if "edit" in request.url:
        return get_template_attribute("shared/_gm.html", "autogm_description_edit")(
            user, world, party
        )
    log(request.json)
    party.next_scene.description = (
        request.json.get("description") or party.next_scene.description
    )
    party.next_scene.scene_type = (
        request.json.get("scene_type") or party.next_scene.scene_type
    )
    party.next_scene.date = request.json.get("date") or party.next_scene.date

    if roll_player := Character.get(request.json.get("pc_roll_player")):
        party.next_scene.roll_required = True
        party.next_scene.roll_player = roll_player
        party.next_scene.roll_attribute = request.json.get("pc_roll_attribute")
        party.next_scene.roll_type = request.json.get("pc_roll_type")
    else:
        party.next_scene.roll_required = False
    party.next_scene.save()
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
    "/party/<string:party>/character/<string:member>/remove", methods=("POST",)
)
def party_remove_character(party, member):
    user, obj, world, *_ = _loader()
    party = Faction.get(party)
    member = Character.get(member)
    party.remove_association(member)
    return get_template_attribute("shared/_gm.html", "autogm_start_session")(
        user, world, party
    )


@autogm_endpoint.route("/<string:pk>/clear", methods=("POST",))
def clearsession(pk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    if party.autogm_summary:
        party.next_scene = party.autogm_summary.pop()
        party.next_scene.player_messages = {}
        party.next_scene.save()
        for ags in party.autogm_summary:
            ags.delete()
        party.autogm_summary = []
        party.save()
    return get_template_attribute("shared/_gm.html", "gm")(user, world, party)
