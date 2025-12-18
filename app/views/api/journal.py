r"""
# Management API Documentation
"""

from autonomous.model.automodel import AutoModel
from flask import Blueprint, get_template_attribute, request

from autonomous import log
from models.journal import JournalEntry

from ._utilities import loader as _loader

journal_endpoint = Blueprint("journal", __name__)


# MARK: CRUD routes
###########################################################
##                    CRUD Routes                        ##
###########################################################
@journal_endpoint.route("/journal/entry/edit", methods=("POST",))
@journal_endpoint.route("/journal/entry/edit/<string:entrypk>", methods=("POST",))
def edit_journal_entry(entrypk=None):
    user, obj, request_data = _loader()
    entry = obj.journal.get_entry(entrypk)
    if not entry:
        entry = obj.journal.add_entry(title=f"Entry #{len(obj.journal.entries) + 1}")
    return get_template_attribute("shared/_journal.html", "journal_entry")(
        user, obj, entry
    )


@journal_endpoint.route("/journal/entry/update", methods=("POST",))
@journal_endpoint.route("/journal/entry/update/<string:entrypk>", methods=("POST",))
def update_journal_entry(entrypk=None):
    user, obj, request_data = _loader()
    associations = []
    for association in request.json.get("associations", []):
        if obj := AutoModel.get_model(association.get("model"), association.get("pk")):
            associations.append(obj)
    kwargs = {
        "title": request.json.get("name"),
        "text": request.json.get("text"),
        "importance": int(request.json.get("importance")),
        "associations": associations,
    }
    entrypk = entrypk or request.json.get("entrypk")
    # log(kwargs)
    entry = obj.journal.update_entry(pk=entrypk, **kwargs)
    return get_template_attribute("shared/_journal.html", "journal_entry")(
        user, obj, entry
    )


@journal_endpoint.route("/journal/entry/delete/<string:entrypk>", methods=("POST",))
def delete_journal_entry(entrypk):
    """
    ## Description
    Deletes the world object's journal entry based on the provided primary keys.
    """
    user, obj, request_data = _loader()
    if entry := obj.journal.get_entry(entrypk):
        obj.journal.entries.remove(entry)
        obj.journal.save()
        entry.delete()
        return "<p>success</p>"
    return "Not found"


@journal_endpoint.route("/journal/entry/<string:epk>/search", methods=("POST",))
def journal_search(epk):
    user, obj, request_data = _loader()
    entry = JournalEntry.get(epk)
    query = request.json.get("query")
    associations = (
        obj.world.search_autocomplete(query) if query and len(query) > 2 else []
    )
    associations = [a for a in associations if a not in entry.associations and a != obj]
    return get_template_attribute("shared/_dropdown.html", "search_dropdown")(
        user, obj, f"journal/entry/{entry.pk}/association/add", associations
    )


@journal_endpoint.route(
    "/journal/entry/<string:entrypk>/association/add/<string:amodel>/<string:apk>",
    methods=("POST",),
)
def journal_add_association(entrypk, amodel, apk):
    user, obj, request_data = _loader()
    if entry := obj.journal.get_entry(entrypk):
        if association := AutoModel.get_model(amodel, apk):
            if association not in entry.associations:
                entry.associations += [association]
                entry.save()
    return get_template_attribute("shared/_journal.html", "journal_entry")(
        user, obj, entry
    )
