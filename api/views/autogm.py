import os

import markdown
import requests
from dmtoolkit import dmtools
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from models.autogm.autogminitiative import AutoGMInitiative
from models.autogm.autogmquest import AutoGMQuest
from models.base.place import Place
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
    if party and party.next_scene:
        # party.next_scene.is_ready = False
        # party.next_scene.save()
        log(
            party.name,
            party.next_scene.gm_mode,
            [p.ready for p in party.next_scene.player_messages],
            party.is_ready(),
            party.next_scene.scene_objects(),
        )
        # return get_template_attribute(
        #     f"autogm/_{party.next_scene.gm_mode}.html", "autogm_session"
        # )(user, world, party)
    return get_template_attribute("autogm/_shared.html", "autogm_3d")(
        user, world, party
    )


@autogm_endpoint.route("/<string:pk>/start", methods=("POST",))
def start(pk=None):
    user, obj, world, *_ = _loader()
    party = None
    if party := Faction.get(pk):
        party.get_next_scene()

        if gmmode := request.json.get("gmmode"):
            party.next_scene.gm_mode = gmmode

        if tone := request.json.get("tone"):
            party.next_scene.tone = tone.title()

        if scenario := request.json.get("scenario"):
            party.next_scene.description = markdown.markdown(scenario)
        party.next_scene.is_ready = False
        party.next_scene.gm_ready = True
        party.next_scene.save()
    return requests.post(
        f"http://tasks:{os.environ.get('COMM_PORT')}/generate/autogm/{party.pk}"
    ).text


@autogm_endpoint.route("/<string:pk>/canonize", methods=("POST",))
def canonizesession(pk):
    user, obj, world, *_ = _loader()
    if party := Faction.get(pk):
        party.end_gm_session()
    return get_template_attribute(
        f"autogm/_{party.next_scene.gm_mode}.html", "autogm_session"
    )(user, world, party)


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
    return get_template_attribute(
        f"autogm/_{party.next_scene.gm_mode}.html", "autogm_session"
    )(user, world, party)


## MARK: Submission
###########################################################
##                   Submission Routes                   ##
###########################################################
@autogm_endpoint.route("/<string:pk>/submit", methods=("POST",))
def submit(pk=None):
    party = Faction.get(pk)
    if party.next_scene.gm_mode == "pc":
        pass
    elif party.next_scene.gm_mode == "gm":
        pass
    elif party.next_scene.gm_mode == "manual":
        party.next_scene.gm_ready = True
        party.next_scene.save()
    return requests.post(
        f"http://tasks:{os.environ.get('COMM_PORT')}/generate/autogm/{pk}"
    ).text


@autogm_endpoint.route("/<string:pk>/<string:playerpk>/ready", methods=("POST",))
def ready(pk, playerpk):
    party = Faction.get(pk)
    player = Character.get(playerpk)
    party.next_scene.get_player_message(player).ready = bool(request.json.get("ready"))
    party.next_scene.get_player_message(player).save()
    log(
        [p.ready for p in party.next_scene.player_messages],
        party.is_ready(),
        party.next_scene.scene_objects(),
    )
    if party.next_scene.gm_ready and party.ready:
        return requests.post(
            f"http://tasks:{os.environ.get('COMM_PORT')}/generate/autogm/{party.pk}"
        ).text
    else:
        return get_template_attribute(
            f"autogm/_{party.next_scene.gm_mode}.html", "autogm_session"
        )(party.user, party.world, party)


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


