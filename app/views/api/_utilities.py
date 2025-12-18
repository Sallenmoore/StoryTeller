import base64

from autonomous.auth import AutoAuth, auth_required
from autonomous.model.automodel import AutoModel
from flask import request, session

from autonomous import log
from models.user import User
from models.world import World


def authenticate(user, obj):
    if obj and user in obj.world.users:
        return True
    return False


def loader(model=None, pk=None):
    # log(f"User: {user}, Model: {model}, PK: {pk}")
    # log(f"Request: {request}")
    if request.method == "GET":
        request_data = request.args
        # log(f"get request: {request_data}")
    elif request.method == "POST":
        if request.files:
            request_data = dict(request.form)
            for key, file in request.files.items():
                request_data[key] = base64.b64encode(file.read()).decode("utf-8")
        else:
            request_data = dict(request.json)
        # log(f"post: {request_data}")
    user = AutoAuth.current_user()
    # log(user)
    # get obj
    try:
        model = model or request_data.get("model", session.get("model", None))
        pk = pk or request_data.get("pk", session.get("pk", None))
        obj = AutoModel.get_model(model, pk)
    except Exception as e:
        log(f"Error getting model: {e}")
        obj = None
    else:
        session["model"] = model
        session["pk"] = pk
    # log(obj)
    return user, obj, request_data
