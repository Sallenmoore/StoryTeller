import os

from config import Config
from flask import Flask, get_template_attribute, request

import tasks
from autonomous import log
from autonomous.model.automodel import AutoModel
from autonomous.tasks import AutoTasks
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

    @app.route("/generate/chat/<string:pk>", methods=("POST",))
    def create_chat(pk):
        task = (
            AutoTasks()
            .task(
                tasks._generate_chat_task,
                pk=pk,
                message=request.json.get("message"),
            )
            .result
        )
        return get_template_attribute("shared/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/autogm/<string:pk>/<string:action>", methods=("POST",))
    def autogm(pk, action):
        task_function = {
            "start": tasks._generate_autogm_start_task,
            "run": tasks._generate_autogm_run_task,
            "end": tasks._generate_autogm_end_task,
            "regenerate": tasks._generate_autogm_regenerate_task,
        }.get(action)

        kwargs = {"pk": pk}
        if message := request.json.get("message"):
            kwargs["message"] = message
        if num_dice := request.json.get("pc_roll_num_dice"):
            type_dice = request.json.get("pc_roll_type_dice")
            modifier = request.json.get("pc_roll_modifier").strip()
            kwargs["roll_dice"] = f"{num_dice}d{type_dice}{modifier}"
        log(kwargs)
        task = (
            AutoTasks()
            .task(
                task_function,
                **kwargs,
            )
            .result
        )
        log(action, task_function, kwargs)
        user = User.get(pk)
        party = Faction.get(pk)
        snippet = get_template_attribute("shared/_gm.html", "scene_intermission")(
            user, party.world, party
        )
        return get_template_attribute("shared/_tasks.html", "checktask")(
            task["id"], snippet=snippet
        )

    @app.route("/generate/audio/<string:pk>", methods=("POST",))
    def create_audio(pk):
        task = (
            AutoTasks()
            .task(
                tasks._generate_audio_task,
                pk=pk,
            )
            .result
        )
        return get_template_attribute("shared/_tasks.html", "checktask")(task["id"])

    return app
