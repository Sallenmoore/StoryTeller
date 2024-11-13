# Built-In Modules
import glob
import os
import subprocess
from datetime import datetime

# external Modules
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from models.images.image import Image
from models.user import User
from models.world import World

admin_endpoint = Blueprint("admin", __name__)

tags = {
    "type": [
        "session",
        "battlemaps",
        "map",
        "world",
        "region",
        "city",
        "location",
        "encounter",
        "poi",
        "faction",
        "creature",
        "item",
        "character",
    ],
    "genre": ["fantasy", "horror", "sci-fi", "western", "historical"],
}
tag_list = sorted([*tags["type"], *tags["genre"]])


@admin_endpoint.route("/manage/images", methods=("POST",))
def images():
    if request.json.get("scan"):
        Image.storage_scan()
    images = Image.all()
    if tag_filter := request.json.get("tag"):
        log(tag_filter)
        if tag_filter == "_NoGenre":
            images = [
                img for img in images if not any(t in img.tags for t in tags["genre"])
            ]
        elif tag_filter == "_NoType":
            images = [
                img for img in images if not any(t in img.tags for t in tags["type"])
            ]
        elif tag_filter == "_Missing":
            images = [img for img in images if not any(t in img.tags for t in tag_list)]
        else:
            images = [img for img in images if tag_filter.lower() in img.tags]
    return get_template_attribute("admin/_images.html", "manage")(
        images=images, tags=tag_list, tag=tag_filter
    )


@admin_endpoint.route("/manage/image/<string:pk>", methods=("POST",))
def add_image_tag(pk):
    img = Image.get(pk)
    new_tag = request.json.get("new_tag")
    if img and new_tag:
        img.add_tag(new_tag)
        img.save()
    return images()


@admin_endpoint.route("/manage/image/<string:pk>/delete", methods=("POST",))
def delete_image(pk):
    img = Image.get(pk)
    if img:
        if img.remove_img_file():
            log(f"Image file removed: {img.asset_id}")
        img.delete()
        log(f"Image {pk} deleted")
        return "Success"
    log(f"Image {pk} not found")
    return "File not found"


@admin_endpoint.route("/manage/image/<string:pk>/tag/remove", methods=("POST",))
def remove_image_tag(pk):
    img = Image.get(pk)
    tag = request.json.get("tag")
    if img and tag:
        img.remove_tag(tag)
        img.save()
        return "Success"
    return "World not found"


@admin_endpoint.route("/manage/users", methods=("POST",))
def users():
    return get_template_attribute("admin/_users.html", "manage")(users=User.all())


@admin_endpoint.route("/manage/users/role", methods=("POST",))
def role_user():
    if user := User.get(request.json.get("user")):
        user.role = request.json.get("role")
        user.save()
        return "Success"
    return "User not found"


@admin_endpoint.route("/manage/users/delete", methods=("POST",))
def delete_user():
    if user := User.get(request.json.get("user")):
        user.delete()
        return "Success"
    return "User not found"


@admin_endpoint.route("/manage/worlds", methods=("POST",))
def worlds():
    return get_template_attribute("admin/_worlds.html", "manage")(worlds=World.all())


@admin_endpoint.route("/manage/users/delete", methods=("POST",))
def delete_world():
    if world := World.get(request.json.get("world")):
        world.delete()
        return "Success"
    return "World not found"


