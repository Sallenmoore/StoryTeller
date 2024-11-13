# Built-In Modules

# external Modules
import json
import random
from datetime import datetime

from flask import Blueprint, redirect, render_template, request, session, url_for

from autonomous import log
from autonomous.auth import AutoAuth, GoogleAuth
from models.user import User
from models.world import World

auth_page = Blueprint("auth", __name__)


@auth_page.route("/login", methods=("GET", "POST"))
def login():
    log(AutoAuth.current_user().to_json())
    user = AutoAuth.current_user()
    if user.role != "guest":
        if user.last_login:
            log(f"last login: {user.last_login}")
            diff = datetime.now() - user.last_login
            if diff.days <= 30 and AutoAuth.current_user().state == "authenticated":
                log(f"successfully logged in {AutoAuth.current_user().email}")
                return redirect("/home")

    if request.method == "POST":
        authorizer = GoogleAuth()
        session["authprovider"] = "google"
        uri, state = authorizer.authenticate()
        session["authprovider_state"] = state

        return redirect(uri)
    return render_template("index.html", page_url="/auth/login")


@auth_page.route("/authorize", methods=("GET", "POST"))
def authorize():
    authorizer = GoogleAuth()
    response = str(request.url)
    # log(response)
    user_info, token = authorizer.handle_response(
        response, state=request.args.get("state")
    )
    log(user_info)
    if user := User.authenticate(user_info, token):
        session["user"] = user.to_json()
    else:
        session["user"] = None
    log(session["user"])
    return redirect(url_for("auth.login"))


@auth_page.route("/logout", methods=("POST", "GET"))
def logout():
    if session.get("user"):
        try:
            user = User.from_json(session["user"])
            user.state = "unauthenticated"
            log(f"User {user} logged out")
            user.save()
        except Exception as e:
            log(e)
        session.pop("user")

    return redirect(url_for("auth.login"))
