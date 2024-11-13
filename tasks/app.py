import os

from config import Config
from flask import Flask, get_template_attribute, request

import tasks
from autonomous import log
from autonomous.model.automodel import AutoModel
from autonomous.tasks import AutoTasks

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
                return get_template_attribute("components/_tasks.html", "completetask")(
                    **task.return_value
                )
            elif task.status == "failed":
                return f"Generation Error for task#: {task.id} <br> {task.result.get('error', '')}"
            else:
                return get_template_attribute("components/_tasks.html", "checktask")(
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
        return get_template_attribute("components/_tasks.html", "checktask")(task["id"])

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
        return get_template_attribute("components/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/webcomic/scenes/<string:sessionpk>", methods=("POST",))
    def scene_generate_task(sessionpk):
        task = (
            AutoTasks()
            .task(tasks._generate_webcomic_task, pk=sessionpk, panel=False)
            .result
        )
        return get_template_attribute("components/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/webcomic/<string:sessionpk>", methods=("POST",))
    def webcomic_generate_task(sessionpk):
        task = (
            AutoTasks()
            .task(
                tasks._generate_webcomic_task,
                pk=sessionpk,
            )
            .result
        )
        return get_template_attribute("components/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/battlemap/<string:model>/<string:pk>", methods=("POST",))
    def create_battlemap(model, pk):
        task = (
            AutoTasks()
            .task(
                tasks._generate_battlemap_task,
                model=model,
                pk=pk,
            )
            .result
        )
        return get_template_attribute("components/_tasks.html", "checktask")(task["id"])

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
        return get_template_attribute("components/_tasks.html", "checktask")(task["id"])

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
        return get_template_attribute("components/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/autogm/<string:pk>", methods=("POST",))
    def autogm(pk):
        task_function = {
            "start": tasks._generate_autogm_start_task,
            "run": tasks._generate_autogm_run_task,
            "end": tasks._generate_autogm_end_task,
            "clear": tasks._generate_autogm_clear_task,
        }.get(request.json.get("action"))

        kwargs = {"pk": pk}
        if message := request.json.get("message", "").strip():
            kwargs["message"] = message
        if start_date := request.json.get("year"):
            kwargs["year"] = start_date
        if roll_type := request.json.get("roll_type"):
            kwargs["roll_type"] = roll_type
        if roll_type := request.json.get("roll_dice"):
            kwargs["roll_dice"] = roll_type
        log(kwargs)
        task = (
            AutoTasks()
            .task(
                task_function,
                **kwargs,
            )
            .result
        )
        return get_template_attribute("components/_tasks.html", "checktask")(task["id"])

    return app
