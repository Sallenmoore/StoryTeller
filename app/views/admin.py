# external Modules
import os

import requests
from autonomous.auth import AutoAuth, auth_required
from autonomous.tasks.autotask import AutoTasks
from flask import Blueprint, get_template_attribute, render_template, request

from autonomous import log
from models.campaign.campaign import Campaign
from models.campaign.episode import Episode
from models.world import World

admin_page = Blueprint("admin", __name__)


@admin_page.route("/manage", methods=("GET",))
# @auth_required(admin=True)
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
# @auth_required(admin=True)
def migrate():
    # task = (
    #     AutoTasks()
    #     .task(
    #         migrate_task,
    #     )
    #     .result
    # )
    return "success"


# def migrate_task():
#     results = requests.get(
#         f"https://storyteller.stevenamoore.dev/data/world/6764552d82587e6d53d86794",
#     ).json()
#     log(results["campaigns"])
#     for campaign_data in results["campaigns"]:
#         campaign = Campaign.get(campaign_data["pk"])
#         campaign.description = campaign_data["description"]
#         if campaign.name == "The Unholy Trinity":
#             for episode_data in campaign_data["episodes"]:
#                 try:
#                     if episode := Episode.get(episode_data["pk"]) or Episode.search(
#                         campaign=campaign, name=episode_data["name"]
#                     ).pop(0):
#                         episode.name = episode_data["name"] or episode.name
#                         episode.loot = episode_data["loot"] or episode.loot
#                         episode.hooks = episode_data["hooks"] or episode.hooks
#                         episode.episode_report = (
#                             episode_data["episode_report"] or episode.episode_report
#                         )
#                         episode.associations = []
#                         for model_name, pk in episode_data["associations"]:
#                             if obj := World.get_model(model_name, pk):
#                                 episode.add_association(obj)
#                         episode.save()
#                         log(
#                             f"Saved Episode: {campaign.name, episode.episode_num, episode.name}",
#                             _print=True,
#                         )
#                 except IndexError as e:
#                     log(f"Error with episode: {episode_data['name']}, {e}", _print=True)
#             campaign.save()
#     return "Migration complete"
