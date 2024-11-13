r"""
# World API Documentation

## World Endpoints

### Model Structure

- name: "",
- backstory: "",
- desc: "",
- traits: [str],
- notes: [str],
- regions: [`Region`],
- players: [`Character`],
- player_faction: `Faction`,

"""

from flask import Blueprint, get_template_attribute, request

from autonomous import log
from models.user import User
from models.world import World

from ._utilities import loader as _loader

world_endpoint = Blueprint("world", __name__)


###########################################################
##                    World Routes                       ##
###########################################################
@world_endpoint.route("<string:pk>", methods=("POST",))
def index(pk):
    user, *_ = _loader()
    world = World.get(pk)
    return get_template_attribute("shared/_gm.html", "home")(user, world)


@world_endpoint.route("<string:pk>/delete", methods=("POST",))
def delete(pk):
    user, *_ = _loader()
    if world := World.get(pk):
        world.delete()
    return get_template_attribute("home.html", "home")(user)
