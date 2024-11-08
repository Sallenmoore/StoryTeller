import os

from config import Config
from flask import Flask, url_for
from views import (
    admin,
    campaign,
    gmscreen,
    manage,
    nav,
    page,
    search,
    tabletop,
    timeline,
    world,
)

from autonomous import log
from autonomous.auth import AutoAuth
from filters.model import in_list, organize_models
from filters.page import filter_shuffle, roll_dice
from models.user import User


def create_app():
    app = Flask(os.getenv("APP_NAME", __name__))
    app.config.from_object(Config)

    #################################################################
    #                                                        Plug-ins                                      #
    #################################################################

    AutoAuth.user_class = User
    # Configure Filters
    app.jinja_env.filters["organize_models"] = organize_models
    app.jinja_env.filters["in_list"] = in_list
    app.jinja_env.filters["roll_dice"] = roll_dice
    app.jinja_env.filters["filter_shuffle"] = filter_shuffle
    if app.config["DEBUG"]:
        app.jinja_env.add_extension("jinja2.ext.debug")

    ######################################
    #              Routes                #
    ######################################
    @app.route("/favicon.ico")
    def favicon():
        return url_for("static", filename="images/favicon.ico")

    @app.route("/docs", endpoint="docs", methods=("GET", "POST"))
    def docs():
        return {"redirect": os.environ.get("DOC_URL", "#")}

    ######################################
    #           Blueprints               #
    ######################################

    app.register_blueprint(page.page_endpoint, url_prefix="/")
    app.register_blueprint(nav.nav_endpoint, url_prefix="/nav")
    app.register_blueprint(world.world_endpoint, url_prefix="/world")
    app.register_blueprint(manage.manage_endpoint, url_prefix="/manage")
    app.register_blueprint(search.search_endpoint, url_prefix="/search")
    app.register_blueprint(gmscreen.gmscreen_endpoint, url_prefix="/gmscreen")
    app.register_blueprint(campaign.campaign_endpoint, url_prefix="/campaign")
    app.register_blueprint(tabletop.tabletop_endpoint, url_prefix="/tabletop")
    app.register_blueprint(admin.admin_endpoint, url_prefix="/admin")
    app.register_blueprint(timeline.timeline_endpoint, url_prefix="/timeline")
    return app
