import os

import requests
from autonomous.ai.textagent import TextAgent


def start_task(endpoint, **kwargs):
    return requests.post(
        f"http://{os.environ.get('TASKS_SERVICE_NAME')}:{os.environ.get('COMM_PORT')}/{endpoint}",
        json=kwargs,
    ).text


def generate_text(messages, primer=""):
    return TextAgent().generate(messages, additional_instructions=primer)


def summarize_text(messages, primer=""):
    return TextAgent().summarize_text(messages, primer)
