"""
app.py - Flask Application Factory

This module defines a Flask application factory for creating the main application
object. It configures various components, such as routes, blueprints, and extensions.

Usage:
1. Import the create_app function.
2. Call create_app() to create the Flask app object.

Example:
    app = create_app()

Functions:
    - create_app: Function to create and configure the Flask app object.

Routes:
    - /favicon.ico: Endpoint to serve the favicon.

Blueprints:
    - The blueprints are registered with the app object, each with its respective
      URL prefix.

Extensions:
    - TBD

Configurations:
    - The app is configured using settings from the Config class.

Note:
    Make sure to set the APP_NAME environment variable to specify the Flask app's name.

"""

import os

from autonomous.auth import AutoAuth
from config import Config
from flask import Flask, json, render_template, request, url_for
from views import (
    auth,
    foundry,
    index,
)
from views.api import (
    admin,
    campaign,
    dungeon,
    endpoints,
    episode,
    event,
    gmscreen,
    lore,
    manage,
    nav,
    story,
    world,
)
from werkzeug.exceptions import HTTPException

from autonomous import log
from filters.forms import label_style
from filters.utils import bonus, get_icon, roll_dice
from models.user import User


def create_app():
    """
    Create and configure the Flask application.

    Returns:
        Flask: The configured Flask app object.
    """
    app = Flask(os.getenv("APP_NAME", __name__))
    app.config.from_object(Config)
    AutoAuth.user_class = User

    # Configure Extensions
    app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024  # 300 MB upload limit
    if app.config["DEBUG"]:
        app.jinja_env.add_extension("jinja2.ext.debug")

    # Configure Filters
    app.jinja_env.filters["roll_dice"] = roll_dice
    app.jinja_env.filters["bonus"] = bonus
    app.jinja_env.filters["label_style"] = label_style
    app.jinja_env.filters["get_icon"] = get_icon

    # Configure Routes
    @app.route("/favicon.ico")
    def favicon():
        """Endpoint to serve the favicon."""
        return url_for("static", filename="images/favicon.ico")

    @app.errorhandler(HTTPException)
    def handle_exception(e):
        emsg = json.dumps(
            {
                "code": e.code,
                "name": e.name,
                "description": e.description,
                "trace": str(e.__traceback__),
            }
        )
        log(f"HTTP Exception: {emsg}")
        # TODO: send email
        return render_template("error.html", url=request.url, error=e)

    ######################################
    #           Blueprints               #
    ######################################
    app.register_blueprint(auth.auth_page, url_prefix="/auth")
    app.register_blueprint(foundry.foundry_page, url_prefix="/foundry")
    app.register_blueprint(index.index_page)

    #### API Blueprints ####
    app.register_blueprint(admin.admin_endpoint, url_prefix="/admin")
    app.register_blueprint(nav.nav_endpoint, url_prefix="/nav")
    app.register_blueprint(manage.manage_endpoint, url_prefix="/manage")
    app.register_blueprint(campaign.campaign_endpoint, url_prefix="/campaign")
    app.register_blueprint(story.story_endpoint, url_prefix="/story")
    app.register_blueprint(gmscreen.gmscreen_endpoint, url_prefix="/gmscreen")
    app.register_blueprint(event.event_endpoint, url_prefix="/event")
    app.register_blueprint(episode.episode_endpoint, url_prefix="/episode")
    app.register_blueprint(endpoints.endpoints_endpoint, url_prefix="/endpoints")
    app.register_blueprint(world.world_endpoint, url_prefix="/world")
    app.register_blueprint(dungeon.dungeon_endpoint, url_prefix="/dungeon")
    app.register_blueprint(lore.lore_endpoint, url_prefix="/lore")

    return app
