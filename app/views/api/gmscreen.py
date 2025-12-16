"""
# Components API Documentation

## Components Endpoints
"""

import random

import dmtoolkit
import markdown
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from autonomous.model.automodel import AutoModel
from models.gmscreen.gmscreen import (
    GMScreen,
    GMScreenDnD5E,
    GMScreenLink,
    GMScreenNote,
    GMScreenTable,
)
from models.gmscreen.gmscreennoncanon import GMScreenNonCanon

from ._utilities import loader as _loader

gmscreen_endpoint = Blueprint("gmscreen", __name__)


@gmscreen_endpoint.route("/display", methods=("POST",))
def gmscreendisplay():
    user, obj, request_data = _loader()
    user.current_screen = (
        GMScreen.get(request.json.get("screenpk")) or user.current_screen
    )
    log(user.current_screen, request.json.get("screenpk"))
    user.save()
    return get_template_attribute("manage/_gmscreen.html", "screen")(user, obj)


###########################################################
##             Screen Manage Routes                      ##
###########################################################
@gmscreen_endpoint.route("/", methods=("POST",))
def gmscreenmanage():
    user, obj, request_data = _loader()
    user.current_screen = (
        GMScreen.get(request.json.get("screenpk")) or user.current_screen
    )

    user.save()
    return get_template_attribute("manage/_gmscreen.html", "manage_gmscreens")(
        user, obj
    )


@gmscreen_endpoint.route("/add", methods=("POST",))
def gmscreenadd():
    user, obj, request_data = _loader()
    gm_screen = GMScreen(user=user, world=obj.world)
    gm_screen.save()
    user.screens += [gm_screen]
    if not user.current_screen:
        user.current_screen = gm_screen
    user.save()
    return get_template_attribute("manage/_gmscreen.html", "manage_gmscreens")(
        user, obj
    )


@gmscreen_endpoint.route("/<string:screenpk>/update", methods=("POST",))
def gmscreenupdate(screenpk):
    user, obj, request_data = _loader()
    gm_screen = GMScreen.get(screenpk)
    if new_area := request.json.get("addarea"):
        gm_screen.add_area(new_area)
    elif name := request.json.get("name"):
        log(name)
        gm_screen.name = name
        gm_screen.save()
    return get_template_attribute("manage/_gmscreen.html", "manage_gmscreens")(
        user, obj
    )


###########################################################
##             Screen Area Manage Routes                 ##
###########################################################


@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/update", methods=("POST",)
)
def gmscreenareaupdate(screenpk, areapk):
    gm_screen = GMScreen.get(screenpk)
    for area in gm_screen.areas:
        if str(area.pk) == areapk:
            area.name = request.json.get("name")
            area.save()
            return "success"
    log("not found")
    return "not found"


@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/remove", methods=("POST",)
)
def gmscreenarearemove(screenpk, areapk):
    user, obj, request_data = _loader()
    gm_screen = GMScreen.get(screenpk)
    areas = []
    for area in gm_screen.areas:
        if str(area.pk) != areapk:
            areas.append(area)
        else:
            area.delete()
    gm_screen.areas = areas
    gm_screen.save()
    return get_template_attribute("manage/_gmscreen.html", "manage_gmscreens")(
        user, obj
    )


#######################################################################
##                    Component Area Routes                          ##
#######################################################################

## MARK: Note Area
############# Note Area ################


@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/note", methods=("POST",)
)
def gmscreennote(screenpk, areapk):
    gm_screen_area = GMScreenNote.get(areapk)
    gm_screen_area.text_type = request.json.get("text_type") or gm_screen_area.text_type
    gm_screen_area.note = request.json.get("note", "").strip() or gm_screen_area.note
    gm_screen_area.text_type = request.json.get("text_type") or gm_screen_area.text_type
    gm_screen_area.save()
    return gm_screen_area.area()


## MARK: Table Area
############# Table Area ################
@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/table", methods=("POST",)
)
def gmscreentable(screenpk, areapk):
    user, obj, request_data = _loader()
    gm_screen_area = GMScreenTable.get(areapk)
    gm_screen_area.itemlist = [i for i in request.json.get("itemlist", []) if i.strip()]
    gm_screen_area.save()
    return gm_screen_area.area()


@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/table/preset",
    methods=("POST",),
)
def gmscreentablepreset(screenpk, areapk):
    gm_screen_area = GMScreenTable.get(areapk)
    gm_screen_area.entries = []
    gm_screen_area.datafile = request.json.get("preset")
    gm_screen_area.save()
    return gm_screen_area.area()


