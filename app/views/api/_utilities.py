import base64
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional, Sequence

from autonomous.auth import AutoAuth
from autonomous.model.automodel import AutoModel
from flask import request, session

try:
    # Works when a Flask application context is active
    from flask import render_template
except Exception:  # pragma: no cover - only hit if Flask is unavailable
    render_template = None  # type: ignore
from jinja2 import TemplateNotFound

from autonomous import log
from models.user import User
from models.world import World


def authenticate(user, obj):
    if obj and user in obj.world.users:
        return True
    return False


def loader(model=None, pk=None):
    # log(f"User: {user}, Model: {model}, PK: {pk}")
    # log(f"Request: {request}")
    if request.method == "GET":
        request_data = request.args
        # log(f"get request: {request_data}")
    elif request.method == "POST":
        if request.files:
            request_data = dict(request.form)
            for key, file in request.files.items():
                request_data[key] = base64.b64encode(file.read()).decode("utf-8")
        else:
            request_data = dict(request.json)
        # log(f"post: {request_data}")
    user = AutoAuth.current_user()
    # log(user)
    # get obj
    try:
        model = model or request_data.get("model", session.get("model", None))
        pk = pk or request_data.get("pk", session.get("pk", None))
        obj = AutoModel.get_model(model, pk)
    except Exception as e:
        log(f"Error getting model: {e}")
        obj = None
    else:
        session["model"] = model
        session["pk"] = pk
    # log(obj)
    return user, obj, request_data


"""Lightweight SMTP email helper used by API routes."""


SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME or "no-reply@example.com")


def _render_html(template: Optional[str], context: Optional[dict]) -> Optional[str]:
    """Render a Jinja template to HTML if a template path is provided."""
    if not template:
        return None
    if render_template is None:
        raise RuntimeError("Flask render_template is unavailable in this context")
    try:
        return render_template(template, **(context or {}))
    except TemplateNotFound as exc:
        log(f"Email template not found: {exc.name}")
        return None


def email(
    *,
    subject: str,
    recipients: Sequence[str],
    template: Optional[str] = None,
    context: Optional[dict] = None,
    body: Optional[str] = None,
    sender: Optional[str] = None,
    cc: Optional[Sequence[str]] = None,
    bcc: Optional[Sequence[str]] = None,
) -> bool:
    """Send a simple HTML email via SMTP.

    Args:
        subject: Email subject line.
        recipients: List of primary recipient addresses.
        template: Optional Jinja template path to render as HTML.
        context: Template context when using ``template``.
        body: Fallback HTML body if no template is supplied.
        sender: Optional from address (defaults to SMTP_FROM).
        cc: Optional CC recipients.
        bcc: Optional BCC recipients.

    Returns:
        True when the message is accepted by the SMTP server, False otherwise.
    """

    if not recipients:
        log("send_email called without recipients; skipping send")
        return False

    html_body = _render_html(template, context)
    if not html_body:
        html_body = body

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender or SMTP_FROM
    msg["To"] = ", ".join(recipients)
    if cc:
        msg["Cc"] = ", ".join(cc)

    all_recipients: list[str] = list(recipients)
    if cc:
        all_recipients.extend(cc)
    if bcc:
        all_recipients.extend(bcc)

    # Plaintext fallback for clients without HTML support
    msg.set_content("This message requires an HTML-capable email client.")
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            if SMTP_USE_TLS:
                server.starttls(context=context)
                server.ehlo()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg, to_addrs=all_recipients)
        return True
    except Exception as exc:  # pragma: no cover - logged for visibility
        log(f"Failed to send email: {exc}")
        return False
