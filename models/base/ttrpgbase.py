import random

import markdown
import validators
from bs4 import BeautifulSoup
from flask import get_template_attribute
from slugify import slugify

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import BoolAttr, IntAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.events.event import Event
from models.images.image import Image
from models.journal import Journal

MAX_NUM_IMAGES_IN_GALLERY = 100
IMAGES_BASE_PATH = "static/images/tabletop"


class TTRPGBase(AutoModel):
    meta = {"abstract": True, "allow_inheritance": True, "strict": False}
    name = StringAttr(default="")
    backstory = StringAttr(default="")
    backstory_summary = StringAttr(default="")
    desc = StringAttr(default="")
    desc_summary = StringAttr(default="")
    traits = StringAttr(default="")
    image = ReferenceAttr(choices=[Image])
    start_date = ReferenceAttr(choices=[Event])
    end_date = ReferenceAttr(choices=[Event])
    current_age = IntAttr(default=0)
    history = StringAttr(default="")
    journal = ReferenceAttr(choices=[Journal])

    story_types = [
        "tragic",
        "heroic",
        "mysterious",
        "sinister",
        "unexpected",
        "dangerous",
        "boring",
        "mundane",
        "opulent",
        "decaying",
        "haunted",
        "harrowing",
        "enchanted",
        "cursed",
    ]

    _models = [
        "City",
        "Creature",
        "Character",
        "Encounter",
        "Faction",
        "Item",
        "Location",
        "POI",
        "Region",
    ]
    child_list = {"city": "cities"}
    model_list = {"poi": "POI"}
    _no_copy = {
        "journal": None,
        "history": "",
    }
    _possible_events = Event.event_options
    _traits_list = [
        "secretly evil",
        "openly evil",
        "openly neutral",
        "secretly neutral",
        "openly good",
        "secretly good",
        "dangerous",
        "mysterious",
    ]
    _funcobj = {}

    ########### Dunder Methods ###########

    def __eq__(self, obj):
        if hasattr(obj, "pk"):
            return self.pk == obj.pk
        return False

    def __ne__(self, obj):
        if hasattr(obj, "pk"):
            return self.pk != obj.pk
        return True

    def __lt__(self, obj):
        if hasattr(obj, "name"):
            return self.name < obj.name
        return False

    def __gt__(self, obj):
        if hasattr(obj, "name"):
            return self.name > obj.name
        return False

    def __hash__(self):
        return hash(self.pk)

    ########### Class Methods ###########

    @classmethod
    def child_list_key(cls, model):
        return cls.child_list.get(model.lower(), f"{model.lower()}s") if model else None

    @classmethod
    def get_model(cls, model, pk=None):
        if not model or not isinstance(model, str):
            return model
        model_str = cls.model_list.get(model.lower(), model.title())
        Model = AutoModel.load_model(model_str)
        return Model.get(pk) if pk else Model

    @classmethod
    def get_models(cls):
        return [AutoModel.load_model(model_str) for model_str in cls._models]

    ########### Property Methods ###########
    @property
    def age(self):
        if not self.current_age:
            if (
                self.end_date
                and self.start_date
                and self.end_date.year
                and self.start_date.year
            ):
                self.current_age = self.end_date.year - self.start_date.year
                self.save()
            elif (
                self.start_date
                and self.start_date.year
                and self.calendar.current_date.year
                and self.start_date.year < self.calendar.current_date.year
            ):
                self.current_age = (
                    self.calendar.current_date.year - self.start_date.year
                )
                self.save()

        return self.current_age

    @age.setter
    def age(self, value):
        self.current_age = value

    @property
    def child_models(self):
        results = []
        for model in self._models:
            Model = AutoModel.load_model(model)
            if self.model_name() in Model.parent_list:
                results.append(model)
        return results

    @property
    def current_date(self):
        return self.calendar.current_date

    @property
    def description(self):
        return self.desc

    @description.setter
    def description(self, val):
        self.desc = val

    @property
    def description_summary(self):
        return self.desc_summary

    @description_summary.setter
    def description_summary(self, val):
        self.desc_summary = val

    @property
    def funcobj(self):
        self._funcobj["parameters"]["required"] = list(
            self._funcobj["parameters"]["properties"].keys()
        )
        return self._funcobj

    @property
    def geneology(self):
        ancestor = self.parent
        line = []
        while ancestor and ancestor != self:
            if ancestor not in line:
                line += [ancestor]
            ancestor = ancestor.parent
        return line if line else [self.world]

    @property
    def genres(self):
        return list(self._systems.keys())

    @property
    def history_primer(self):
        return f"Incorporate the below EVENTS into the given {self.title}'s HISTORY to generate a narrative summary of the {self.title}'s story. Use MARKDOWN format with paragraph breaks after no more than 4 sentences."

    @property
    def history_prompt(self):
        return f"""
FOUNDED
---
{self.start_date.datestr() if self.start_date else "Unknown"}

HISTORY
---
{self.backstory_summary}

EVENTS
---
"""

    @property
    def image_tags(self):
        return [self.genre, self.model_name().lower()]

    @property
    def image_prompt(self):
        return f"Create an image of a {self.title}"

    @property
    def path(self):
        return f"{self.model_name().lower()}/{self.pk}"

    @property
    def possible_events(self):
        return self._possible_events

    @property
    def slug(self):
        return slugify(self.name)

    @property
    def title(self):
        return self.system.get_title(self)

    @property
    def titles(self):
        return self.system._titles

    ########### CRUD Methods ###########
    def delete(self):
        if self.journal:
            self.journal.delete()
        if self.events:
            [event.delete() for event in self.events]
        return super().delete()

    # MARK: Generate
    def generate(self, prompt=""):
        log(f"Generating data with AI for {self.name} ({self})...", _print=True)
        prompt += f"""
Use and expand on the existing object data listed below for the {self.title} object:
{"- Name: " + self.name if self.name.strip() else ""}
{"- Goal: " + self.goal if getattr(self, "goal", None) else ""}
{"- Current Status: " + self.status if getattr(self, "status", None) else ""}
{"- Description: "+self.description.strip() if self.description.strip() else ""}
{"- Backstory: " + self.backstory.strip() if self.backstory.strip() else ""}
        """
        if self.parent:
            prompt += f"""
===
The {self.title} is located in a {self.parent.title} described as: {self.parent.backstory_summary}.
        """
        if associations := [a for a in self.associations if a != self.parent]:
            prompt += """
===
- Associated Objects:
        """
            for child in associations:
                if child.name and child.backstory_summary:
                    prompt += f"""
        - pk: {child.pk}
            - Model: {child.model_name()}
            - Type: {child.title}
            - Name: {child.name}
            - Backstory: {child.backstory_summary}
                """
        # log(prompt, _print=True)
        if results := self.system.generate(self, prompt=prompt):
            # log(results, _print=True)
            if notes := results.pop("notes", None):
                if not self.journal:
                    self.journal = Journal(world=self.get_world(), parent=self)
                    self.journal.save()
                    self.save()
                self.journal.add_entry(
                    title="Secrets",
                    text=f"<p>{'</p><p>'.join(notes)}</p>",
                    importance=1,
                )
            for k, v in results.items():
                setattr(self, k, v)
            self.save()
        else:
            log(results, _print=True)
        return results

    ############# Boolean Methods #############

    def is_child(self, obj):
        return self in obj.children

    def is_associated(self, obj):
        return obj in self.associations

    ############# Image Methods #############

    def get_image_list(self, tags=[]):
        images = []
        tags = tags or [self.model_name().lower()]
        images = [img for img in Image.all() if all(t in img.tags for t in tags)]
        return images

    # MARK: generate_image
    def generate_image(self):
        log(f"Generating an Image with AI for {self.name} ({self})...", _print=True)
        date = ""
        if self.genre != "fantasy":
            if self.end_date and self.end_date.year:
                date = self.end_date.year
            elif self.start_date and self.start_date.year:
                date = self.end_date.year
            elif self.calendar.current_date.year:
                date = self.calendar.current_date.year
        prompt = (f"Set in the year {date}." if date else "") + self.image_prompt
        self.image = Image.generate(prompt=prompt, tags=self.image_tags)
        self.image.save()
        self.save()
        return self.image

    ############# Association Methods #############
    # MARK: Associations
    def add_association(self, obj):
        log(self, obj)
        # log(len(obj.associations), self in obj.associations)
        if self not in obj.associations:
            obj.associations.append(self)
        # log(len(obj.associations), self in obj.associations)

        # log(len(self.associations), obj in self.associations)
        if obj not in self.associations:
            self.associations.append(obj)
        # log(len(self.associations), obj in self.associations)

        if (
            not self.parent or self.parent == self.world
        ) and obj.model_name() in self.parent_list:
            self.parent = obj
        obj.save()
        self.save()
        return obj

    def remove_association(self, obj):
        if obj in self.associations:
            self.associations.remove(obj)
            if self.parent == obj:
                self.parent = None
            self.save()
            obj.remove_association(self)
        return self.associations

    def get_associations(self, model=None, children=True):
        if not model:
            associations = self.associations
        else:
            model = (
                model.__name__.lower() if not isinstance(model, str) else model.lower()
            )
            model = self.model_list.get(model, model.title())
            associations = [a for a in getattr(self, self.child_list_key(model)) if a]
        result = [o for o in associations if (children or o.parent != self)]
        result.sort(
            key=lambda x: (x.name.startswith("_"), x.name == "", x.name),
            reverse=True,
        )
        return result

    def has_associations(self, model):
        if not isinstance(model, str):
            model = model.__name__
        for assoc in self.associations:
            if assoc.model_name() == model:
                return True
        return False

    ########## Object Data ######################
    def resummarize(self, upload=False):
        self.history = "Generating... please refresh the page in a few seconds."
        self.save()
        # generate backstory summary
        if len(self.backstory) < 250:
            self.backstory_summary = self.backstory
        else:
            primer = "Generate a summary of less than 250 words of the following events in MARKDOWN format with paragraph breaks where appropriate, but after no more than 4 sentences."
            self.backstory_summary = self.system.generate_summary(
                self.backstory, primer
            )
            self.backstory_summary = markdown.markdown(self.backstory_summary)
        # generate backstory summary
        if len(self.description) < 15:
            self.description_summary = self.description
        else:
            primer = "Generate a plain text summary of the provided character's description in 15 words or fewer."
            self.description_summary = self.system.generate_summary(
                self.description, primer
            )
        self.campaigns.sort(key=lambda x: x.start_date)
        self.save()

        # generate history
        if (hasattr(self, "group") and self.group) or (
            self.start_date and self.start_date.year
        ):
            history = self.history_prompt
            for campaign in self.campaigns:
                for episode in campaign.sessions:
                    if self in episode.associations:
                        soup = BeautifulSoup(episode.summary, "html.parser")
                        summary = ""
                        for p in soup.prettify().split("<p>"):
                            if self.name.lower() in p.lower():
                                summary += p.replace("</p>", "")
                        if summary:
                            le = f"""
Dates: {episode.start_date.datestr()} - {episode.end_date.datestr()}
------
{summary}
"""
                            history += le
            history = self.system.generate_summary(history, self.history_primer)
            history = history.replace("```markdown", "").replace("```", "")
            self.history = (
                markdown.markdown(history).replace("h1>", "h3>").replace("h2>", "h3>")
            )
            self.save()
            if upload:
                self.get_world().update_refs()
        else:
            log("Character Not Yet Canon. Must have a Start Date", _print=True)

    def get_title(self, model):
        return self.system.get_title(model)

    def page_data(self):
        return {}

    def add_journal_entry(
        self,
        pk=None,
        title=None,
        text=None,
        tags=[],
        importance=0,
        date=None,
        associations=[],
    ):
        if pk:
            return self.journal.update_entry(
                pk=pk,
                title=title,
                text=text,
                tags=tags,
                importance=importance,
                date=date,
                associations=associations,
            )
        else:
            return self.journal.add_entry(
                title=title,
                text=text,
                tags=tags,
                importance=importance,
                date=date,
                associations=associations,
            )

    def add_event(
        self,
        episode=None,
        date=None,
        visibility=True,
        name=None,
        coordinates=None,
    ):
        new_event = Event(
            _obj=self,
            _episode=episode,
            _date=date,
            _visibility=visibility,
            _name=name,
            _coordinates=coordinates,
        )
        new_event.save()
        self.events.append(new_event)
        self.save()
        if new_event.date > self.calendar.current_date:
            self.calendar.current_date.day = new_event.day
            self.calendar.current_date.month = new_event.month
            self.calendar.current_date.year = new_event.year
            self.calendar.save()

    def get_events(
        self,
        start_date=None,
        end_date=None,
        campaign=None,
        mtype=None,
        placed=False,
        unplaced=False,
    ):
        start_year = int(
            start_date
            or (campaign and campaign.start_date.year)
            or self.start_date.date.year
        )
        end_year = int(
            end_date
            or (campaign and campaign.end_date.year)
            or self.end_date.date.year
            or self.current_date
        )
        result = []
        # log(len(self.events), start_year, end_year)
        for event in self.events:
            if start_year <= event.date.year <= end_year:
                # log(mtype, event.obj.model_name())
                if not mtype or event.obj.model_name() == mtype:
                    # log(placed, unplaced, event.placed)
                    if (
                        (not placed and not unplaced)
                        or (placed and event.placed)
                        or (unplaced and not event.placed)
                    ):
                        result.append(event)
        return result

    def remove_event(self, event):
        if event in self.events:
            self.events.remove(event)
            self.save()
            event.delete()

    def search_autocomplete(self, query):
        results = []
        for model in self._models:
            Model = self.load_model(model)
            # log(model, query)
            results += [
                r for r in Model.search(name=query, world=self.get_world()) if r != self
            ]
            # log(results)
        return results

    # /////////// HTML SNIPPET Methods ///////////
    def get_icon(self, model=None, size="1rem", type="basic"):
        model = model or self.model_name()
        return f"<iconify-icon icon='{Event.icon_options[type][model]}' width='{size}'></iconify-icon>"

    def label(self, model):
        if not isinstance(model, str):
            model = model.__name__
        return self.titles.get(model, model)

    def snippet(self, user, macro, kwargs=None):
        module = f"models/_{self.model_name().lower()}.html"
        if kwargs:
            return get_template_attribute(module, macro)(user, self, **kwargs)
        else:
            log(module, macro)
            return get_template_attribute(module, macro)(user, self)

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                   ##
    ###############################################################

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_image()
        document.pre_save_dates()
        document.pre_save_backstory()
        document.pre_save_traits()

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)
        document.post_save_start_date()
        document.post_save_end_date()
        document.post_save_journal()

    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################

    def pre_save_dates(self):
        if (
            self.pk
            and isinstance(self.start_date, dict)
            and all(
                (
                    "day" in self.start_date,
                    "month" in self.start_date,
                    "year" in self.start_date,
                )
            )
        ):
            start_date = Event.find(obj=self, name=self.possible_events[0])
            if not start_date:
                start_date = Event(obj=self, name=self.possible_events[0])
            start_date.day = (
                int(self.start_date["day"]) if self.start_date["day"].isdigit() else 0
            )
            start_date.month = (
                int(self.start_date["month"])
                if self.start_date["month"].isdigit()
                else 0
            )
            start_date.year = (
                int(self.start_date["year"]) if self.start_date["year"].isdigit() else 0
            )
            start_date.save()

            self.start_date = start_date
            # log(self.start_date)

        if (
            self.pk
            and isinstance(self.end_date, dict)
            and all(
                (
                    "day" in self.start_date,
                    "month" in self.start_date,
                    "year" in self.start_date,
                )
            )
        ):
            end_date = Event.find(obj=self, name=self.possible_events[-1])
            if not end_date:
                end_date = Event(obj=self, name=self.possible_events[0])
            end_date.day = (
                int(self.end_date["day"]) if self.end_date["day"].isdigit() else 0
            )
            end_date.month = (
                int(self.end_date["month"]) if self.end_date["month"].isdigit() else 0
            )
            end_date.year = (
                int(self.end_date["year"]) if self.end_date["year"].isdigit() else 0
            )
            end_date.save()
            self.end_date = end_date

        if (
            self.start_date
            and self.end_date
            and self.end_date.year != 0
            and self.start_date.year > self.end_date.year
        ):
            self.start_date.year = self.end_date.year - 1

    def pre_save_image(self):
        if isinstance(self.image, str):
            if validators.url(self.image):
                image = Image.from_url(
                    self.image,
                    prompt=self.image_prompt,
                    tags=[*self.image_tags],
                )
                image.save()
                self.image = image
            elif image := Image.get(self.image):
                self.image = image
            else:
                raise ValidationError(
                    f"Image must be an Image object, url, or Image pk, not {self.image}"
                )
        elif self.image and not self.image.tags:
            self.image.tags = self.image_tags
            self.image.save()
        # log(self.image)

    def pre_save_backstory(self):
        if not self.backstory:
            self.backstory = f"A {self.traits} {self.title}."
        self.backstory_summary = self.backstory_summary.replace("h1>", "h3>").replace(
            "h2>", "h3>"
        )

    def pre_save_traits(self):
        if not self.traits:
            self.traits = random.choice(self._traits_list)

    def post_save_journal(self):
        if not self.journal:
            self.journal = Journal(world=self.get_world(), parent=self)
            self.journal.save()
            self.save()

    def post_save_start_date(self):
        if not self.start_date:
            self.start_date = Event(obj=self, name=self._possible_events[0])
            self.start_date.save()
            self.save()
        else:
            self.start_date.obj = self
            self.start_date.name = self._possible_events[0]
            self.start_date.save()

    def post_save_end_date(self):
        if not self.end_date:
            self.end_date = Event(obj=self, name=self._possible_events[-1])
            self.end_date.save()
            self.save()
        else:
            self.end_date.obj = self
            self.end_date.name = self._possible_events[-1]
            self.end_date.save()