@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/table/additem",
    methods=("POST",),
)
def gmscreentableadd(screenpk, areapk):
    gm_screen_area = GMScreenTable.get(areapk)
    if not gm_screen_area.itemlist or gm_screen_area.itemlist[0] != "":
        gm_screen_area.itemlist.insert(0, "")
        gm_screen_area.save()
    return gm_screen_area.area()


@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/table/random",
    methods=("POST",),
)
def gmscreentablerandom(screenpk, areapk):
    gm_screen_area = GMScreenTable.get(areapk)
    gm_screen_area.selected = random.choice(gm_screen_area.itemlist)
    gm_screen_area.save()
    return gm_screen_area.area()


@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/table/reset",
    methods=("POST",),
)
def gmscreentablereset(screenpk, areapk):
    gm_screen_area = GMScreenTable.get(areapk)
    gm_screen_area.selected = ""
    gm_screen_area.save()
    return gm_screen_area.area()


## MARK: Link Area
############# Link Area ################
@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/link", methods=("POST",)
)
def gmscreenlink(screenpk, areapk):
    gm_screen_area = GMScreenLink.get(areapk)
    if objs := request.json("objs"):
        objs = [AutoModel.load_model(obj["model"]).get(obj["pk"]) for obj in objs]
        gm_screen_area.objs = objs
        gm_screen_area.save()
    return gm_screen_area.area()


@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/link/search", methods=("POST",)
)
def gmscreensearch(screenpk, areapk):
    user, obj, request_data = _loader()
    gm_screen_area = GMScreenLink.get(areapk)
    query = request.json.get("query", "")
    results = obj.world.search_autocomplete(query=query) if len(query) > 2 else []
    results = [r for r in results if r not in gm_screen_area.objs]
    return get_template_attribute("manage/_gmscreen.html", "screen_link_area_dropdown")(
        user, obj, gm_screen_area, results
    )


@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/link/add/<string:childmodel>/<string:childpk>",
    methods=("POST",),
)
def gmscreenlinkadd(screenpk, areapk, childmodel, childpk):
    user, obj, request_data = _loader()
    gm_screen_area = GMScreenLink.get(areapk)
    obj = obj.world.get_model(childmodel, childpk)
    gm_screen_area.objs.append(obj)
    gm_screen_area.save()
    return gm_screen_area.area()


@gmscreen_endpoint.route(
    "/<string:screenpk>/link/<string:areapk>/remove/<string:itemmodel>/<string:itempk>",
    methods=("POST",),
)
def gmscreenlinkremoveitem(screenpk, areapk, itemmodel, itempk):
    user, obj, request_data = _loader()
    gm_screen_area = GMScreenLink.get(areapk)
    obj = obj.world.get_model(itemmodel, itempk)
    gm_screen_area.objs = [o for o in gm_screen_area.objs if o != obj]
    gm_screen_area.save()
    return gm_screen_area.area()


## MARK: DnD5e Lookup Area
############# DnD5e Lookup Area ################
@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/dnd5e",
    methods=("POST",),
)
def gmscreendnd5e(screenpk, areapk):
    gm_screen_area = GMScreenDnD5E.get(areapk)
    return gm_screen_area.area(selected=request.json.get("selected"))


@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/dnd5e/search",
    methods=("POST",),
)
def dnd5esearch(screenpk, areapk):
    gm_screen_area = GMScreenDnD5E.area()
    results = []
    query = request.json.get("query", "")
    if len(query) > 2:
        results += dmtoolkit.dmtools.search_monster(query)
        results += dmtoolkit.dmtools.search_item(query)
        results += dmtoolkit.dmtools.search_feature(query)
        results += dmtoolkit.dmtools.search_rules(query)
    log(results)
    snippet = get_template_attribute("manage/_gmscreen.html", "dnd5e_search")(
        gm_screen_area, results
    )

    return snippet


## MARK: Non-Canon Lookup Area
############# Non-Canon Lookup Area ################
@gmscreen_endpoint.route(
    "/<string:screenpk>/area/<string:areapk>/noncanon",
    methods=("POST",),
)
def gmscreennoncanon(screenpk, areapk):
    gm_screen_area = GMScreenNonCanon.get(areapk)
    gm_screen_area.filter = request.json.get("filtermodel", "Character")
    gm_screen_area.save()
    log(gm_screen_area.filter)
    result = gm_screen_area.area()
    log(result)
    return result
