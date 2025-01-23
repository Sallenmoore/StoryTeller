import os

from config import Config
from flask import Flask, get_template_attribute, request

import tasks
from autonomous import log
from autonomous.model.automodel import AutoModel
from autonomous.tasks import AutoTasks
from filters.utils import bonus, roll_dice
from models.ttrpgobject.faction import Faction
from models.user import User

models = {
    "player": "Character",
    "player_faction": "Faction",
    "poi": "POI",
}  # add model names that cannot just be be titlecased from lower case, such as POI or 'player':Character


def _import_model(model):
    model_name = models.get(model, model.title())
    if Model := AutoModel.load_model(model_name):
        return Model
    return None


def create_app():
    app = Flask(os.getenv("APP_NAME", __name__))
    app.config.from_object(Config)

    app.jinja_env.filters["bonus"] = bonus
    app.jinja_env.filters["roll_dice"] = roll_dice

    # Configure Routes
    @app.route(
        "/checktask/<taskid>",
        methods=(
            "GET",
            "POST",
        ),
    )
    def checktask(taskid):
        if task := AutoTasks().get_task(taskid):
            # log(task.status, task.return_value, task.id)
            if task.status == "finished":
                return get_template_attribute("shared/_tasks.html", "completetask")(
                    **task.return_value
                )
            elif task.status == "failed":
                return f"<p>Generation Error for task#: {task.id} </p> </p>{task.result.get('error', '')}</p>"
            else:
                return get_template_attribute("shared/_tasks.html", "checktask")(
                    task.id
                )
        else:
            return "No task found"

    @app.route("/generate/<string:model>/<string:pk>", methods=("POST",))
    def generate(model, pk):
        task = (
            AutoTasks()
            .task(
                tasks._generate_task,
                model=model,
                pk=pk,
            )
            .result
        )
        return get_template_attribute("shared/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/image/<string:model>/<string:pk>", methods=("POST",))
    def image_generate_task(model, pk):
        task = (
            AutoTasks()
            .task(
                tasks._generate_image_task,
                model=model,
                pk=pk,
            )
            .result
        )
        return get_template_attribute("shared/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/map/<string:model>/<string:pk>", methods=("POST",))
    def create_map(model, pk):
        task = (
            AutoTasks()
            .task(
                tasks._generate_map_task,
                model=model,
                pk=pk,
            )
            .result
        )
        return get_template_attribute("shared/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/history/<string:model>/<string:pk>", methods=("POST",))
    def generate_history(model, pk):
        task = (
            AutoTasks()
            .task(
                tasks._generate_history_task,
                model=model,
                pk=pk,
            )
            .result
        )
        return get_template_attribute("shared/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/campaign/<string:pk>/summary", methods=("POST",))
    def generate_campaign_summary(pk):
        task = (
            AutoTasks()
            .task(
                tasks._generate_campaign_summary_task,
                pk=pk,
            )
            .result
        )
        return get_template_attribute("shared/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/campaign/episode/<string:pk>/summary", methods=("POST",))
    def generate_session_summary(pk):
        task = (
            AutoTasks()
            .task(
                tasks._generate_session_summary_task,
                pk=pk,
            )
            .result
        )
        return get_template_attribute("shared/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/audio/<string:model>/<string:pk>", methods=("POST",))
    def create_audio(model, pk):
        task = (
            AutoTasks()
            .task(
                tasks._generate_audio_task,
                model=model,
                pk=pk,
                pre_text=request.json.get("pre_text", ""),
                post_text=request.json.get("post_text", ""),
            )
            .result
        )
        return get_template_attribute("shared/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/campaign/episode/<string:pk>/gn", methods=("POST",))
    def create_gn(pk):
        task = (
            AutoTasks()
            .task(
                tasks._generate_gn_task,
                pk=pk,
            )
            .result
        )
        return get_template_attribute("shared/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/campaign/<string:pk>/outline", methods=("POST",))
    def create_outline(pk):
        task = (
            AutoTasks()
            .task(
                tasks._generate_campaign_outline_task,
                pk=pk,
                scenario=request.json.get("scenario", ""),
            )
            .result
        )
        return get_template_attribute("shared/_tasks.html", "checktask")(task["id"])

    return app
