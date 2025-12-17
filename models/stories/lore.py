import os
import random

import requests
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
from models.audio.audio import Audio
from models.calendar.date import Date
from models.utility.parse_attributes import parse_text


class LoreResponse(AutoModel):
    obj = ReferenceAttr(choices=["Character"], required=True)
    scene = ReferenceAttr(choices=["LoreScene"])
    verbal = StringAttr(default="")
    verbal_audio = ReferenceAttr(choices=["Audio"])
    thoughts = StringAttr(default="")
    thoughts_audio = ReferenceAttr(choices=["Audio"])
    actions = StringAttr(default="")
    actions_audio = ReferenceAttr(choices=["Audio"])
    roll_type = StringAttr(default="")
    roll_explanation = StringAttr(default="")
    roll_formula = StringAttr(default="")
    roll_bonuses = StringAttr(default="")
    roll_result = IntAttr(default=0)

    def delete(self):
        if self.verbal_audio:
            self.verbal_audio.delete()
        if self.thoughts_audio:
            self.thoughts_audio.delete()
        if self.actions_audio:
            self.actions_audio.delete()
        super().delete()

    def roll(self):
        try:
            if self.roll_formula:
                self.roll_result = dmtools.dice_roll(self.roll_formula)
                self.save()
        except Exception as e:
            log(f"Error rolling dice for formula {self.roll_formula}: {e}", _print=True)

    def generate_audio(self):
        # log(
        #     f"Generating audio for LoreResponse of {self.obj.name} with voice {voice}",
        #     _print=True,
        # )
        if self.verbal and not self.verbal_audio:
            if audio := self.obj.speak(message=self.verbal):
                self.verbal_audio = audio
                self.save()
        if self.thoughts and not self.thoughts_audio:
            if audio := self.obj.speak(message=self.thoughts):
                self.thoughts_audio = audio
                self.save()
        if self.actions and not self.actions_audio:
            if audio := self.obj.speak(message=self.actions):
                self.actions_audio = audio
                self.save()
        # log(
        #     f"Finished generating audio for LoreResponse of {self.obj.name}: verbal_audio={self.verbal_audio}, thoughts_audio={self.thoughts_audio}, actions_audio={self.actions_audio}",
        #     _print=True,
        # )


class LoreScene(AutoModel):
    party = ListAttr(ReferenceAttr(choices=["Character"]))
    image = ReferenceAttr(choices=["Image"])
    prompt = StringAttr(default="")
    summary = StringAttr(default="")
    summary_audio = ReferenceAttr(choices=["Audio"])
    situation = StringAttr(default="")
    setting = ReferenceAttr(choices=["Place"])
    date = ReferenceAttr(choices=["Date"])
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    responses = ListAttr(ReferenceAttr(choices=["LoreResponse"]))
    lore = ReferenceAttr(choices=["Lore"], require=True)

    def delete(self):
        if self.date:
            self.date.delete()
        for r in self.responses:
            if isinstance(r, LoreResponse):
                r.delete()
        super().delete()

    def summarize(self):
        prompt = f"""in MARKDOWN, summarize the below scenario details as a detailed historical record. Do not include any information about the characters' internal thoughts, only what actually happened. Do not worry about conciseness. Be sure not leave out any events that transpired, not matter how small.
{f"Summary of events up to current situation: {self.lore.last_summary}" if self.lore.last_summary else ""}

The current situation: {self.situation}

CHARACTER RESPONSES:
{"\n".join([f"\n{member.name}: {member.history or member.backstory}\nRESPONSE:{self.get_response(member.name)}" for member in self.party])}
"""
        log("Generating Lore Summary with prompt: " + prompt, _print=True)
        summary_result = self.lore.world.system.generate_text(
            prompt=prompt,
            primer="Rewrite the described events into a cohesive narrative based on the scenario information and character responses. Feel free to embellish for dramatic effect, but keep the same narrative structure, sequence of events, and do not leave out any events that transpired, not matter how small.",
        )
        if summary_result:
            log(f"Generated Lore Summary: {summary_result}", _print=True)
            self.summary = parse_text(self, summary_result)
            self.save()
            self.summary_audio = Audio.tts(
                audio_text=self.summary,
                voice=random.choice(self.party).voice,
            )
            self.save()

    def get_response(self, character_name):
        for response in self.responses:
            if response.obj.name == character_name:
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

        #### MIGRATION CODE - REMOVE AFTERWARDS ####
        if not document.party and document.lore and document.lore.party:
            document.party = document.lore.party
        #############################################
        document.pre_save_dates()
        document.pre_save_responses()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    def pre_save_dates(self):
        if self.pk and self.date.obj != self:
            self.date.obj = self
            self.date.save()

    def pre_save_responses(self):
        for idx, response in enumerate(self.responses):
            if isinstance(response, dict):
                obj = [
                    member
                    for member in self.party
                    if member.name == response.get("character_name")
                ][0]
                lr = LoreResponse(obj=obj, scene=self, **response)
                lr.roll()
                lr.save()
                self.responses[idx] = lr


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
                            "verbal": {
                                "type": "string",
                                "description": "The character's verbal response to the situation, if any. Otherwise an empty string.",
                            },
                            "thoughts": {
                                "type": "string",
                                "description": "The character's internal thoughts regarding the situation. Any plans or considerations they have.",
                            },
                            "actions": {
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
    def events(self):
        return [e for e in self.world.events if e.date and e.date <= self.current_date]

    @property
    def image(self):
        return self.scenes[-1].image if self.scenes else None

    @property
    def geneology(self):
        return [self.world, self.story]

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

    @property
    def summary(self):
        result = ""
        i = -1
        scenes = self.scenes[::]
        while not result and scenes:
            result = scenes[i].summary if scenes else ""
            i -= 1
            scenes = scenes[:-1]
        return result

    @property
    def summary_audio(self):
        return self.scenes[-1].summary_audio if self.scenes else None

    @property
    def last_summary(self):
        if len(self.scenes) > 1 and self.scenes[-2].summary:
            return self.scenes[-2].summary
        return self.summary

    @property
    def last_summary_audio(self):
        return self.scenes[-2].summary_audio if len(self.scenes) > 1 else None

    @property
    def history(self):
        return self.summary

    @property
    def system(self):
        return self.world.system

    @property
    def path(self):
        return f"lore/{self.pk}"

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
            ls = LoreScene(
                lore=self,
                prompt=prompt,
                setting=self.setting,
                associations=self.associations,
                situation=self.situation,
                date=self.current_date.copy(self),
            )
            ls.save()
            self.scenes += [ls]
            self.save()
            for resp in result["responses"]:
                log(f"Response: {resp}", _print=True)
                obj = [
                    member
                    for member in self.party
                    if member.name == resp.get("character_name")
                ][0]
                lr = LoreResponse(obj=obj, scene=ls)
                lr.verbal = resp.get("verbal", "")
                lr.thoughts = resp.get("thoughts", "")
                lr.actions = resp.get("actions", "")
                lr.roll_type = resp.get("roll_type", "")
                lr.roll_explanation = resp.get("roll_explanation", "")
                lr.roll_formula = resp.get("roll_formula", "")
                lr.roll_bonuses = resp.get("roll_bonuses", "")
                lr.roll()
                lr.save()
                if resp := ls.get_response(obj.name):
                    resp.delete()
                ls.responses += [lr]
                ls.save()
                lr.generate_audio()
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
        document.pre_save_associations()
        document.pre_save_dates()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()
    def pre_save_associations(self):
        for char in [self.setting, self.bbeg, *self.party]:
            if char and char not in self.associations:
                self.associations += [char]

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
