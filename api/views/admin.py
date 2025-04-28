# Built-In Modules
import glob
import os
import subprocess
from datetime import datetime

import requests

# external Modules
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from autonomous.auth.autoauth import AutoAuth
from autonomous.tasks.autotask import AutoTasks
from models.calendar.date import Date
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

admin_endpoint = Blueprint("admin", __name__)

tags = {
    "type": [
        "episode",
        "battlemaps",
        "map",
        "world",
        "region",
        "city",
        "location",
        "encounter",
        "district",
        "faction",
        "creature",
        "shop",
        "item",
        "character",
    ],
    "genre": ["fantasy", "horror", "sci-fi", "western", "historical"],
}
tag_list = sorted([*tags["type"], *tags["genre"]])


@admin_endpoint.route("/manage", methods=("POST",))
def index():
    return get_template_attribute("admin/_index.html", "manage")()


@admin_endpoint.route("/manage/images", methods=("POST",))
def images():
    if request.json.get("scan"):
        Image.storage_scan()
    images = Image.all()
    if tag_filter := request.json.get("tag"):
        # log(tag_filter)
        if tag_filter == "_NoGenre":
            images = [
                img for img in images if not any(t in img.tags for t in tags["genre"])
            ]
        elif tag_filter == "_NoType":
            images = [
                img for img in images if not any(t in img.tags for t in tags["type"])
            ]
        elif tag_filter == "_Missing":
            images = [img for img in images if not any(t in img.tags for t in tag_list)]
        else:
            images = [img for img in images if tag_filter.lower() in img.tags]
    return get_template_attribute("admin/_images.html", "manage")(
        images=images, tags=tag_list, tag=tag_filter
    )


@admin_endpoint.route("/manage/image/<string:pk>", methods=("POST",))
def add_image_tag(pk):
    img = Image.get(pk)
    new_tag = request.json.get("new_tag")
    if img and new_tag:
        img.add_tag(new_tag)
        img.save()
    return images()


@admin_endpoint.route("/manage/image/<string:pk>/delete", methods=("POST",))
def delete_image(pk):
    img = Image.get(pk)
    if img:
        img.delete()
        # log(f"Image {pk} deleted")
        return "Success"
    # log(f"Image {pk} not found")
    return "File not found"


@admin_endpoint.route("/manage/image/<string:pk>/tag/remove", methods=("POST",))
def remove_image_tag(pk):
    img = Image.get(pk)
    tag = request.json.get("tag")
    if img and tag:
        img.remove_tag(tag)
        img.save()
        return "Success"
    return "World not found"


@admin_endpoint.route("/manage/users", methods=("POST",))
def users():
    return get_template_attribute("admin/_users.html", "manage")(users=User.all())


@admin_endpoint.route("/manage/users/role", methods=("POST",))
def role_user():
    if user := User.get(request.json.get("user")):
        user.role = request.json.get("role")
        user.save()
        return "Success"
    return "User not found"


@admin_endpoint.route("/manage/users/delete", methods=("POST",))
def delete_user():
    if user := User.get(request.json.get("user")):
        user.delete()
        return "Success"
    return "User not found"


@admin_endpoint.route("/manage/worlds", methods=("POST",))
def worlds():
    return get_template_attribute("admin/_worlds.html", "manage")(worlds=World.all())


@admin_endpoint.route("/manage/users/delete", methods=("POST",))
def delete_world():
    if world := World.get(request.json.get("world")):
        world.delete()
        return "Success"
    return "World not found"


@admin_endpoint.route("/manage/agents", methods=("POST",))
def agents():
    return get_template_attribute("admin/_agents.html", "manage")(worlds=World.all())


@admin_endpoint.route("/manage/agents/delete", methods=("POST",))
def delete_agents():
    from autonomous.ai.baseagent import clear_agents

    result = clear_agents()
    return "Success"


@admin_endpoint.route("/migration/data", methods=("GET", "POST"))
def migration():
    for obj in Campaign.all():
        for ep in obj.episodes:
            if not ep.campaign:
                ep.campaign = obj
            if not ep.start_date.calendar:
                ep.start_date.calendar = obj.world.calendar
                ep.start_date.save()
            if not ep.end_date.calendar:
                ep.end_date.calendar = obj.world.calendar
                ep.end_date.save()
    # for obj in Episode.all():
    #     if not obj.campaign:
    #         obj.delete()

    return "Success"


@admin_endpoint.route("/dbdump", methods=("POST",))
def dbdump():
    dev = int(os.environ.get("DEBUG") or os.environ.get("TESTING"))
    # log(
    #     os.environ.get("DEBUG"),
    #     os.environ.get("TESTING"),
    #     dev,
    #     type(dev),
    #     not dev,
    # )
    log("starting dump...")
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", 27017)
    password = os.getenv("DB_PASSWORD")
    username = os.getenv("DB_USERNAME")
    connect_str = f"mongodb://{username}:{password}@{host}:{port}"
    datetime_string = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    command_str = f'mongodump --uri="{connect_str}" --archive="dbbackups/dbbackup-{datetime_string}.archive"'
    result = subprocess.Popen(command_str, shell=True).wait()
    log(result)
    return "<p>Success</p>"


@admin_endpoint.route("/dbload", methods=("POST",))
def dbload():
    log("starting load...")
    files = glob.glob(
        "dbbackups/dbbackup-*.archive"
    )  # replace with your directory path
    # Find the file with the most recent timestamp
    latest_file = max(files, key=os.path.getctime)
    # log(latest_file)
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", 27017)
    password = os.getenv("DB_PASSWORD")
    username = os.getenv("DB_USERNAME")
    connect_str = f"mongodb://{username}:{password}@{host}:{port}"
    log("Flushing and Restoring DB...")
    command_str = f'mongorestore -v --drop --noIndexRestore --uri="{connect_str}" --archive="{latest_file}"'
    result = subprocess.Popen(command_str, shell=True).wait()
    log(command_str, result)
    return "<p>Success</p>"
