import os

import requests


def start_task(endpoint, **kwargs):
    return requests.post(
        f"http://{os.environ.get('TASKS_SERVICE_NAME')}:{os.environ.get('COMM_PORT')}/{endpoint}",
        json=kwargs,
    ).text
