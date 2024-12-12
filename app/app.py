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

from config import Config
from flask import Flask, json, render_template, request, url_for
from views.admin import admin_page
from views.auth import auth_page
from views.index import index_page
from filters.utils import roll_dice, bonus
from werkzeug.exceptions import HTTPException

from autonomous import log
from autonomous.auth import AutoAuth
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
    if app.config["DEBUG"]:
        app.jinja_env.add_extension("jinja2.ext.debug")

    # Configure Filters
    app.jinja_env.filters["roll_dice"] = roll_dice
    app.jinja_env.filters["bonus"] = bonus

    # Configure Routes
    @app.route("/favicon.ico")
    def favicon():
        """Endpoint to serve the favicon."""
        return url_for("static", filename="images/favicon.ico")

    @app.errorhandler(HTTPException)
    def handle_exception(e):
        log(
            json.dumps(
                {
                    "code": e.code,
                    "name": e.name,
                    "description": e.description,
                }
            )
        )
        return render_template("error.html", url=request.url, error=e)

    # Register Blueprints
    app.register_blueprint(auth_page, url_prefix="/auth")
    app.register_blueprint(admin_page, url_prefix="/admin")
    app.register_blueprint(index_page)

    return app