@admin_endpoint.route("/migration", methods=("POST",))
def migration():
    if os.environ.get("DEBUG"):
        log("starting migration...")
        # # dbload()
        # models = {
        #     "world": World,
        #     "region": Region,
        #     "city": City,
        #     "location": Location,
        #     "encounter": Encounter,
        #     "p_o_i": POI,
        #     "faction": Faction,
        #     "creature": Creature,
        #     "character": Character,
        #     "item": Item,
        #     "session": Session,
        #     "calendar": Calendar,
        #     "event": Event,
        #     "journal": Journal,
        #     "image": Image,
        #     "journal_entry": JournalEntry,
        #     "fantasy_system": FantasySystem,
        #     "horror_system": HorrorSystem,
        #     "sci_fi_system": SciFiSystem,
        #     "western_system": WesternSystem,
        #     "historical_system": HistoricalSystem,
        #     "post_apocalyptic_system": PostApocalypticSystem,
        #     "hardboiled_system": HardboiledSystem,
        #     "user": User,
        #     "auto_g_m": AutoGM,
        # }

        # from bson import DBRef, ObjectId

        # from autonomous.db.context_managers import switch_collection

        # with switch_collection(User, "Episode") as DropModel:
        #     DropModel._get_collection().drop()
        # with switch_collection(User, "GMScreen") as DropModel:
        #     DropModel._get_collection().drop()
        # with switch_collection(User, "GMScreenDnD5EClass") as DropModel:
        #     DropModel._get_collection().drop()
        # with switch_collection(User, "GMScreenDnD5ECombat") as DropModel:
        #     DropModel._get_collection().drop()
        # with switch_collection(User, "GMScreenDnD5ERace") as DropModel:
        #     DropModel._get_collection().drop()
        # with switch_collection(User, "GMScreenDnD5ESpell") as DropModel:
        #     DropModel._get_collection().drop()
        # with switch_collection(User, "GMScreenTable") as DropModel:
        #     DropModel._get_collection().drop()
        # with switch_collection(User, "GMScreenNote") as DropModel:
        #     DropModel._get_collection().drop()
        # with switch_collection(User, "Scene") as DropModel:
        #     DropModel._get_collection().drop()
        # with switch_collection(User, "OAIAgent") as DropModel:
        #     DropModel._get_collection().drop()
        # with switch_collection(User, "Event") as DropModel:
        #     DropModel._get_collection().drop()
        # with switch_collection(User, "EventDate") as DropModel:
        #     DropModel._get_collection().drop()

        # switch_collection(User, "User")

        # def get_new_table_name(old_table):
        #     for k, v in models.items():
        #         if v.model_name() == old_table:
        #             return k

        # def migrate_refs(obj):
        #     if isinstance(obj, dict):
        #         if "__extended_json_type__" in obj:
        #             if obj["__extended_json_type__"] == "datetime":
        #                 obj = obj["value"]
        #                 obj = datetime.fromisoformat(obj)
        #             elif obj["__extended_json_type__"] == "AutoModel":
        #                 obj_ref = obj["value"]
        #                 # log(obj_ref)
        #                 a_id = ObjectId(obj_ref["_id"])
        #                 old_table = obj_ref["_automodel"].split(".")[-1]
        #                 if model_ref_name := get_new_table_name(old_table):
        #                     a_ref = DBRef(model_ref_name, a_id)
        #                     obj = {"_cls": old_table, "_ref": a_ref}
        #                 else:
        #                     log(f"Error: {old_table} not found")
        #                     obj = None
        #         else:
        #             for k, v in obj.items():
        #                 if result := migrate_refs(v):
        #                     obj[k] = result
        #     elif isinstance(obj, list):
        #         for i, v in enumerate(obj):
        #             if result := migrate_refs(v):
        #                 obj[i] = result
        #     elif isinstance(obj, str):
        #         obj = obj.strip()
        #     return obj

        # for table_name, model in models.items():
        #     old_model_name = model.model_name()
        #     objs = model._get_collection()
        #     objs.drop()
        #     with switch_collection(model, old_model_name) as OldModel:
        #         old_objs = OldModel._get_collection()
        #         for o in old_objs.find():
        #             new_o = {"_cls": old_model_name}
        #             o.pop("_automodel", None)
        #             o.pop("_events", None)
        #             if old_model_name == "World":
        #                 o.pop("_world")
        #                 o.pop("_parent")
        #             else:
        #                 o.pop("_lineage", None) or o.pop("lineage", None)
        #             if old_model_name not in ["World", "Region", "City", "Location", "POI"]:
        #                 o.pop("battlemap", None)
        #             for k, v in o.items():
        #                 if k not in ["_id", "_data"] and k.startswith("_"):
        #                     k = k[1:]

        #                 if k == "bs_summary":
        #                     k = "backstory_summary"
        #                 elif k == "battlemap":
        #                     k = "map"
        #                 elif k == "image_data":
        #                     k = "image"
        #                 elif k == "traits" and isinstance(v, list):
        #                     v = ",".join(v)
        #                 elif k == "screens":
        #                     v = []
        #                 elif k in ["comic", "start_date", "end_date"]:
        #                     v = None
        #                 elif k == "coordinates":
        #                     if isinstance(v, list):
        #                         v = {"x": v[0], "y": v[1]}
        #                     if not isinstance(v, dict):
        #                         v = None
        #                 elif k == "world_pks":
        #                     k = "worlds"
        #                     worlds = []
        #                     for w_pk in v:
        #                         a_id = ObjectId(w_pk)
        #                         a_ref = DBRef("world", a_id)
        #                         worlds.append(a_ref)
        #                     v = worlds
        #                 # log(model, k, v)
        #                 new_o[k] = migrate_refs(v)

        #             # try:
        #             objs.insert_one(
        #                 new_o,
        #                 # bypass_document_validation=True,
        #             )
        #             # except Exception as e:
        #             #     log(f"Error: {e}")
        #         old_objs.drop()
        # log("...migration complete")

    return "<a href='/db'>DB</a>"


@admin_endpoint.route("/dbdump", methods=("POST",))
def dbdump():
    dev = int(os.environ.get("DEBUG") or os.environ.get("TESTING"))
    # log(
    #     os.environ.get("DEBUG"),
    #     os.environ.get("TESTING"),
    #     dev,
    #     type(dev),
    #     not dev,
    # )
    if not dev:
        log("starting dump...")
        host = os.getenv("DB_HOST", "db")
        port = os.getenv("DB_PORT", 27017)
        password = os.getenv("DB_PASSWORD")
        username = os.getenv("DB_USERNAME")
        connect_str = f"mongodb://{username}:{password}@{host}:{port}"
        datetime_string = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        command_str = f'mongodump --uri="{connect_str}" --archive="dbbackups/dbbackup-{datetime_string}.archive"'
        result = subprocess.Popen(command_str, shell=True).wait()
        log(result)
        return "<p>Success</p>"
    else:
        return "<p>!!! Cannot Dump Dev DB !!!</p>"


@admin_endpoint.route("/dbload", methods=("POST",))
# @auth_required()  # admin=True)
def dbload():
    log("starting load...")
    files = glob.glob(
        "dbbackups/dbbackup-*.archive"
    )  # replace with your directory path
    # Find the file with the most recent timestamp
    latest_file = max(files, key=os.path.getctime)
    # log(latest_file)
    host = os.getenv("DB_HOST", "db")
    port = os.getenv("DB_PORT", 27017)
    password = os.getenv("DB_PASSWORD")
    username = os.getenv("DB_USERNAME")
    connect_str = f"mongodb://{username}:{password}@{host}:{port}"
    log("Flushing and Restoring DB...")
    command_str = f'mongorestore -v --drop --noIndexRestore --uri="{connect_str}" --archive="{latest_file}"'
    result = subprocess.Popen(command_str, shell=True).wait()
    log(command_str, result)
    return "<p>Success</p>"
