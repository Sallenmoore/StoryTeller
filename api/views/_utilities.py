from flask import request

from autonomous import log
from models.user import User
from models.world import World


def loader(
    user=None,
    model=None,
    pk=None,
    macro=None,
    module=None,
):
    # log(f"User: {user}, Model: {model}, PK: {pk}")
    # get user
    if request.method == "GET":
        request_data = request.args
    elif request.method == "POST":
        request_data = request.json
    else:
        request_data = None

    if not user:
        user_data = request_data.get("user", None)
        user = (
            User.get(user_data["pk"])
            if isinstance(user_data, dict) and user_data.get("pk")
            else User.get(user_data)
        )
    else:
        user = User.get(user)

    # get obj
    obj = World.get_model(
        model or request_data.get("model", None), pk or request_data.get("pk", None)
    )

    # get world

    world = obj.get_world() if obj else None
    macro = macro or request_data.get("macro", None)
    module = module or request_data.get("module", None)
    return user, obj, world, macro, module
