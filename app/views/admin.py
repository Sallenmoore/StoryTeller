# external Modules
import os

import requests
from autonomous.auth import AutoAuth, auth_required
from flask import Blueprint, get_template_attribute, render_template, request

from autonomous import log
from models.world import World

admin_page = Blueprint("admin", __name__)


@admin_page.route("/", methods=("GET",))
@auth_required(admin=True)
def index():
    return render_template(
        "index.html",
        user=AutoAuth.current_user().pk,
        page_url="/admin/manage",
    )


# @admin_page.route("/manage/images", methods=("GET",))
# # @auth_required(admin=True)
# def images():
#     # url = f"http://api:{os.environ.get('COMM_PORT')}/admin/manage/images"
#     # params = {"user": str(AutoAuth.current_user().pk)}
#     return render_template(
#         "index.html",
#         user=AutoAuth.current_user().pk,
#         page_url="/admin/manage/images",
#     )


# @admin_page.route("/manage/worlds", methods=("GET",))
# # @auth_required(admin=True)
# def worlds():
#     # url = f"http://api:{os.environ.get('COMM_PORT')}/admin/manage/images"
#     # params = {"user": str(AutoAuth.current_user().pk)}
#     return render_template(
#         "index.html",
#         user=AutoAuth.current_user().pk,
#         page_url="/admin/manage/worlds",
#     )


@admin_page.route("/manage/migrate", methods=("POST",))
@auth_required(admin=True)
def migrate():
    for world in World.all():
        for obj in world.associations:
            if obj.image:
                if obj not in obj.image.associations:
                    obj.image.associations += [obj]
                    obj.image.save()
            if hasattr(obj, "map") and obj.map:
                if obj not in obj.map.associations:
                    obj.map.associations += [obj]
                    obj.map.save()
        for obj in world.events:
            if obj.image:
                if obj not in obj.image.associations:
                    obj.image.associations += [obj]
                    obj.image.save()
        for obj in world.stories:
            if obj.image:
                if obj not in obj.image.associations:
                    obj.image.associations += [obj]
                    obj.image.save()
    return "Migration complete"
