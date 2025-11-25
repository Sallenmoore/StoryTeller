import os

from autonomous.auth import AutoAuth
from config import Config
from flask import Flask, url_for
from views import (
    admin,
    campaign,
    endpoints,
    episode,
    event,
    gmscreen,
    index,
    manage,
    nav,
    story,
    world,
)

from autonomous import log
from filters.forms import label_style
from filters.utils import bonus, roll_dice
from models.user import User


def create_app():
    app = Flask(os.getenv("APP_NAME", __name__))
    app.config.from_object(Config)

    #################################################################
    #                                                        Plug-ins                                      #
    #################################################################

    AutoAuth.user_class = User
    # Configure Filters
    app.jinja_env.filters["roll_dice"] = roll_dice
    app.jinja_env.filters["bonus"] = bonus
    app.jinja_env.filters["label_style"] = label_style

    if app.config["DEBUG"]:
        app.jinja_env.add_extension("jinja2.ext.debug")

    app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024  # 300 MB upload limit

    ######################################
    #              Routes                #
    ######################################
    @app.route("/favicon.ico")
    def favicon():
        return url_for("static", filename="images/favicon.ico")

    ######################################
    #           Blueprints               #
    ######################################
    app.register_blueprint(admin.admin_endpoint, url_prefix="/admin")
    app.register_blueprint(nav.nav_endpoint, url_prefix="/nav")
    app.register_blueprint(manage.manage_endpoint, url_prefix="/manage")
    app.register_blueprint(index.index_endpoint, url_prefix="/")
    app.register_blueprint(campaign.campaign_endpoint, url_prefix="/campaign")
    app.register_blueprint(story.story_endpoint, url_prefix="/story")
    app.register_blueprint(gmscreen.gmscreen_endpoint, url_prefix="/gmscreen")
    app.register_blueprint(event.event_endpoint, url_prefix="/event")
    app.register_blueprint(episode.episode_endpoint, url_prefix="/episode")
    app.register_blueprint(endpoints.endpoints_endpoint, url_prefix="/endpoints")
    app.register_blueprint(world.world_endpoint, url_prefix="/world")
    return app
