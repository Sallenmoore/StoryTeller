from autonomous.auth.autoauth import AutoAuth
from autonomous.model.automodel import AutoModel
from flask import (
    Blueprint,
    get_template_attribute,
)

from autonomous import log
from models.base.actor import Actor
from models.base.place import Place
from models.ttrpgobject.item import Item
from models.utility.foundry_client import FoundryClient
from models.world import World

foundry_page = Blueprint("foundry", __name__)


@foundry_page.route("/<string:world_name>", methods=("GET", "POST"))
def index(world_name):
    try:
        foundry_client = FoundryClient(world_name=world_name)
    except Exception as e:
        log(f"Error initializing FoundryClient: {e}")
        return f"Error: {e}", 500
    return foundry_client.client_id


@foundry_page.route(
    "/<string:world_name>/<string:category_name>", methods=("GET", "POST")
)
def listobjects(world_name, category_name):
    try:
        foundry_client = FoundryClient(world_name=world_name)
    except Exception as e:
        log(f"Error initializing FoundryClient: {e}")
        return f"Error: {e}", 500
    if category_name == "scenes":
        response = foundry_client.get_scenes()
    elif category_name == "actors":
        response = foundry_client.get_actors()
    elif category_name == "items":
        response = foundry_client.get_items()
    else:
        response = {"error": "Invalid category"}
    return response


@foundry_page.route(
    "/push/<string:model_name>/<string:pk>",
    methods=("GET", "POST"),
)
def pushobject(model_name, pk):
    if obj := AutoModel.get_model(model_name, pk):
        try:
            foundry_client = FoundryClient(world_name=obj.world.name)
        except Exception as e:
            log(f"Error initializing FoundryClient: {e}")
            return f"Error: {e}", 500
        if not obj.foundry_client_id:
            obj.foundry_client_id = foundry_client.client_id
            obj.save()
        if isinstance(obj, (World, Place)):
            response = foundry_client.push_scene(obj)
        elif isinstance(obj, Actor):
            response = foundry_client.push_actor(obj)
        elif isinstance(obj, Item):
            response = foundry_client.push_item(obj)
        else:
            response = {"error": "Invalid category"}
        log(response)
        user = AutoAuth.current_user()
        return get_template_attribute(
            f"models/_{obj.model_name().lower()}.html", "gmnotes"
        )(user, obj)
    return {"error": "Object not found"}


@foundry_page.route(
    "/pull/<string:model_name>/<string:pk>",
    methods=("GET", "POST"),
)
def pullobject(model_name, pk):
    if obj := AutoModel.get_model(model_name, pk):
        try:
            foundry_client = FoundryClient(world_name=obj.world.name)
        except Exception as e:
            log(f"Error initializing FoundryClient: {e}")
            return f"Error: {e}", 500
        if not obj.foundry_id:
            return {"error": "Object does not have a Foundry ID"}
        if isinstance(obj, (World, Place)):
            response = foundry_client.get_scene(obj.foundry_id)
        elif isinstance(obj, Actor):
            response = foundry_client.get_actor(obj.foundry_id)
        elif isinstance(obj, Item):
            response = foundry_client.get_item(obj.foundry_id)
        else:
            response = {"error": "Invalid category"}
        log(response)
        user = AutoAuth.current_user()
        return get_template_attribute(
            f"models/_{obj.model_name().lower()}.html", "gmnotes"
        )(user, obj)
    return {"error": "Object not found"}
