r"""
# World API Documentation

## World Endpoints

### Model Structure

- name: "",
- backstory: "",
- desc: "",
- traits: [str],
- notes: [str],
- campaigns: [Campaign],
- regions: [`Region`],
- players: [`Character`],
- player_faction: `Faction`,

"""

from flask import Blueprint, get_template_attribute, render_template, request
from views.manage import childmanage

from autonomous import log
from models.campaign.campaign import Campaign
from models.campaign.episode import Session
from models.user import User
from models.world import World

world_endpoint = Blueprint("world", __name__)


###########################################################
##                    World Routes                       ##
###########################################################
@world_endpoint.route("/", methods=("POST",))
def index():
    user = User.get(request.json.get("user"))
    return render_template("home.html", user=user)


@world_endpoint.route("/build", methods=("POST",))
def build():
    """
    Description: Adds a new subuser to the world if the user is authenticated.
    Parameters:
      - pk: Primary key of the world
      - user: Primary key of the user
      - new_user: Email of the new user to be added
    Returns:
      - A message indicating the result of the operation
    """
    user = User.get(request.json.get("user"))
    if user.role == "guest":
        return "You do not have permission to create a world."

    World.build(
        system=request.json.get("system"),
        user=user,
        name=request.json.get("name"),
        desc=request.json.get("desc"),
        backstory=request.json.get("backstory"),
    )

    return render_template("home.html", user=user)


@world_endpoint.route("/build/form", methods=("POST",))
def buildform():
    user = User.get(request.json.get("user"))
    return get_template_attribute("models/_world.html", "worldbuild")(user=user)


@world_endpoint.route("<string:pk>/timeline", methods=("POST",))
def timeline(pk):
    obj = World.get(pk)
    macro = "timeline"
    events = []
    for c in obj.campaigns:
        c.save()
        for e in c.canon:
            if e not in events:
                events += [e]
    params = {
        "user": User.get(request.json.get("user")),
        "obj": obj,
        "events": events[::-1],
    }
    return get_template_attribute("components/_timeline.html", macro)(**params)


@world_endpoint.route("<string:pk>/childmanage", methods=("POST",))
def childmanager(pk):
    return childmanage()


@world_endpoint.route("/user/add", methods=("POST",))
def user_add():
    """
    Description: Adds a new subuser to the world if the user is authenticated.
    Parameters:
      - pk: Primary key of the world
      - user: Primary key of the user
      - new_user: Email of the new user to be added
    Returns:
      - A message indicating the result of the operation
    """
    obj = World.get(request.json.get("pk"))
    user = User.get(request.json.get("user"))
    if new_user := User.find(email=request.json.get("new_user").strip()):
        if new_user not in obj.subusers:
            obj.subusers.append(new_user)
            obj.save()
            log(f"User {new_user.email} added to World {obj.name}")
        else:
            log("User already added to world")
        new_user.add_world(obj)

    return get_template_attribute("models/_world.html", "details")(user, obj)


@world_endpoint.route("/calendar/update", methods=("POST",))
def calendar_update():
    user = User.get(request.json.get("user"))
    world = World.get(request.json.get("pk"))
    world.calendar.year_string = (
        request.json.get("year_string") or world.calendar.year_string
    )
    world.calendar.months = request.json.get("months") or world.calendar.months
    if (
        diff_index := int(request.json.get("num_months_per_year"))
        - world.calendar.num_months_per_year
    ):
        if diff_index > 0:
            world.calendar.months += [""] * diff_index
        elif diff_index < 0:
            world.calendar.months = world.calendar.months[:diff_index]

    world.calendar.day_names = request.json.get("days") or world.calendar.days
    if (
        diff_index := int(request.json.get("num_days_per_week"))
        - world.calendar.num_days_per_week
    ):
        if diff_index > 0:
            world.calendar.days += [""] * diff_index
        elif diff_index < 0:
            world.calendar.days = world.calendar.days[:diff_index]

    world.calendar.days_per_year = int(
        request.json.get("num_days_per_year") or world.calendar.days_per_year
    )
    world.save()
    info = get_template_attribute("models/_world.html", "manage_details")
    return get_template_attribute("manage/_details.html", "details")(user, world, info)


@world_endpoint.route("/visualize", methods=("POST",))
def world_visualizations():
    user = User.get(request.json.get("user"))
    world = World.get(request.json.get("pk"))
    return get_template_attribute("models/_world.html", "visualizations")(user, world)


@world_endpoint.route("/webcomic", methods=("POST",))
@world_endpoint.route("/webcomic/<string:episodepk>", methods=("POST",))
def webcomic(episodepk=None):
    user = User.get(request.json.get("user"))
    world = World.get(request.json.get("pk"))
    episode = None
    if episodepk := episodepk or request.json.get("episodepk"):
        log(episodepk)
        episode = Session.get(episodepk)
    elif campaign := Campaign.get(request.json.get("campaignpk")):
        episode = campaign.episodes[0]
    elif world.current_campaign:
        episode = world.current_campaign.episodes[0]

    if episode and request.json.get("comic_prompt"):
        episode.comic_prompt = request.json.get("comic_prompt")
        episode.save()
    return get_template_attribute("models/_world.html", "webcomic_generator")(
        user, world, episode
    )


@world_endpoint.route("/characterrelations", methods=("POST",))
def characterrelations():
    user = User.get(request.json.get("user"))
    world = World.get(request.json.get("pk"))
    return get_template_attribute("models/_world.html", "character_visualizations")(
        user, world
    )
