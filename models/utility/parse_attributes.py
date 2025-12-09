import random
import re

import markdown
from autonomous.model.automodel import AutoModel
from bs4 import BeautifulSoup

from autonomous import log
from models.calendar.date import Date


def parse_text(obj, text):
    text = (
        markdown.markdown(text.strip().replace("```markdown", "").replace("```", ""))
        .replace("h1>", "h3>")
        .replace("h2>", "h4>")
        .replace("h3>", "h5>")
        .replace("h4>", "h6>")
    )
    log(text)
    if text.count("<") < 3 or len(text) < 100:
        text = sanitize(text)
    log(text)
    if hasattr(obj, "associations"):
        LINK_PATTERN = re.compile(r'href="/([a-zA-Z]+)/([a-fA-F0-9]+)"')
        # Use re.findall to get all tuples of (model, pk) from the report string
        found_links = LINK_PATTERN.findall(text)
        # Use a set to store unique associations to prevent duplicates
        unique_associations = set()

        for model_name, pk_value in found_links:
            # Check if this specific association has already been processed in this run
            if (model_name, pk_value) in unique_associations:
                continue

            try:
                # Attempt to retrieve the object using the custom function
                # Note: AutoModel and get_model must be defined/imported correctly in your environment.

                if linked_object := AutoModel.get_model(model_name, pk_value):
                    if linked_object not in obj.associations:
                        obj.associations += [linked_object]

                    # Mark as processed to handle multiple links to the same object
                    unique_associations.add((model_name, pk_value))

            except Exception as e:
                # Log an error if the model/PK combination fails lookup (e.g., deleted object)
                log(f"Error retrieving linked object /{model_name}/{pk_value}: {e}")

        if obj.associations:
            STRIP_ANCHOR_TAGS_PATTERN = re.compile(
                r"</?a[^>]*>", re.IGNORECASE | re.DOTALL
            )
            # --- 1. Strip all existing anchor tags from the text ---
            # This ensures that any existing links are removed, allowing a clean, full-name match.
            text = STRIP_ANCHOR_TAGS_PATTERN.sub("", text.replace("@", ""))
            associations = sorted(
                obj.associations,
                key=lambda x: len(x.name or ""),
                reverse=True,
            )
            for a in associations:
                if not a or not a.name or not a.path:
                    continue

                # Escape the name for regex safety and add word boundaries (\b)
                safe_name = re.escape(a.name)

                # --- 3. Define the Pattern: Full Name Match ---
                # The pattern matches the full name and uses re.IGNORECASE
                full_name_pattern = re.compile(r"\b" + safe_name + r"\b", re.IGNORECASE)

                # --- 4. Define the Replacement Template ---
                # Note: Added the style tag inline for CSS portability,.
                link_template = f"<a href='/{a.path}' class='text-underline' style='font-weight:bold;'>{a.name}</a>"

                # --- 5. Perform the safe substitution ---
                # The substitution function checks if the match is already surrounded by the intended link.
                def replacer(match):
                    """
                    This function ensures we don't accidentally link a name that has already
                    been processed by a previous iteration, although stripping should make this redundant.
                    It primarily handles the case-insensitive replacement with the link template.
                    """
                    return link_template

                # Use re.sub to replace the name occurrences with the link template
                text = full_name_pattern.sub(replacer, text)
        log(text)
    return text


def parse_date(obj, date):
    if obj.pk and obj.calendar:
        # log(f"Pre-saving dates for {obj}", obj.start_date, obj.end_date)
        if isinstance(date, dict):
            new_date = Date(obj=obj, calendar=obj.calendar)
            new_date.day, new_date.month, new_date.year = (
                date["day"],
                date["month"],
                date["year"],
            )
            new_date.month = (
                obj.calendar.months.index(new_date.month.title())
                if new_date.month
                else random.randrange(len(obj.calendar.months))
            )
            new_date.day = int(new_date.day) if new_date.day else random.randint(1, 28)
            new_date.year = int(new_date.year) if new_date.year else -1
            new_date.save()
            date = new_date
        elif not obj.start_date or not isinstance(obj.start_date, Date):
            new_date = Date(
                obj=obj,
                calendar=obj.calendar,
                day=random.randint(1, 28),
                month=random.randrange(len(obj.calendar.months) or 12),
                year=-1,
            )
            date = new_date
    return date

    # log(
    #     f"Pre-saved dates for {obj}",
    #     obj.start_date,
    #     obj.end_date,
    #     obj.world.current_date,
    # )


def sanitize(data):
    if isinstance(data, str):
        data = BeautifulSoup(data, "html.parser").get_text()
    return data
