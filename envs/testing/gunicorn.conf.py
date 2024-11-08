import os
from glob import glob

# Non logging stuff
bind = f"{os.environ.get('APP_HOST', '0.0.0.0')}:{os.environ.get('COMM_PORT', 80)}"
timeout = 120
workers = 2
capture_output = True  # Whether to send output to the error log

access_log_format = "ACCESS - %(U)s-%(m)s - res time: %(M)s %(b)s \n"
error_log_format = "ERROR - %(U)s :: \n"
# Access log - records incoming HTTP requests
accesslog = os.getenv("ACCESS_LOG", "-")
# Error log - records Gunicorn server goings-on
errorlog = os.getenv("ERROR_LOG", "-")
loglevel = "debug"
reload = True
reload_extra_files = glob("templates/**/*", recursive=True) + glob(
    "static/**/*", recursive=True
)
