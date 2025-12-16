# Built-In Modules

# external Modules
import json
import random
from datetime import datetime

from autonomous.auth import AutoAuth, GoogleAuth
from flask import (
    Blueprint,
    get_template_attribute,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from autonomous import log
from models.user import User
from models.world import World

auth_page = Blueprint("auth", __name__)


@auth_page.route("/login", methods=("GET", "POST"))
def login():
    # log(AutoAuth.current_user().to_json())
    user = AutoAuth.current_user()
    if user.role != "guest":
        if user.last_login:
            # f"last login: {user.last_login}")
            diff = datetime.now() - user.last_login
            if diff.days <= 30 and AutoAuth.current_user().state == "authenticated":
                # log(f"successfully logged in {AutoAuth.current_user().email}")
                return redirect("/home")

    if request.method == "POST":
        authorizer = GoogleAuth()
        session["authprovider"] = "google"
        uri, state = authorizer.authenticate()
        session["authprovider_state"] = state

        return redirect(uri)
    worlds = World.all()
    worlds = random.sample(worlds, 4) if len(worlds) > 4 else worlds
    page = get_template_attribute("login.html", "login")(worlds=worlds)
    return render_template("index.html", page=page)


@auth_page.route("/authorize", methods=("GET", "POST"))
def authorize():
    authorizer = GoogleAuth()
    response = str(request.url)
    # log(response)
    user_info, token = authorizer.handle_response(
        response, state=request.args.get("state")
    )
    # log(user_info)
    if user := User.authenticate(user_info, token):
        session["user"] = user.to_json()
    else:
        session["user"] = None
    # log(session["user"])
    return redirect(url_for("auth.login"))


@auth_page.route("/logout", methods=("POST", "GET"))
def logout():
    if user := AutoAuth.current_user():
        if user.state == "guest":
            return redirect(url_for("auth.login"))

        try:
            user.state = "unauthenticated"
            # log(f"User {user} logged out")
            user.save()
        except Exception as e:
            log(e)
        session.pop("user")

    return redirect(url_for("auth.login"))
