import os

from autonomous.model.automodel import AutoModel
from autonomous.tasks import AutoTasks
from config import Config
from flask import Flask, get_template_attribute, request

import tasks
from autonomous import log
from filters.forms import label_style
from filters.utils import bonus, get_icon, roll_dice
from models.campaign.episode import Episode
from models.ttrpgobject.faction import Faction
from models.user import User
from models.world import World

models = {
    "player": "Character",
    "player_faction": "Faction",
}  # add model names that cannot just be be titlecased from lower case, such as POI or 'player':Character


def _import_model(model):
    model_name = models.get(model, model.title())
    if Model := AutoModel.load_model(model_name):
        return Model
    return None


def create_app():
    app = Flask(os.getenv("APP_NAME", __name__))
    app.config.from_object(Config)

    app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024  # 300 MB upload limit

    app.jinja_env.filters["bonus"] = bonus
    app.jinja_env.filters["roll_dice"] = roll_dice
    app.jinja_env.filters["label_style"] = label_style
    app.jinja_env.filters["get_icon"] = get_icon

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

    def _generate_task(func, **kwargs):
        task = (
            AutoTasks()
            .task(
                func,
                **kwargs,
            )
            .result
        )
        return get_template_attribute("shared/_tasks.html", "checktask")(task["id"])

    @app.route("/generate/<string:model>/<string:pk>", methods=("POST",))
    def generate(model, pk):
        return _generate_task(
            tasks._generate_task,
            model=model,
            pk=pk,
        )

    @app.route("/generate/character/<string:pk>/dndbeyond", methods=("POST",))
    def pulldnbeyonddata(pk):
        return _generate_task(
            tasks._generate_character_from_dndbeyond_task,
            pk=pk,
        )

    @app.route("/generate/image/<string:model>/<string:pk>", methods=("POST",))
    def image_generate_task(model, pk):
        return _generate_task(
            tasks._generate_image_task,
            model=model,
            pk=pk,
        )

    @app.route("/generate/map/<string:model>/<string:pk>", methods=("POST",))
    def create_map(model, pk):
        return _generate_task(
            tasks._generate_map_task,
            model=model,
            pk=pk,
        )

    @app.route("/generate/history/<string:model>/<string:pk>", methods=("POST",))
    def generate_history(model, pk):
        return _generate_task(
            tasks._generate_history_task,
            model=model,
            pk=pk,
        )

    @app.route("/generate/campaign/<string:pk>/summary", methods=("POST",))
    def generate_campaign_summary(pk):
        return _generate_task(
            tasks._generate_campaign_summary_task,
            pk=pk,
        )

    @app.route("/generate/campaign/episode/<string:pk>/summary", methods=("POST",))
    def generate_session_summary(pk):
        return _generate_task(
            tasks._generate_session_summary_task,
            pk=pk,
        )

    @app.route("/generate/campaign/episode/<string:pk>/report", methods=("POST",))
    def generate_session_report(pk):
        return _generate_task(
            tasks._generate_session_report_task,
            pk=pk,
        )

    @app.route("/generate/episode/<string:pk>/graphic", methods=("POST",))
    def generate_episode_graphic(pk):
        return _generate_task(
            tasks._generate_episode_graphic_task,
            pk=pk,
        )

    @app.route("/generate/episode/<string:pk>/transcribe", methods=("POST",))
    def create_episode_transcription(pk):
        return _generate_task(
            tasks._generate_episode_transcription_task,
            pk=pk,
        )

    @app.route("/generate/episode/<string:pk>/transcription/summary", methods=("POST",))
    def generate_episode_report(pk):
        return _generate_task(
            tasks._generate_episode_transcription_summary_task,
            pk=pk,
        )

    @app.route("/generate/character/<string:pk>/chat", methods=("POST",))
    def generate_character_chat(pk):
        return _generate_task(
            tasks._generate_character_chat_task,
            pk=pk,
            chat=request.json.get("chat"),
        )

    @app.route("/generate/ability/<string:pk>", methods=("POST",))
    def generate_ability(pk):
        return _generate_task(
            tasks._generate_ability_task,
            pk=pk,
        )

    @app.route("/generate/audio/<string:model>/<string:pk>", methods=("POST",))
    def create_audio(model, pk):
        return _generate_task(
            tasks._generate_audio_task,
            model=model,
            pk=pk,
            pre_text=request.json.get("pre_text", ""),
            post_text=request.json.get("post_text", ""),
        )

    @app.route("/generate/gmscreen/table/<string:pk>", methods=("POST",))
    def create_table(pk):
        return _generate_task(
            tasks._generate_table_items_task,
            pk=pk,
            worldpk=request.json.get("worldpk"),
            prompt=request.json.get("prompt"),
        )

    @app.route("/generate/dungeon/<string:pk>/map", methods=("POST",))
    def create_dungeon_map(pk):
        return _generate_task(
            tasks._generate_dungeon_map_task,
            pk=pk,
        )

    @app.route("/generate/dungeon/room/<string:pk>", methods=("POST",))
    def create_dungeon_room(pk):
        return _generate_task(
            tasks._generate_dungeon_room_task,
            pk=pk,
        )

    @app.route("/generate/dungeon/room/<string:pk>/map", methods=("POST",))
    def create_dungeon_room_map(pk):
        return _generate_task(
            tasks._generate_dungeon_room_map_task,
            pk=pk,
        )

    @app.route("/generate/dungeon/room/<string:pk>/encounter", methods=("POST",))
    def create_dungeon_room_encounter(pk):
        return _generate_task(
            tasks._generate_dungeon_room_encounter_task,
            pk=pk,
        )

    @app.route("/generate/<string:pk>/quest/create", methods=("POST",))
    def create_quest(pk):
        return _generate_task(tasks._generate_quest_task, pk=pk)

    @app.route("/generate/event/<string:pk>", methods=("POST",))
    def generate_event(pk):
        return _generate_task(
            tasks._generate_event_task,
            pk=pk,
        )

    @app.route("/generate/event/from_events", methods=("POST",))
    def generate_event_from_events():
        return _generate_task(
            tasks._generate_event_from_events_task,
            event_ids=request.json.get("event_ids"),
        )

    @app.route("/generate/event/<string:pk>/summary", methods=("POST",))
    def generate_event_summary(pk):
        return _generate_task(tasks._generate_event_summary_task, pk=pk)

    @app.route("/generate/lore/<string:pk>", methods=("POST",))
    def generate_lore(pk):
        return _generate_task(tasks._generate_lore_task, pk=pk)

    @app.route("/generate/story/<string:pk>", methods=("POST",))
    def create_story(pk):
        return _generate_task(tasks._generate_story_task, pk=pk)

    @app.route("/generate/story/<string:pk>/summary", methods=("POST",))
    def generate_story_summary(pk):
        return _generate_task(
            tasks._generate_story_summary_task,
            pk=pk,
        )

    return app
