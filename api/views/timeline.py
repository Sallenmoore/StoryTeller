"""
# Components API Documentation

## Components Endpoints

"""

from flask import Blueprint, get_template_attribute, request
from jinja2 import TemplateNotFound

from autonomous import log
from models.campaign import Campaign
from models.campaign.session import Session
from models.events.event import Event
from models.world import World

from ._utilities import loader as _loader

timeline_endpoint = Blueprint("timeline", __name__)


# MARK: Timeline route
###########################################################
##                    Timeline Routes                    ##
###########################################################
@timeline_endpoint.route("/event/list", methods=("POST",))
def timelist():
    user, obj, world, *_ = _loader()
    return get_template_attribute("components/_timeline.html", "eventlist")(
        user, obj, events=[e for e in obj.events if e.placed and e.year]
    )


# @timeline_endpoint.route("/event/unplaced", methods=("POST",))
# def unplaced():
#     user, obj, world, *_ = _loader()
#     return get_template_attribute("components/_timeline.html", "unplaced")(
#         user, obj, events=[e for e in obj.events if not e.placed and e.year]
#     )


# @timeline_endpoint.route("/event/noncanon", methods=("POST",))
# def noncanon():
#     user, obj, world, *_ = _loader()
#     events = [e for e in obj.events if int(e.year) == 0]
#     log(events)
#     return get_template_attribute("components/_timeline.html", "noncanon")(
#         user, obj, events=events
#     )


# @timeline_endpoint.route("/event/add", methods=("POST",))
# def add_event():
#     user, obj, world, *_ = _loader()
#     if name := request.json.get("name"):
#         date = request.json.get("date", world.current_date)
#         obj.add_event(name=name, date=date)
#     return get_template_attribute("components/_timeline.html", "addevent")(user, obj)


# @timeline_endpoint.route("/event/<pk>", methods=("POST",))
# def get_event(pk):
#     user, obj, world, *_ = _loader()
#     event = Event.get(pk)
#     return event.serialize() if event else {"error": "<p>Not Found</p>"}


# @timeline_endpoint.route("/event/<string:pk>/update", methods=("POST",))
# def update_event(pk):
#     user, obj, *_ = _loader()
#     if event := Event.get(pk):
#         event.coordinates["x"] = request.json.get("xcoor") or event.coordinates["x"]
#         event.coordinates["y"] = request.json.get("ycoor") or event.coordinates["y"]
#         if episode := Session.get(request.json.get("episodepk")):
#             event.episode = episode
#         elif campaign := Campaign.get(request.json.get("campaignpk")):
#             event.episode = campaign.sessions[-1] if campaign.sessions else None
#         event.save()
#     return get_template_attribute("components/_timeline.html", "timeline")(user, obj)


# @timeline_endpoint.route("/markers", methods=("POST",))
# def event_markers():
#     user, obj, *_ = _loader()
#     markers = []
#     campaign = Campaign.get(request.json.get("campaignpk"))
#     daterange = request.json.get("daterange") or [None, None]
#     start_date = int(float(daterange[0])) if daterange[0] else None
#     end_date = int(float(daterange[1])) if daterange[1] else None
#     events = obj.get_events(
#         start_date=start_date,
#         end_date=end_date,
#         campaign=campaign,
#         mtype=request.json.get("mtype"),
#         placed=True,
#     )
#     # log(obj.name, events)
#     for e in events:
#         mark = {
#             "pk": e.pk,
#             "name": e.name,
#             "date": e.datestr(),
#             "coordinates": e.coordinates,
#             "summary": e.summary,
#             "imgurl": e.obj.image.url(50),
#         }
#         # log(mark)
#         markers.append(mark)
#     # log(markers)
#     return {"markers": markers}


# @timeline_endpoint.route("/event/<string:pk>/delete", methods=("POST",))
# def delete_event(pk):
#     user, obj, world, *_ = _loader()
#     if event := Event.get(pk):
#         event.obj.remove_event(event)
#         obj.save()
#         return "<p>success</p>"
#     return "<p>Not Found</p>"
