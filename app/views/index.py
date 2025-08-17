import io
import json
import os

import requests
from flask import (
    Blueprint,
    Response,
    render_template,
    request,
    session,
)

from autonomous import log
from autonomous.auth import AutoAuth, auth_required
from models.gmscreen.gmscreen import GMScreen  # required import for model loading
from models.images.image import Image
from models.ttrpgobject.faction import Faction  # required import for model loading
from models.world import World

index_page = Blueprint("index", __name__)


def _authenticate(user, obj):
    if user in obj.get_world().users:
        return True
    return False


# def update_with_session(requestdata):
#     # log(requestdata)
#     args = requestdata.copy()
#     args["scenepk"] = requestdata.get("scenepk") or session.get("scenepk")
#     return args


@index_page.route("/", endpoint="index", methods=("GET", "POST"))
@index_page.route("/home", endpoint="index", methods=("GET", "POST"))
@auth_required()
def index():
    user = AutoAuth.current_user()
    session["page"] = "/home"
    return render_template("index.html", user=user, page_url="/home")


@index_page.route("/test", endpoint="test", methods=("GET", "POST"))
@auth_required()
def indextest():
    user = AutoAuth.current_user()
    session["page"] = "/test"
    return render_template("index-test.html", user=user, page_url="/test")


@index_page.route(
    "/image/<string:pk>/<string:size>",
    methods=("GET",),
)
def image(pk, size):
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
def audio(model, pk):
    obj = World.get_model(model, pk)
    log(hasattr(obj, "audio"), obj.audio)
    if hasattr(obj, "audio") and obj.audio:
        return Response(
            obj.audio.read(),
            mimetype="audio/mpeg",
            headers={"Content-Disposition": f"inline; filename={pk}.mp3"},
        )
    else:
        return Response("No audio available", status=404)


@index_page.route(
    "/manage/<string:model>/<string:pk>",
    methods=(
        "GET",
        "POST",
    ),
)
@auth_required()
def manage(model, pk):
    user = AutoAuth.current_user()
    obj = World.get_model(model, pk)
    content = "<p>You do not have permission to alter this object<p>"
    if _authenticate(user, obj):
        args = request.json if request.method == "POST" else dict(request.args)
        args["user"] = str(user.pk)
        content = requests.post(
            f"http://api:{os.environ.get('COMM_PORT')}/manage/{model}/{pk}", json=args
        ).text
    return render_template("index.html", user=user, obj=obj, page_content=content)


@index_page.route("/<string:model>/<string:pk>", methods=("GET", "POST"))
@index_page.route("/<string:model>/<string:pk>/<path:page>", methods=("GET", "POST"))
@auth_required(guest=True)
def page(model, pk, page=""):
    user = AutoAuth.current_user()
    session["page"] = f"/{model}/{pk}/{page or 'info'}"
    if obj := World.get_model(model, pk):
        session["model"] = model
        session["pk"] = pk
    return render_template("index.html", user=user, obj=obj, page_url=session["page"])


@index_page.route(
    "/api/<path:rest_path>",
    endpoint="api",
    methods=(
        "GET",
        "POST",
    ),
)
# @auth_required(guest=True)
def api(rest_path):
    url = f"http://api:{os.environ.get('COMM_PORT')}/{rest_path}"
    response = "<p>You do not have permission to alter this object<p>"
    user = AutoAuth.current_user()
    if request.method == "GET":
        rest_path = request.path.replace("/api/", "")
        params = dict(request.args)
        params["user"] = user.pk
        url = f"http://api:{os.environ.get('COMM_PORT')}/{rest_path}?{requests.compat.urlencode(params)}"
        log("API GET REQUEST", url)
        response = requests.get(url).text
    elif not user.is_guest:
        log("API POST REQUEST", rest_path, request.json)
        if "admin/" in url and user.is_admin:
            response = requests.post(url, json=request.json).text
        elif request.json.get("model") and request.json.get("pk"):
            obj = World.get_model(request.json.get("model"), request.json.get("pk"))
            if _authenticate(user, obj):
                response = requests.post(url, json=request.json).text
        else:
            response = requests.post(url, json=request.json).text
    # log(response)
    return response


@index_page.route("/task/<path:rest_path>", endpoint="tasks", methods=("POST",))
@auth_required()
def tasks(rest_path):
    # log("TASK REQUEST", request.files, request.form, _print=True)
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
        obj = World.get_model(metadata.get("model")).get(metadata.get("pk"))
        if _authenticate(user, obj):
            log("Sending files:", files, metadata, _print=True)
            response = requests.post(
                f"http://tasks:{os.environ.get('COMM_PORT')}/{rest_path}",
                files=files,
                data={
                    "model": metadata.get("model"),
                    "pk": metadata.get("pk"),
                    "user": str(user.pk),
                },
            )
    else:
        user = AutoAuth.current_user()
        obj = World.get_model(request.json.get("model")).get(request.json.get("pk"))
        if _authenticate(user, obj):
            response = requests.post(
                f"http://tasks:{os.environ.get('COMM_PORT')}/{rest_path}",
                json=request.json,
            )
    return response.text


# MARK: Data routes
###########################################################
##                    Data        Routes                 ##
###########################################################
@index_page.route(
    "/<pk>/list/<string:model>",
    methods=("GET", "POST"),
)
def listobjs(pk, model):
    world = World.get(pk)
    objs = World.get_model(model).search(world=world)
    result = []
    for obj in objs:
        objs_dict = json.loads(obj.to_json())
        result += [objs_dict]
        log(objs_dict)
    return result


@index_page.route(
    "/data/<string:model>/<pk>",
    methods=("GET", "POST"),
)
def getobjs(pk, model):
    obj = World.get_model(model, pk)
    return obj.page_data()
