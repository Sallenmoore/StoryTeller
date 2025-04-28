# external Modules
import requests
from flask import Blueprint, get_template_attribute, render_template, request

from autonomous import log
from autonomous.auth import AutoAuth, auth_required

admin_page = Blueprint("admin", __name__)


@admin_page.route("/", methods=("GET",))
# @auth_required(admin=True)
def index():
    log("admin index")
    pc = requests.post("http://api:5000/admin/manage").text
    return render_template(
        "index.html",
        user=AutoAuth.current_user().pk,
        page_content=pc,
    )


@admin_page.route("/images", methods=("GET", "POST"))
@auth_required(admin=True)
def images():
    args = request.args.copy()
    if request.method == "POST":
        args.update(request.json)
    # log(args)
    pc = requests.post("http://api:5000/admin/manage/images", json=args).text
    return render_template(
        "admin/index.html",
        user=AutoAuth.current_user().pk,
        page_content=pc,
    )


@admin_page.route("/worlds", methods=("GET", "POST"))
@auth_required(admin=True)
def worlds():
    args = request.args.copy()
    if request.method == "POST":
        args.update(request.json)
    # log(args)
    pc = requests.post("http://api:5000/admin/manage/worlds", json=args).text
    return render_template(
        "admin/index.html",
        user=AutoAuth.current_user().pk,
        page_content=pc,
    )


@admin_page.route("/users", methods=("GET", "POST"))
@auth_required(admin=True)
def users():
    args = request.args.copy()
    if request.method == "POST":
        args.update(request.json)
    # log(args)
    pc = requests.post("http://api:5000/admin/manage/users", json=args).text
    return render_template(
        "admin/index.html",
        user=AutoAuth.current_user().pk,
        page_content=pc,
    )


@admin_page.route("/agents", methods=("GET", "POST"))
# @auth_required(admin=True)
def agents():
    args = request.args.copy()
    if request.method == "POST":
        args.update(request.json)
    # log(args)
    pc = requests.post("http://api:5000/admin/manage/agents", json=args).text
    return pc
