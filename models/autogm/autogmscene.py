import os
import random

import requests
from bs4 import BeautifulSoup

from autonomous import log
from autonomous.ai.audioagent import AudioAgent
from autonomous.model.autoattr import (
    BoolAttr,
    FileAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.autogm.autogmmessage import AutoGMMessage
from models.autogm.autogmquest import AutoGMQuest
from models.images.image import Image
from models.ttrpgobject.character import Character
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.item import Item


class AutoGMScene(AutoModel):
    type = StringAttr(choices=["social", "combat", "exploration", "stealth"])
    description = StringAttr(default="")
    summary = StringAttr()
    date = StringAttr()
    prompt = StringAttr()
    player_messages = ListAttr(ReferenceAttr(choices=["AutoGMMessage"]))
    party = ReferenceAttr(choices=["Faction"])
    npcs = ListAttr(ReferenceAttr(choices=["Character"]))
    combatants = ListAttr(ReferenceAttr(choices=["Creature"]))
    loot = ListAttr(ReferenceAttr(choices=["Item"]))
    places = ListAttr(ReferenceAttr(choices=["Place"]))
    roll_required = BoolAttr()
    roll_type = StringAttr()
    roll_formula = StringAttr()
    roll_attribute = StringAttr()
    roll_description = StringAttr()
    roll_result = IntAttr()
    roll_player = ReferenceAttr(choices=["Character", "Creature"])
    image = ReferenceAttr(choices=[Image])
    image_prompt = StringAttr()
    audio = FileAttr()
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    current_quest = ReferenceAttr(choices=[AutoGMQuest])
    quest_log = ListAttr(ReferenceAttr(choices=[AutoGMQuest]))
    gm_mode = StringAttr(default="pc", choices=["pc", "gm"])

    def delete(self):
        if self.image:
            self.image.delete()
        for m in self.player_messages:
            m.delete()
        for q in self.quest_log:
            q.delete()
        return super().delete()

    @property
    def music(self):
        return f"/static/sounds/music/{random.choice(self.system._music_lists.get(type, ["themesong.mp3"]))}"

    @property
    def player(self):
        members = self.party.characters
        return members[0] if members else None

    def add_association(self, obj):
        if obj not in self.associations:
            self.associations += [obj]
        self.save()

    def remove_association(self, obj):
        if obj in self.associations:
            self.associations.remove(obj)
            self.save()

    def generate_audio(self, voice=None):
        from models.world import World

        if not self.description:
            raise ValueError("Scene Description are required to generate audio")

        description = BeautifulSoup(self.description, "html.parser").get_text()
        voiced_scene = AudioAgent().generate(description, voice=voice or "echo")
        if self.audio:
            self.audio.delete()
            self.audio.replace(voiced_scene, content_type="audio/mpeg")
        else:
            self.audio.put(voiced_scene, content_type="audio/mpeg")
        self.save()

    def generate_player_audio(self):
        for msg in self.player_messages:
            msg.generate_audio()

    def generate_image(self, image_prompt):
        from models.world import World

        log("image prompt:", image_prompt, _print=True)
        self.image_prompt = image_prompt
        desc = f"""Based on the below description of characters, setting, and events in a scene of a {self.party.genre} TTRPG session, generate a single graphic novel style panel in the art style of {random.choice(['Jim Lee', 'Brian Bendis', 'Jorge Jiménez', 'Bilquis Evely', 'Sana Takeda'])} for the scene.

DESCRIPTION OF CHARACTERS IN THE SCENE
"""

        for char in self.party.players:
            desc += f"""
-{char.age} year old {char.race} {char.gender} {char.occupation}. {char.description_summary or char.description}
    - Motif: {char.motif}
"""
        desc += f"""
SCENE DESCRIPTION
{self.image_prompt}
"""
        img = Image.generate(
            desc,
            tags=[
                "scene",
                self.party.name,
                self.party.world.name,
                self.party.genre,
            ],
        )
        img.save()
        self.image = img
        self.save()

    def get_npcs(self):
        return [c for c in self.npcs if c not in self.party.players]

    def generate_npcs(self, objs):
        if not objs:
            return
        for obj in objs:
            first_name = obj["name"].split()[0]
            last_name = obj["name"].split()[-1]
            npc = [
                c
                for c in Character.search(world=self.party.world, name=first_name)
                if last_name in c.name
            ]
            char = npc[0] if npc else []
            if not char:
                char = Character(
                    world=self.party.world,
                    race=obj["species"],
                    name=obj["name"],
                    desc=obj["description"],
                    backstory=obj["backstory"],
                )
                char.save()
                self.associations += [char]
                self.npcs += [char]
                self.save()
                requests.post(
                    f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
                )

    def generate_combatants(self, objs):
        if not objs:
            return
        for obj in objs:
            first_name = obj["name"].split()[0]
            last_name = obj["name"].split()[-1]
            npc = [
                c
                for c in Creature.search(world=self.party.world, name=first_name)
                if last_name == first_name or last_name in c.name
            ]
            char = npc[0] if npc else []

            if not char:
                char = Creature(
                    world=self.party.world,
                    type=obj["combatant_type"],
                    name=obj["name"],
                    desc=obj["description"],
                )
                char.save()
                self.associations += [char]
                self.combatants += [char]
                self.save()
                requests.post(
                    f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
                )

    def generate_loot(self, objs):
        if not objs:
            return
        for obj in objs:
            first_name = obj["name"].split()[0]
            last_name = obj["name"].split()[-1]
            item = [
                c
                for c in Item.search(world=self.party.world, name=first_name)
                if last_name == first_name or last_name in c.name
            ]
            char = item[0] if item else []

            if not char:
                char = Item(
                    world=self.party.world,
                    rarity=obj["rarity"],
                    name=obj["name"],
                    desc=obj["description"],
                    features=obj["attributes"],
                )
                char.save()
                self.associations += [char]
                self.loot += [char]
                self.save()
                requests.post(
                    f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
                )

    def generate_places(self, objs):
        from models.world import World

        if not objs:
            return
        for obj in objs:
            Model = None
            if obj["location_type"] == "poi":
                obj["location_type"] = "location"
            for key, val in self.party.system._titles.items():
                if val.lower() == obj["location_type"].lower():
                    Model = AutoModel.load_model(key)
                    break
            if Model:
                first_name = obj["name"].split()[0]
                last_name = obj["name"].split()[-1]
                char = None
                for c in Model.search(world=self.party.world, name=first_name):
                    if last_name == first_name or last_name in c.name:
                        char = c
                        break
                if not char:
                    char = Model(
                        world=self.party.world,
                        name=obj["name"],
                        desc=obj["description"],
                        backstory=obj["backstory"],
                    )
                    char.save()
                    self.associations += [char]
                    self.places += [char]
                    self.save()
                    requests.post(
                        f"http://tasks:{os.environ.get('COMM_PORT')}/generate/{char.path}"
                    )

    def get_additional_associations(self):
        """
        Retrieves additional associations that are not part of the current scene objects.
        This method first combines all scene objects from the party, NPCs, combatants, and loot.
        It then checks if each object is already in the associations list, and if not, adds it.
        Finally, it saves the updated associations and returns a list of associations that are not part of the scene objects.
        Returns:
            list: A list of associations that are not part of the current scene objects.
        """

        scene_objects = [
            *self.party.players,
            *self.npcs,
            *self.combatants,
            *self.loot,
            *self.places,
        ]
        for o in scene_objects:
            if o not in self.associations:
                self.associations += [o]
        self.save()
        return [o for o in self.associations if o not in scene_objects]

    def get_player_message(self, player):
        for msg in self.player_messages:
            if msg.player == player:
                return msg

    def set_player_messages(self, messages):
        for msg in messages:
            self.set_player_message(
                msg["playerpk"], msg["message"], msg["intent"], msg["emotion"]
            )

    def set_player_message(self, character_pk, response, intention, emotion):
        player = Character.get(character_pk)
        if pc_msg := self.get_player_message(player):
            pc_msg.message = response
            pc_msg.intent = intention
            pc_msg.emotion = emotion
            pc_msg.save()
        else:
            pc_msg = AutoGMMessage(
                player=player,
                scene=self,
                message=response,
                intent=intention,
                emotion=emotion,
            )
            pc_msg.save()
            self.player_messages += [pc_msg]
            self.save()
        # log(self.pk, player.name, player.pk, message, _print=True)

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    @classmethod
    def auto_post_init(cls, sender, document, **kwargs):
        # log("Auto Pre Save World")
        super().auto_post_init(sender, document, **kwargs)
        # if not isinstance(document.player_messages, list):
        #     document.player_messages = []

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_associations()
        document.pre_save_pcmessages()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verification methods ##################

    def pre_save_associations(self):
        self.associations.sort(key=lambda x: (x.title, x.name))

    def pre_save_pcmessages(self):
        if not isinstance(self.player_messages, list):
            self.player_messages = []
