import random
import re

from autonomous.model.automodel import AutoModel
from bs4 import BeautifulSoup

from autonomous import log
from models.calendar.date import Date


def parse_text(obj, text):
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

    if obj.associations or obj.encounters:
        STRIP_ANCHOR_TAGS_PATTERN = re.compile(r"</?a[^>]*>", re.IGNORECASE | re.DOTALL)
        # --- 1. Strip all existing anchor tags from the text ---
        # This ensures that any existing links are removed, allowing a clean, full-name match.
        text = STRIP_ANCHOR_TAGS_PATTERN.sub("", text.replace("@", ""))
        for a in [*obj.associations, *obj.encounters]:
            if not a or not a.name or not a.path:
                continue

            # --- 2. Define the exact, case-insensitive match pattern ---
            # We escape the name to handle special characters and enforce word boundaries (\b)
            # to ensure "John" matches but not "Johnston".
            full_name_pattern = re.compile(
                r"\b" + re.escape(a.name) + r"\b", re.IGNORECASE
            )

            # --- 3. Replace all occurrences of the unwrapped full name ---
            link_template = (
                f"<a href='/{a.path}' style='a{{font-weight:bold;}}'>{a.name}</a>"
            )
            text = full_name_pattern.sub(link_template, text)
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
