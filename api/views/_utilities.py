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
    if not user:
        user_data = request.json.pop("user", None)
        user = (
            User.get(user_data["pk"])
            if isinstance(user_data, dict) and user_data.get("pk")
            else User.get(user_data)
        )
    else:
        user = User.get(user)

    # get obj
    obj = World.get_model(
        model or request.json.pop("model", None), pk or request.json.pop("pk", None)
    )

    # get world

    world = obj.get_world() if obj else None
    macro = macro or request.json.pop("macro", None)
    module = module or request.json.pop("module", None)
    return user, obj, world, macro, module
