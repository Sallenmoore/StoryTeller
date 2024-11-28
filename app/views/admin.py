# external Modules
import requests
from flask import Blueprint, get_template_attribute, render_template, request

from autonomous import log
from autonomous.auth import AutoAuth, auth_required

admin_page = Blueprint("admin", __name__)


@admin_page.route("/", methods=("GET",))
@auth_required(admin=True)
def index():
    return render_template(
        "admin/index.html",
        user=AutoAuth.current_user().pk,
    )


@admin_page.route("/images", methods=("GET", "POST"))
@auth_required(admin=True)
def images():
    args = request.args.copy()
    if request.method == "POST":
        args.update(request.json)
    log(args)
    pc = requests.post("http://api:5000/admin/manage/images", json=args).text
    return render_template(
        "admin/index.html",
        user=AutoAuth.current_user().pk,
        page_content=pc,
    )


@admin_page.route("/pullfromworld", methods=("GET", "POST"))
@auth_required(admin=True)
def pull():
    world_data = requests.get("http://dev.world.stevenamoore.dev/raw/worlds").text
    worlds = []
    for world in world_data:
        pass
    return render_template("admin/index.html")
