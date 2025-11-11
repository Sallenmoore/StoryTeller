import base64
import io
import json
import os
from urllib.parse import urlparse

import requests
from autonomous.auth import AutoAuth, auth_required
from autonomous.model.automodel import AutoModel
from flask import (
    Blueprint,
    Response,
    render_template,
    request,
    session,
)

from autonomous import log
from models.campaign.campaign import Campaign
from models.gmscreen.gmscreen import GMScreen  # required import for model loading
from models.images.image import Image
from models.stories.event import Event
from models.ttrpgobject.faction import Faction  # required import for model loading
from models.world import World

index_page = Blueprint("index", __name__)


def _authenticate(user, obj):
    if user in obj.world.users:
        return True
    return False


@index_page.route("/", endpoint="index", methods=("GET", "POST"))
@index_page.route("/home", endpoint="index", methods=("GET", "POST"))
@auth_required()
def index():
    user = AutoAuth.current_user()
    session["page"] = "/home"
    return render_template("index.html", user=user, page_url="/home")


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
    return render_template("index.html", user=user, obj=obj, page_url=session["page"])


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


@index_page.route(
    "/audio/<string:model>/<string:pk>",
    methods=("GET",),
)
@index_page.route(
    "/audio/<string:model>/<string:pk>/<string:attrib>",
    methods=("GET",),
)
def audio(model, pk, attrib=None):
    attrib = attrib or "audio"
    obj = AutoModel.get_model(model, pk)
    log(hasattr(obj, attrib), getattr(obj, attrib))
    if hasattr(obj, attrib) and getattr(obj, attrib):
        return Response(
            getattr(obj, attrib).read(),
            mimetype="audio/mpeg",
            headers={"Content-Disposition": f"inline; filename={pk}.mp3"},
        )
    else:
        return Response("No audio available", status=404)


@index_page.route(
    "/api/<path:rest_path>",
    endpoint="api",
    methods=(
        "GET",
        "POST",
    ),
)
def api(rest_path):
    url = f"http://{os.environ.get('API_SERVICE_NAME')}:{os.environ.get('COMM_PORT')}/{rest_path}"
    response = "<p>You do not have permission to alter this object<p>"
    user = AutoAuth.current_user()
    response_url = urlparse(request.referrer).path
    if request.method == "GET":
        params = dict(request.args)
        params["user"] = user.pk
        params["response_path"] = response_url
        url = f"http://{os.environ.get('API_SERVICE_NAME')}:{os.environ.get('COMM_PORT')}/{rest_path}?{requests.compat.urlencode(params)}"
        log("API GET REQUEST", url)
        response = requests.get(url).text
    elif not user.is_guest:
        params = {}
        if request.files:
            params = dict(request.form)
            for key, file in request.files.items():
                params[key] = base64.b64encode(file.read()).decode("utf-8")
        elif request.json:
            params = dict(request.json)
        params["response_path"] = response_url
        params |= {"user": str(AutoAuth.current_user().pk)}
        log(url, params)
        if params.get("model") and params.get("pk"):
            obj = AutoModel.get_model(params.get("model"), params.get("pk"))
            if _authenticate(user, obj.world):
                response = requests.post(url, json=params).text
        else:
            response = requests.post(url, json=params).text
    # log(response)
    return response


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


# MARK: Data routes
###########################################################
##                    Data        Routes                 ##
###########################################################
@index_page.route(
    "/data/list/<string:model>",
    methods=("GET", "POST"),
)
def listobjs(model):
    objs = World.get_model(model).all()
    result = []
    for obj in objs:
        objs_dict = json.loads(obj.to_json())
        result += [objs_dict]
        log(objs_dict)
    return result


@index_page.route(
    "/<string:model>/<pk>/data",
    methods=("GET", "POST"),
)
def obj_data(pk, model):
    obj = World.get_model(model, pk)
    return obj.page_data()


@index_page.route(
    "/<string:model>/<pk>/data/foundry",
    methods=("GET", "POST"),
)
def foundry_export(pk, model):
    obj = World.get_model(model, pk)
    log(obj.foundry_export())
    return obj.foundry_export()
