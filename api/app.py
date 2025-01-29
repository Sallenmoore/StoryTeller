import os

from config import Config
from flask import Flask, url_for
from views import admin, campaign, index, manage, nav, gmscreen

from autonomous import log
from autonomous.auth import AutoAuth
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
    if app.config["DEBUG"]:
        app.jinja_env.add_extension("jinja2.ext.debug")

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
    app.register_blueprint(gmscreen.gmscreen_endpoint, url_prefix="/gmscreen")
    return app
