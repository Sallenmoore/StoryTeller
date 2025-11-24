# external Modules
import os

import requests
from autonomous.auth import AutoAuth, auth_required
from autonomous.tasks.autotask import AutoTasks
from flask import Blueprint, get_template_attribute, render_template, request

from autonomous import log
from models.base.actor import Actor
from models.campaign.campaign import Campaign
from models.campaign.episode import Episode
from models.stories.lore import Lore
from models.ttrpgobject.ability import Ability
from models.ttrpgobject.character import Character
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.item import Item
from models.ttrpgobject.vehicle import Vehicle
from models.world import World

admin_page = Blueprint("admin", __name__)


@admin_page.route("/manage", methods=("GET",))  #
# @auth_required(admin=True)
def index():
    return render_template(
        "index.html",
        user=AutoAuth.current_user().pk,
        page_url="/admin/manage",
    )


@admin_page.route("/manage/migrate", methods=("POST",))
# @auth_required(admin=True)
def migrate():
    # worlds = World.all()
    # for world in worlds:
    #     objs = [
    #         *Character.search(world=world),
    #         *Creature.search(world=world),
    #         *Item.search(world=world),
    #         *Vehicle.search(world=world),
    #     ]
    #     for obj in objs:
    #         for a in obj.abilities:
    #             if not a.world or a.world != world:
    #                 a.world = world
    #                 a.save()
    #                 log(f"Updated Ability {a.name} for {world.name}")

    # orphan_abilities = Ability.search(world=None)
    # log(f"Found {len(orphan_abilities)} orphan abilities")
    # for a in orphan_abilities:
    #     log(
    #         f"Deleted orphan ability {a.name} with world {a.world.name if a.world else 'None'} and description: \n{a.description}"
    #     )
    #     a.delete()
    return "success"
