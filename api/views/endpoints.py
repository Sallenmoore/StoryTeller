# Built-In Modules
from datetime import datetime

import requests

# external Modules
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from autonomous.auth.autoauth import AutoAuth
from autonomous.tasks.autotask import AutoTasks
from models.campaign.campaign import Campaign
from models.campaign.episode import Episode, SceneNote
from models.images.image import Image
from models.systems.fantasy import FantasySystem
from models.systems.hardboiled import HardboiledSystem
from models.systems.historical import HistoricalSystem
from models.systems.horror import HorrorSystem
from models.systems.postapocalyptic import PostApocalypticSystem
from models.systems.scifi import SciFiSystem
from models.systems.western import WesternSystem
from models.ttrpgobject.character import Character
from models.ttrpgobject.city import City
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.encounter import Encounter
from models.ttrpgobject.faction import Faction
from models.ttrpgobject.item import Item
from models.ttrpgobject.location import Location
from models.ttrpgobject.region import Region
from models.user import User
from models.world import World

endpoints_endpoint = Blueprint("endpoints", __name__)


@endpoints_endpoint.route("/data", methods=("POST",))
def data():
    # log(AutoAuth.current_user().to_json())
    user = User.get(request.json.get("pk"))
    worlds_data = {}
    for world in user.worlds:
        worlds_data[world.pk] = world.page_data()
    return worlds_data
