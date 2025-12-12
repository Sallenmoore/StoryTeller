import os
import random

import markdown
import requests
import validators
from autonomous.model.autoattr import (
    DictAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from dmtoolkit import dmtools

from autonomous import log
from models.calendar.date import Date
from models.images.image import Image


class LoreScene(AutoModel):
    prompt = StringAttr(default="")
    summary = StringAttr(default="")
    situation = StringAttr(default="")
    setting = ReferenceAttr(choices=["Place"])
    date = ReferenceAttr(choices=["Date"])
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    responses = ListAttr(DictAttr())
    lore = ReferenceAttr(choices=["Lore"], require=True)

    def delete(self):
        if self.date:
            self.date.delete()
        super().delete()

    def summarize(self):
        prompt = f"""Based on the following:
{f"Summary of events: {self.lore.summary}" if self.lore.summary else ""}

The current situation: {self.situation}

CHARACTER RESPONSES:
{"\n".join([f"\n{member.name}: {member.history or member.backstory}\nRESPONSE:{self.get_response(member.name)}" for member in self.lore.party])}

Summarize the events so that that they can be added to the characters' history. Do not include any information about the characters' internal thoughts, only what actually happened. Do not worry about conciseness. Be sure not leave out any events that transpired, not matter how small.
"""
        log("Generating Lore Summary with prompt: " + prompt, _print=True)
        summary_result = self.lore.world.system.generate_text(
            prompt=prompt,
            primer="Rewrite the described events into a cohesive narrative based on the scenario information and character responses. Feel free to embellish for dramatic effect, but keep the same narrative structure, sequence of events, and do not leave out any events that transpired, not matter how small.",
        )
        if summary_result:
            log(f"Generated Lore Summary: {summary_result}", _print=True)
            self.summary = summary_result
            self.save()

    def get_response(self, character_name):
        for response in self.responses:
            if response.get("character_name") == character_name:
                return response
        return None

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                   ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_dates()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    def pre_save_dates(self):
        if self.pk and self.date.obj != self:
            self.date.obj = self
            self.date.save()


class Lore(AutoModel):
    name = StringAttr(default="")
    scope = StringAttr(default="Local", choices=["Local", "Regional", "Global", "Epic"])
    backstory = StringAttr(default="")
    guidance = StringAttr(
        default="Ensure consistency with the established timeline, responding appropriately for that period in the timeline."
    )
    situation = StringAttr(default="")
    setting = ReferenceAttr(choices=["Place"])
    start_date = ReferenceAttr(choices=["Date"])
    current_date = ReferenceAttr(choices=["Date"])
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    party = ListAttr(ReferenceAttr(choices=["Character"]))
    scenes = ListAttr(ReferenceAttr(choices=["LoreScene"]))
    story = ReferenceAttr(choices=["Story"])
    world = ReferenceAttr(choices=["World"], required=True)
    bbeg = ReferenceAttr(choices=["Character", "Faction"])

    funcobj = {
        "name": "generate_response",
        "description": "Generates a response from the party characters to the current described situation.",
        "parameters": {
            "type": "object",
            "properties": {
                "situation": {
                    "type": "string",
                    "description": "Suggest likely next scenes/scenarios based on the character's responses to the previous scenario and the setting information.",
                },
                "responses": {
                    "type": "array",
                    "description": "A list of responses from each party character to the current described situation. The responses should include the character's verbal response, thoughts, actions taken, and any relevant roll information. If there is more than one character in the party, provide responses for each character that show awareness of each other to create a dynamic interaction.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "character_name": {
                                "type": "string",
                                "description": "The full name of the character.",
                            },
                            "verbal_response": {
                                "type": "string",
                                "description": "The character's verbal response to the situation, if any. Otherwise an empty string.",
                            },
                            "thoughts": {
                                "type": "string",
                                "description": "The character's internal thoughts regarding the situation. Any plans or considerations they have.",
                            },
                            "actions_taken": {
                                "type": "string",
                                "description": "Any actions the character takes in response to the situation, if any. Otherwise an empty string.",
                            },
                            "roll_type": {
                                "type": "string",
                                "description": "The type of roll the character would make to respond to the situation (e.g., 'Persuasion', 'Intimidation', 'Stealth', etc.), if any. Otherwise an empty string.",
                            },
                            "roll_explanation": {
                                "type": "string",
                                "description": "The reasoning behind the chosen roll type and how it relates to the character's response, if any. Otherwise an empty string.",
                            },
                            "roll_formula": {
                                "type": "string",
                                "description": "The numerical formula of the roll the character makes in response to the situation (e.g. '1d20 + 5'). Only use the '#d## +/- #' format, with no other text, since this output will be used to calculate the result. Otherwise an empty string.",
                            },
                            "roll_bonuses": {
                                "type": "string",
                                "description": "The specific attribue/skill bonuses/abilities used for the roll (e.g. Notice:+2, Wisdom:+3, Fireball'), if any. Otherwise an empty string.",
                            },
                        },
                    },
                },
            },
        },
    }

    @property
    def calendar(self):
        return self.world.calendar

    @property
    def places(self):
        return [
            a
            for a in self.associations
            if a.model_name() in ["Region", "Location", "City", "Shop", "District"]
        ]

    @property
    def responses(self):
        return self.scenes[-1].responses if self.scenes else []

    @responses.setter
    def responses(self, rsps):
        if self.scenes:
            self.scenes[-1].responses = rsps
        else:
            ls = LoreScene(lore=self, responses=rsps)
            ls.save()
            self.scenes = [ls]
            self.save()

    @property
    def summary(self):
        result = ""
        result = self.scenes[-1].summary if self.scenes else ""
        log(result, _print=True)
        return result

    @property
    def last_summary(self):
        if len(self.scenes) > 1 and self.scenes[-2].summary:
            log(self.scenes[-2].summary, _print=True)
            return self.scenes[-2].summary
        return self.summary

    ############# CRUD #############

    def delete(self):
        if self.start_date:
            self.start_date.delete()
        if self.current_date:
            self.current_date.delete()
        for scene in self.scenes:
            scene.delete()
        super().delete()

    ############# image generation #############
    def generate(self):
        prompt = f"""The goal is to develop the historical Lore of the character, places, and things in a TTRPG world by 'acting out' their roles and interactions to the described situation and events. Your task is to respond to the presented situation as the party characters would, based on their histories and personalities. You will be provided with specific scenario context, and your responses should reflect that context. The events describe may be in the past or present, but should always be consistent with the worlds's established history and current state.

WORLD NAME: {self.world.name}
WORLD CURRENT DATE: {self.current_date}
WORLD's HISTORY:
{self.world.history}

LORE SCENARIO START DATE: {self.start_date}
LORE SCENARIO CURRENT DATE: {self.current_date}
"""
        if self.story:
            prompt += f"\n\nThe lore is part of the following storylines: \n{self.story.name}: {self.story.summary or self.story.backstory}."

        if self.party:
            prompt += "\n\nThe party consists of the following characters: "
            for member in self.party:
                prompt += f"\n- {member.name}: {member.history or member.backstory}. SKILLS: {member.skills} ABILITIES: {member.abilities}"

        if self.associations:
            prompt += "\n\nHere are some additional elements related to this lore: "
            for assoc in self.associations:
                if assoc not in [*self.party, self.setting, self.world]:
                    prompt += f"\n\n{assoc.name}: {assoc.history or assoc.backstory}."

        if self.summary:
            prompt += f"\n\nThe lore we are currently working on has the following summary: {self.summary}."

        prompt += f"""
The party should respond to the following:

{f"CURRENT SETTING:{self.setting.name}:  {self.setting.description} {self.setting.backstory}" if self.setting else ""}.

{f"CONTEXT GUIDANCE: {self.guidance}" if self.guidance else ""}

NEXT SCENE: {self.situation}.
"""

        log("Generating Expanded Lore with prompt: " + prompt, _print=True)
        result = self.world.system.generate_json(
            prompt=prompt,
            primer=f"Create expanded lore that fits into the described world. Respond in JSON format consistent with this structure: {self.funcobj['parameters']}.",
            funcobj=self.funcobj,
        )
        if result.get("responses"):
            log(f"Generated Lore: {result}", _print=True)
            for resp in result["responses"]:
                try:
                    resp["roll_result"] = (
                        dmtools.dice_roll(resp["roll_formula"])
                        if resp.get("roll_formula")
                        else 0
                    )
                except Exception as e:
                    log(
                        f"Error rolling dice for formula {resp.get('roll_formula')}: {e}",
                        _print=True,
                    )
            ls = LoreScene(
                lore=self,
                prompt=prompt,
                setting=self.setting,
                associations=self.associations,
                situation=self.situation,
                date=self.current_date.copy(self),
                responses=result["responses"],
            )
            ls.save()
            self.scenes += [ls]
            self.situation = result.get("situation", "")
            self.save()
            requests.post(
                f"http://{os.environ.get('TASKS_SERVICE_NAME')}:{os.environ.get('COMM_PORT')}/generate/lore/{ls.pk}/summary"
            )
        else:
            log("Failed to generate Lore", _print=True)

    def get_response(self, character_name):
        return self.scenes[-1].get_response(character_name) if self.scenes else {}

    ############# Association Methods #############
    # MARK: Associations
    def add_association(self, obj):
        # log(len(self.associations), obj in self.associations)
        if obj not in self.associations:
            self.associations += [obj]
            self.save()
        return obj

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                   ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_setting()
        document.pre_save_dates()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    def pre_save_setting(self):
        if isinstance(self.setting, str):
            self.setting = self.world.get_model(*self.setting.split("/"))

    def pre_save_dates(self):
        if self.pk:
            for date_attr in ["start_date", "current_date"]:
                date = getattr(self, date_attr)
                if isinstance(date, dict):
                    date = self.calendar.date(self, **date)
                elif not date:
                    date = Date(
                        obj=self,
                        calendar=self.calendar,
                        day=random.randint(1, 28),
                        month=random.randrange(len(self.calendar.months) or 12),
                        year=0,
                    )
                    date.save()
                else:
                    if date.obj != self:
                        date.obj = self
                    if date.day <= 0:
                        setattr(self, date_attr, random.randint(1, 28))
                    if date.month < 0:
                        setattr(self, date_attr, random.randint(0, 11))
                    date.save()
                setattr(self, date_attr, date)
            for date in Date.search(obj=self):
                if date not in [self.start_date, self.current_date]:
                    date.delete()
