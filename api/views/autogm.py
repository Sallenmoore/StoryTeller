from flask import Blueprint, render_template, request
from autonomous import log
from models.user import User
from models.world import World

autogm_endpoint = Blueprint("autogm", __name__)


###########################################################
##                    World Routes                       ##
###########################################################
@autogm_endpoint.route("/", methods=("POST",))
def index():
    user = User.get(request.json.get("user"))
    return render_template("home.html", user=user)
