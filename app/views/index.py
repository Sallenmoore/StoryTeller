import os

import requests
from flask import (
    Blueprint,
    render_template,
    request,
    session,
)

from autonomous import log
from autonomous.auth import AutoAuth, auth_required
from models.campaign import Campaign
from models.world import World

index_page = Blueprint("index", __name__)


def _authenticate(user, obj):
    if user == obj.get_world().user or obj.get_world() in user.worlds:
        return True
    return False


# def update_with_session(requestdata):
#     # log(requestdata)
#     args = requestdata.copy()
#     args["campaignpk"] = requestdata.get("campaignpk") or session.get("campaignpk")
#     args["sessionpk"] = requestdata.get("sessionpk") or session.get("sessionpk")
#     args["scenepk"] = requestdata.get("scenepk") or session.get("scenepk")
#     return args


@index_page.route("/", endpoint="index", methods=("GET",))
@index_page.route("/<string:model>/<string:pk>", methods=("GET", "POST"))
@index_page.route("/<string:model>/<string:pk>/<path:page>", methods=("GET", "POST"))
@auth_required(guest=True)
def index(model=None, pk=None, page=""):
    user = AutoAuth.current_user()
    session["page"] = f"/{page}" if page else session.get("page", "/home")
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
    # log(request.method)
    user = AutoAuth.current_user()
    if request.method == "GET":
        log(rest_path)
        response = requests.get(url).text
    elif not user.is_guest:
        log(rest_path, request.json)
        if "admin/" in url and user.is_admin:
            response = requests.post(url, json=request.json).text
        elif request.json.get("model") and request.json.get("pk"):
            obj = World.get_model(request.json.get("model"), request.json.get("pk"))
            # log(obj)
            if _authenticate(user, obj):
                response = requests.post(url, json=request.json).text
    # log(response)
    return response


@index_page.route("/task/<path:rest_path>", endpoint="tasks", methods=("POST",))
@auth_required()
def tasks(rest_path):
    user = AutoAuth.current_user()
    obj = World.get_model(request.json.get("model")).get(request.json.get("pk"))
    if _authenticate(user, obj):
        log(request.json)
        response = requests.post(
            f"http://tasks:{os.environ.get('COMM_PORT')}/{rest_path}", json=request.json
        )
        # log(response.text)
    return response.text
