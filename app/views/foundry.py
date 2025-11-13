import base64
import io
import json
import os
from urllib.parse import urlparse

import requests
from autonomous.model.automodel import AutoModel
from flask import (
    Blueprint,
    Response,
    render_template,
    request,
    session,
)

from autonomous import log
from models.images.image import Image
from models.utility.foundry_client import FoundryClient
from models.world import World

foundry_page = Blueprint("foundry", __name__)


@foundry_page.route("/<string:world_name>", methods=("GET", "POST"))
def index(world_name):
    foundry_client = FoundryClient(world_name=world_name)
    return foundry_client.client_id


@foundry_page.route(
    "/<string:world_name>/get/<string:category_name>", methods=("GET", "POST")
)
def get(world_name, category_name):
    foundry_client = FoundryClient(world_name=world_name)
    # /get?clientId=$clientId&selected=true&actor=true
    if category_name == "scenes":
        response = foundry_client.get_world_scenes()
    elif category_name == "actors":
        response = foundry_client.get_world_actors()
    elif category_name == "items":
        response = foundry_client.get_world_items()
    else:
        response = {"error": "Invalid category"}
    return response
