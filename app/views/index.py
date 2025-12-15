import json
import os

import requests
from autonomous.auth import AutoAuth, auth_required
from autonomous.model.automodel import AutoModel
from flask import (
    Blueprint,
    Response,
    get_template_attribute,
    render_template,
    request,
    session,
)

from autonomous import log
from models.audio.audio import Audio
from models.campaign.campaign import Campaign
from models.gmscreen.gmscreen import GMScreen  # required import for model loading
from models.images.image import Image
from models.stories.event import Event
from models.ttrpgobject.faction import Faction  # required import for model loading
from models.world import World

index_page = Blueprint("index", __name__)


def _authenticate(user, obj):
    if obj and user in obj.world.users:
        return True
    return False


@index_page.route("/", endpoint="index", methods=("GET", "POST"))
@index_page.route("/home", endpoint="index", methods=("GET", "POST"))
@auth_required()
def index():
    user = AutoAuth.current_user()
    session["page"] = "/home"
    page = get_template_attribute("home.html", "home")(user)
    return render_template("index.html", user=user, page=page)


@index_page.route("/<string:model>/<string:pk>", methods=("GET", "POST"))
@index_page.route("/<string:model>/<string:pk>/<path:page>", methods=("GET", "POST"))
@auth_required(guest=True)
def page(model, pk, page=""):
    user = AutoAuth.current_user()
    session["page"] = f"/{model}/{pk}{'/' + page if page else ''}"
    if obj := AutoModel.get_model(model, pk):
        session["model"] = model
        session["pk"] = pk
    if "manage" in page and not _authenticate(user, obj):
        return "<p>You do not have permission to manage this object<p>"
    page = get_template_attribute(f"models/_{model}.html", page or "index")(user, obj)

    return render_template("index.html", user=user, obj=obj, page=page)


# MARK: Association routes
###########################################################
##                    Association Routes                 ##
###########################################################
@index_page.route("/<string:model>/<string:pk>/associations", methods=("GET", "POST"))
def associations(model, pk):
    user = AutoAuth.current_user()
    obj = AutoModel.get_model(model, pk)
    associations = obj.associations
    if request.method == "POST":
        if filter_str := request.json.get("filter"):
            if len(filter_str) > 2:
                associations = [
                    o for o in associations if filter_str.lower() in o.name.lower()
                ]
        if type_str := request.json.get("type"):
            associations = [
                o for o in associations if o.model_name().lower() == type_str.lower()
            ]
        if rel_str := request.json.get("relationship"):
            if rel_str.lower() == "parent":
                associations = [o for o in associations if o in obj.geneology]
            elif rel_str.lower() == "child":
                associations = [o for o in associations if obj == o.parent]
            elif hasattr(obj, "lineage") and rel_str.lower() == "lineage":
                associations = [o for o in associations if o in obj.lineage]
        if sort_str := request.json.get("sorter"):
            order = request.json.get("order", "ascending")
            if sort_str.lower() == "name":
                associations.sort(
                    key=lambda x: x.name, reverse=True
                ) if order == "descending" else associations
            elif sort_str.lower() == "date":
                associations = [
                    a for a in associations if a.end_date and a.end_date.year > 0
                ]
                associations.sort(
                    key=lambda x: x.end_date, reverse=True
                ) if order == "descending" else associations.sort(
                    key=lambda x: x.end_date
                )
            elif sort_str.lower() == "type":
                associations.sort(
                    key=lambda x: x.model_name(), reverse=True
                ) if order == "descending" else associations.sort(
                    key=lambda x: x.model_name()
                )
    if hasattr(obj, "split_associations"):
        relations, associations = obj.split_associations(associations=associations)
    else:
        relations = []
    page = get_template_attribute(f"models/_{model}.html", "associations")(
        user, obj, extended_associations=associations, direct_associations=relations
    )
    return render_template("index.html", user=user, obj=obj, page=page)


# MARK: Association routes
###########################################################
##                    Media Routes                       ##
###########################################################
@index_page.route(
    "/image/<string:pk>/<string:size>",
    methods=("GET",),
)
@index_page.route(
    "/image/<string:pk>",
    methods=("GET",),
)
def image(pk, size="orig"):
    img = Image.get(pk)
    if img and img.data:
        img_data = img.resize(size) if size != "orig" else img.read()
        # log(img_data)
        return Response(
            img_data,
            mimetype=img.data.content_type,
            headers={"Content-Disposition": f"inline; filename={img.pk}.webp"},
        )
    else:
        return Response("No image available", status=404)


@index_page.route("/audio/<string:pk>", methods=("GET",))
def audio(pk):
    if audio := Audio.get(pk):
        return Response(
            audio.read(),
            mimetype="audio/mpeg",
            headers={"Content-Disposition": f"inline; filename={pk}.mp3"},
        )
    else:
        return Response("No audio available", status=404)


# MARK: Association routes
###########################################################
##                    Task Routes                        ##
###########################################################


@index_page.route("/task/<path:rest_path>", endpoint="tasks", methods=("POST",))
@auth_required()
def tasks(rest_path):
    log("TASK REQUEST", rest_path, request.json, _print=True)
    if request.files:
        files = {}
        for key, file in request.files.items():
            audio_content = file.read()
            files |= {
                key: (
                    file.filename,
                    audio_content,
                    file.mimetype,
                )
            }
        metadata_str = request.form.get("metadata")
        metadata = json.loads(metadata_str)
        user = AutoAuth.current_user(metadata.get("user"))
        obj = AutoModel.get_model(metadata.get("model")).get(metadata.get("pk"))
        if _authenticate(user, obj):
            log("Sending files:", files, metadata, _print=True)
            response = requests.post(
                f"http://{os.environ.get('TASKS_SERVICE_NAME')}:{os.environ.get('COMM_PORT')}/{rest_path}",
                files=files,
                data={
                    "model": metadata.get("model"),
                    "pk": metadata.get("pk"),
                    "user": str(user.pk),
                },
            )
    else:
        user = AutoAuth.current_user()
        obj = AutoModel.get_model(request.json.get("model")).get(request.json.get("pk"))
        if _authenticate(user, obj):
            response = requests.post(
                f"http://{os.environ.get('TASKS_SERVICE_NAME')}:{os.environ.get('COMM_PORT')}/{rest_path}",
                json=request.json,
            )
    return response.text
