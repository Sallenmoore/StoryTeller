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
@auth_required()
def index():
    return render_template("home.html", user=AutoAuth.current_user())


@index_page.route("/<string:model>/<string:pk>", methods=("GET", "POST"))
@index_page.route("/<string:model>/<string:pk>/<path:page>", methods=("GET", "POST"))
@auth_required(guest=True)
def page(model, pk, page="details"):
    # log(page)
    user = AutoAuth.current_user()
    if page.startswith("manage/"):
        obj = World.get_model(model, pk)
        url = f"/api/{page}"
    elif page == "frompoi":
        if poi := World.get_model("POI", pk):
            obj = poi.get_location()
            poi.delete()
            url = f"/api/location/{obj.pk}/details"
    else:
        obj = World.get_model(model, pk)
        url = f"/api/{model}/{pk}/{page}"
    session["model"] = model
    session["pk"] = pk
    session["page"] = page
    log(url)
    return render_template("page.html", user=user, obj=obj, page_url=url)


@index_page.route("/<string:model>/<string:pk>/card", methods=("GET", "POST"))
@auth_required(guest=True)
def card(model, pk, page="history"):
    user = AutoAuth.current_user()
    obj = World.get_model(model, pk)
    return render_template("card.html", user=user, obj=obj)


@index_page.route("/map/<string:campaignpk>", methods=("GET", "POST"))
def map(campaignpk):
    campaign = Campaign.get(campaignpk)
    log(campaignpk, campaign)
    episode = campaign.current_episode
    scene = episode.current_scene
    if not scene.music:
        scene.music = "static/sounds/music/themesong.mp3"
    log(episode, scene, scene.map.url())
    return render_template("map.html", episode=episode, scene=scene)


@index_page.route("/map/<string:campaignpk>/update", methods=("GET", "POST"))
def mapdata(campaignpk):
    campaign = Campaign.get(campaignpk)
    log(campaignpk, campaign)
    episode = campaign.current_episode
    scene = episode.current_scene
    result = (
        requests.get(
            f"http://api:5000/tabletop/{episode.pk}/scene/{scene.pk}/data"
        ).json()
        if scene
        else {}
    )
    return result


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
    url = f"http://api:5000/{rest_path}"
    response = "<p>You do not have permission to alter this object<p>"
    # log(request.method)
    user = AutoAuth.current_user()
    if request.method == "GET":
        args = {}
        for key, value in dict(request.args.lists()).items():
            if len(value) == 1:
                args[key] = value[0]
            elif len(value) > 1:
                args[key] = value
        # log(url, args)
        response = requests.post(url, json=args).text
    elif not user.is_guest:
        # log(rest_path, request.json)
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
        response = requests.post(f"http://tasks:5000/{rest_path}", json=request.json)
        # log(response.text)
    return response.text