@autogm_endpoint.route("/<string:pk>/update", methods=("POST",))
def scene_update(pk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    log(request.json)
    if desc := request.json.get("description"):
        party.next_scene.description = markdown.markdown(desc)

    if scene_type := request.json.get("scene_type"):
        party.next_scene.scene_type = scene_type

    if date := request.json.get("date"):
        party.next_scene.date = date
        party.next_scene.save()

    if quest := request.json.get("quest"):
        quest_obj = AutoGMQuest.get(quest["pk"])
        name = quest["name"]
        type = quest["type"]
        description = quest["description"]
        status = quest["status"]
        next_steps = quest["next_steps"]
        importance = quest["importance"]
        quest_obj.save()

    if message := request.json.get("message"):
        party.next_scene.set_player_message(
            message["playerpk"],
            response=message["player_message"],
            intent=message["intentions"],
            emotion=message["emotion"],
            ready=bool(message.get("ready")),
        )

    if next_actions := request.json.get("next_actions"):
        party.next_scene.next_actions = [na for na in next_actions if na.strip()]
        log(party.next_scene.next_actions)

    if request.json.get("pc_roll_player"):
        party.next_scene.roll_required = True
        party.next_scene.roll_player = Character.get(request.json.get("pc_roll_player"))
        party.next_scene.roll_attribute = request.json.get("pc_roll_attribute")
        party.next_scene.roll_type = request.json.get("pc_roll_type")
    elif (
        party.next_scene.roll_required
        and request.json.get("pc_roll_num_dice")
        and request.json.get("pc_roll_type_dice")
        and request.json.get("pc_roll_modifier")
    ):
        party.next_scene.roll_formula = f"{request.json.get("pc_roll_num_dice")}d{request.json.get("pc_roll_type_dice")}{request.json.get("pc_roll_modifier")}"
        party.next_scene.roll_result = dmtools.dice_roll(party.next_scene.roll_formula)
    party.next_scene.save()
    # log(
    #     [p.ready for p in party.next_scene.player_messages],
    #     party.is_ready(),
    #     party.next_scene.gm_ready,
    # )
    return get_template_attribute(
        f"autogm/_{party.next_scene.gm_mode}.html", "autogm_session"
    )(user, world, party)


@autogm_endpoint.route("/<string:pk>/combat/update", methods=("POST",))
def combatupdate(pk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    if not party.last_scene.initiative:
        raise ValueError("No Initiative List")
    hp = request.json.get("hp")
    status = request.json.get("status")
    action = request.json.get("action-description")
    bonus_action = request.json.get("bonus_action")
    movement = request.json.get("movement")
    action_target = request.json.get("action_target")
    action_attack_roll = request.json.get("action_attack_roll")
    action_dmg_roll = request.json.get("action_dmg_roll")
    action_saving_throw = request.json.get("action_saving_throw")
    action_skill_check = request.json.get("action_skill_check")
    bonus_action_target = request.json.get("bonus_action_target")
    bonus_action_attack_roll = request.json.get("bonus_action_attack_roll")
    bonus_action_dmg_roll = request.json.get("bonus_action_dmg_roll")
    bonus_action_saving_throw = request.json.get("bonus_action_saving_throw")
    bonus_action_skill_check = request.json.get("bonus_action_skill_check")
    if atarget := Character.get(action_target) or Creature.get(action_target):
        if action_attack_roll >= atarget.ac:
            atarget.current_hitpoints -= int(action_dmg_roll) if action_dmg_roll else 0
        atarget.save()
    if atarget := Character.get(bonus_action_target) or Creature.get(
        bonus_action_target
    ):
        if bonus_action_attack_roll >= atarget.ac:
            atarget.current_hitpoints -= (
                int(bonus_action_dmg_roll) if bonus_action_dmg_roll else 0
            )
        atarget.save()
    party.last_scene.current_combat_turn(
        hp=hp,
        status=status,
        action=action,
        bonus_action=bonus_action,
        movement=movement,
        action_target=action_target,
        action_attack_roll=action_attack_roll,
        action_dmg_roll=action_dmg_roll,
        action_saving_throw=action_saving_throw,
        action_skill_check=action_skill_check,
        bonus_action_target=bonus_action_target,
        bonus_action_attack_roll=bonus_action_attack_roll,
        bonus_action_dmg_roll=bonus_action_dmg_roll,
        bonus_action_saving_throw=bonus_action_saving_throw,
        bonus_action_skill_check=bonus_action_skill_check,
    )
    return get_template_attribute(
        f"autogm/_{party.next_scene.gm_mode}.html", "autogm_session"
    )(user, world, party)


@autogm_endpoint.route(
    "/<string:pk>/<string:playerpk>/current_hitpoints", methods=("POST",)
)
def autogm_player_current_hp(pk, playerpk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    player = Character.get(playerpk)
    if player:
        player.current_hitpoints = int(request.json.get("current_hitpoints"))
        player.save()
    return get_template_attribute(
        f"autogm/_{party.next_scene.gm_mode}.html", "autogm_session"
    )(user, world, party)


@autogm_endpoint.route("/<string:pk>/mode", methods=("POST",))
def mode(pk=None):
    user, obj, world, *_ = _loader()
    party = None
    if party := Faction.get(pk):
        next_scene = party.get_next_scene()
        next_scene.gm_mode = request.json.get("gmmode")
        next_scene.save()
    return get_template_attribute(
        f"autogm/_{party.next_scene.gm_mode}.html", "autogm_session"
    )(user, world, party)


@autogm_endpoint.route("/<string:pk>/status/<string:actorpk>", methods=("POST",))
def playerstatus(pk, actorpk):
    user, obj, world, *_ = _loader()
    party = Faction.get(pk)
    if not party.last_scene.initiative:
        raise ValueError("No Initiative List")
    if ini := AutoGMInitiative.get(actorpk):
        ini.status = request.json.get("status")
        ini.save()
    return get_template_attribute(
        f"autogm/_{party.next_scene.gm_mode}.html", "autogm_session"
    )(user, world, party)


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
    return get_template_attribute(
        f"autogm/_{party.next_scene.gm_mode}.html", "autogm_association_search"
    )(user, party, objs)


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
            elif amodel == "vehicle":
                party.next_scene.vehicles += [ass]
            elif amodel == "creature":
                party.next_scene.combatants += [ass]
            elif amodel == "faction":
                party.next_scene.factions += [ass]
            elif amodel in ["region", "city", "district", "location"]:
                party.next_scene.places += [ass]
            party.next_scene.save()
    return get_template_attribute(
        f"autogm/_{party.next_scene.gm_mode}.html", "autogm_session"
    )(user, world, party)


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
    return get_template_attribute(
        f"autogm/_{party.next_scene.gm_mode}.html", "autogm_session"
    )(user, world, party)


# MARK: Quests
###########################################################
##              Quest       Routes                       ##
###########################################################
@autogm_endpoint.route(
    "/<string:partypk>/quest",
    methods=("POST",),
)
@autogm_endpoint.route(
    "/<string:partypk>/quest/current/<string:pk>",
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

    return get_template_attribute(
        f"autogm/_{party.next_scene.gm_mode}.html", "scene_quest_log"
    )(user, world, party)


@autogm_endpoint.route(
    "/<string:partypk>/quest/add",
    methods=("POST",),
)
def autogm_party_quest_add(partypk):
    user, obj, world, *_ = _loader()
    party = Faction.get(partypk)
    """
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    """
    quest = AutoGMQuest(name="New Quest", associations=[party, *party.players])
    quest.save()
    party.next_scene.quest_log += [quest]
    party.next_scene.save()
    return get_template_attribute(
        f"autogm/_{party.next_scene.gm_mode}.html", "autogm_session"
    )(user, world, party)


@autogm_endpoint.route(
    "/<string:partypk>/quest/delete/<string:pk>",
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
    return get_template_attribute(
        f"autogm/_{party.next_scene.gm_mode}.html", "autogm_session"
    )(user, world, party)
