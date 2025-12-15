from autonomous.auth import AutoAuth, auth_required
from autonomous.model.automodel import AutoModel
from flask import request, session

from autonomous import log
from models.user import User
from models.world import World


def loader():
    # log(f"User: {user}, Model: {model}, PK: {pk}")
    # log(f"Request: {request}")
    if request.method == "GET":
        request_data = request.args
        # log(f"get request: {request_data}")
    elif request.method == "POST":
        request_data = request.json
        # log(f"post: {request_data}")
    user = AutoAuth.current_user()
    # log(user)
    # get obj
    try:
        obj = AutoModel.get_model(session.get("model", None), session.get("pk", None))
    except Exception as e:
        log(f"Error getting model: {e}")
        obj = None
    # log(obj)
    return user, obj, request_data
