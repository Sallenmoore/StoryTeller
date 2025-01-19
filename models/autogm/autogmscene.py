import os
import random

import requests
from bs4 import BeautifulSoup

from autonomous import log
from autonomous.ai.audioagent import AudioAgent
from autonomous.model.autoattr import (
    BoolAttr,
    DictAttr,
    FileAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.autogm.autogminitiative import AutoGMInitiativeList
from models.autogm.autogmmessage import AutoGMMessage
from models.autogm.autogmquest import AutoGMQuest
from models.images.image import Image
from models.ttrpgobject.character import Character
from models.ttrpgobject.creature import Creature
from models.ttrpgobject.item import Item


class AutoGMScene(AutoModel):
    gm_ready = BoolAttr(default=False)
    campaign = ReferenceAttr(choices=["Campaign"])
    type = StringAttr(
        choices=[
            "social",
            "encounter",
            "combat",
            "investigation",
            "exploration",
            "stealth",
            "puzzle",
        ]
    )
    description = StringAttr(default="")
    next_actions = ListAttr(StringAttr(default=""))
    tone = StringAttr(
        default="Noblebright",
        choices=["Noblebright", "Grimdark", "Gilded", "Heroic", "Fairytale"],
    )
    summary = StringAttr()
    date = StringAttr()
    prompt = StringAttr()
    player_messages = ListAttr(ReferenceAttr(choices=["AutoGMMessage"]))
    party = ReferenceAttr(choices=["Faction"])
    npcs = ListAttr(ReferenceAttr(choices=["Character"]))
    combatants = ListAttr(ReferenceAttr(choices=["Creature"]))
    loot = ListAttr(ReferenceAttr(choices=["Item"]))
    places = ListAttr(ReferenceAttr(choices=["Place"]))
    factions = ListAttr(ReferenceAttr(choices=["Faction"]))
    vehicles = ListAttr(ReferenceAttr(choices=["Vehicle"]))
    initiative = ReferenceAttr(choices=["AutoGMInitiativeList"])
    roll_required = BoolAttr(default=False)
    roll_type = StringAttr()
    roll_formula = StringAttr()
    roll_attribute = StringAttr()
    roll_description = StringAttr()
    roll_result = IntAttr()
    roll_player = ReferenceAttr(choices=["Character", "Creature"])
    roll_audio = FileAttr()
    image = ReferenceAttr(choices=[Image])
    image_style = StringAttr(
        default=lambda: random.choice(
            ["Jim Lee", "Brian Bendis", "Jorge Jiménez", "Bilquis Evely", "Sana Takeda"]
        )
    )
    image_prompt = StringAttr()
    audio = FileAttr()
    music_ = StringAttr(
        default="theme",
        choices=[
            "battle",
            "suspense",
            "celebratory",
            "restful",
            "creepy",
            "relaxed",
            "skirmish",
            "themesong",
        ],
    )
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    current_quest = ReferenceAttr(choices=[AutoGMQuest])
    quest_log = ListAttr(ReferenceAttr(choices=[AutoGMQuest]))
    gm_mode = StringAttr(default="manual", choices=["manual", "pc", "gm"])

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
        return f"/static/sounds/music/{self.music_}{random.randint(1, 2)}.mp3"

    @music.setter
    def music(self, value):
        self.music_ = value

    @property
    def player(self):
        members = self.party.characters
        return members[0] if members else None

    @property
    def is_ready(self):
        return [p.player for p in self.player_messages if p.ready]

    @is_ready.setter
    def is_ready(self, value):
        self.save()
        for p in self.player_messages:
            p.ready = bool(value)
            p.save()

    def add_association(self, obj):
        if obj not in self.associations:
            self.associations += [obj]
        self.save()

    def remove_association(self, obj):
        if obj in self.associations:
            self.associations.remove(obj)
            self.save()

    def generate_audio(self, voice=None, pre_text="", post_text=""):
        from models.world import World

        if not self.description:
            raise ValueError("Scene Description are required to generate audio")
        description = f"""
{pre_text} {self.description} {post_text}

{"Now you must decide on the next course of action:" if self.next_actions else ""}

{"...\n\n Or, ".join(self.next_actions)}

{"Or you may decide your own path." if self.next_actions else "What are you going to do?"}
"""
        description = BeautifulSoup(description, "html.parser").get_text()
        voiced_scene = AudioAgent().generate(description, voice=voice or "onyx")
        if self.audio:
            self.audio.delete()
            self.audio.replace(voiced_scene, content_type="audio/mpeg")
        else:
            self.audio.put(voiced_scene, content_type="audio/mpeg")
        self.save()

    def generate_image(self, image_prompt=None):
        from models.world import World

        # log("image prompt:", image_prompt, _print=True)
        self.image_prompt = f"""Based on the below description of characters, setting, and events in a scene of a {self.party.genre} TTRPG session, generate a single graphic novel style panel in the art style of {self.image_style} for the scene.

DESCRIPTION OF CHARACTERS IN THE SCENE
"""
        characters = [self.roll_player] if self.roll_player else self.party.players
        for char in characters:
            description = (
                char.description
                if len(char.description.split()) < 100
                else char.description_summary
            )
            self.image_prompt += f"""
- {char.age} year old {char.species} {char.gender} {char.occupation}. {description}
    - Motif: {char.motif}
    - Looks Like: {char.lookalike}
"""
        self.image_prompt += f"""

SCENE DESCRIPTION

{image_prompt or self.description}
"""
        img = Image.generate(
            self.image_prompt,
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
                    species=obj["species"],
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

    def scene_objects(self):
        return [
            *self.npcs,
            *self.combatants,
            *self.loot,
            *self.vehicles,
            *self.places,
            *self.factions,
        ]

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
            *self.vehicles,
            *self.places,
            *self.factions,
        ]
        for o in scene_objects:
            if o not in self.associations:
                self.associations += [o]
        self.save()
        return [o for o in self.associations if o not in scene_objects]

    def get_player_message(self, player):
        if isinstance(player, str):
            player = Character.get(player)
        result = None
        for msg in self.player_messages:
            if msg.player == player:
                result = msg
        if not result:
            result = AutoGMMessage(player=player, scene=self)
            result.save()
            self.player_messages += [result]
            self.save()
        return result

    def set_player_messages(self, messages):
        for msg in messages:
            if msg.get("character_pk"):
                self.set_player_message(
                    msg["character_pk"], msg["response"], msg["intent"], msg["emotion"]
                )

    def set_player_message(
        self, character, response=None, intent=None, emotion="steady", ready=False
    ):
        player = (
            character if isinstance(character, Character) else Character.get(character)
        )
        if pc_msg := self.get_player_message(player):
            pc_msg.message = response if response is not None else pc_msg.message
            pc_msg.intent = intent if intent is not None else pc_msg.intent
            pc_msg.emotion = emotion if emotion is not None else pc_msg.emotion
            pc_msg.ready = ready
            pc_msg.save()
        else:
            raise ValueError("Player Message not found")
        log(pc_msg.message, pc_msg.intent, pc_msg.emotion, pc_msg.ready)
        return pc_msg

    ########################################################
    ##                    COMBAT METHODS                  ##
    ########################################################

    def start_combat(self):
        if self.initiative:
            self.initiative.delete()

        if not self.combatants:
            return

        combatants = []
        for cbt in self.combatants:
            combatants += ([cbt] * random.randint(1, cbt.group)) if cbt.group else [cbt]
        self.initiative = AutoGMInitiativeList(
            party=self.party,
            combatants=combatants,
            allies=self.npcs,
            scene=self,
        )
        self.initiative.save()
        self.save()
        self.initiative.start_combat()

    def current_combat_turn(
        self,
        hp=None,
        status=None,
        movement=None,
        action_target=None,
        action=None,
        action_attack_roll=None,
        action_dmg_roll=None,
        action_saving_throw=None,
        action_skill_check=None,
        bonus_action_target=None,
        bonus_action=None,
        bonus_action_attack_roll=None,
        bonus_action_dmg_roll=None,
        bonus_action_saving_throw=None,
        bonus_action_skill_check=None,
    ):
        """
        Handles the current combat turn by updating the combatant's state and actions.
        Parameters:
        hp (int, optional): The hit points of the combatant.
        status (str, optional): The status of the combatant.
        movement (int, optional): The movement points of the combatant.
        action_target (int, optional): The target of the main action.
        action (str, optional): The description of the main action.
        action_attack_roll (int, optional): The attack roll of the main action.
        action_dmg_roll (int, optional): The damage roll of the main action.
        action_saving_throw (int, optional): The saving throw of the main action.
        action_skill_check (int, optional): The skill check of the main action.
        bonus_action_target (int, optional): The target of the bonus action.
        bonus_action (str, optional): The description of the bonus action.
        bonus_action_attack_roll (int, optional): The attack roll of the bonus action.
        bonus_action_dmg_roll (int, optional): The damage roll of the bonus action.
        bonus_action_saving_throw (int, optional): The saving throw of the bonus action.
        bonus_action_skill_check (int, optional): The skill check of the bonus action.
        Returns:
        object: The current combat turn object with updated state and actions.
        """
        if not self.initiative or not self.initiative.order:
            self.start_combat()

        if cct := self.initiative.current_combat_turn():
            if action:
                # log(self.initiative.order, action_target, _print=True)
                target = [
                    ini
                    for ini in self.initiative.order
                    if str(ini.pk) == str(action_target)
                ]
                cct.add_action(
                    description=action,
                    attack_roll=action_attack_roll,
                    damage_roll=action_dmg_roll,
                    saving_throw=action_saving_throw,
                    skill_check=action_skill_check,
                    target=target[0] if target else None,
                )
                # log(cct.action)
            if bonus_action:
                target = [
                    ini
                    for ini in self.initiative.order
                    if str(ini.pk) == str(bonus_action_target)
                ]
                cct.add_action(
                    description=bonus_action,
                    attack_roll=bonus_action_attack_roll,
                    damage_roll=bonus_action_dmg_roll,
                    saving_throw=bonus_action_saving_throw,
                    skill_check=bonus_action_skill_check,
                    target=target[0] if target else None,
                    bonus=True,
                )
                # log(cct.bonus_action)

            if hp is not None:
                cct.hp = int(hp)
            if status is not None:
                cct.status = status
            if movement is not None:
                cct.movement = movement
            cct.save()
        # log(cct, print=True)
        return cct

    def next_combat_turn(self):
        """
        Advances to the next combat turn if combat is ongoing, otherwise switches to investigation mode.
        If the initiative is active and combat has not ended, this method will call the `next_combat_turn`
        method on the initiative object to proceed to the next turn. If the combat has ended or there is
        no active initiative, it will change the type to "investigation" and save the current state.
        Returns:
            The result of `initiative.next_combat_turn()` if combat is ongoing, otherwise None.
        """

        if self.initiative and not self.initiative.combat_ended:
            return self.initiative.next_combat_turn()
        else:
            self.type = "investigation"
            self.save()

    def remove_initiative(self, cbtpk):
        for idx, ini in enumerate(self.initiative.order):
            if str(ini.pk) == str(cbtpk):
                ini.delete()
                del self.initiative.order[idx]
                break

    def initiative_index(self, combatant):
        """
        Get the index of a combatant in the initiative order.
        Args:
            combatant (object): The combatant whose index in the initiative order is to be found.
        Returns:
            int: The index of the combatant in the initiative list.
        Raises:
            ValueError: If the combatant is not found in the initiative list.
        """

        return self.initiative.index(combatant)

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     # log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        """
        Automatically called before saving a document to perform pre-save operations.
        This method is intended to be used as a pre-save signal handler for a document.
        It performs several pre-save operations such as handling associations, private
        messages, and rolls. Additionally, it ensures that the document's music attribute
        is set to a valid value.
        Args:
            cls (type): The class that this method is bound to.
            sender (type): The model class that sent the signal.
            document (object): The document instance that is being saved.
            **kwargs: Additional keyword arguments.
        Operations:
            - Calls the superclass's auto_pre_save method.
            - Calls the document's pre_save_associations method.
            - Calls the document's pre_save_pcmessages method.
            - Calls the document's pre_save_rolls method.
            - Ensures the document's music attribute is set to a valid value, defaulting to "themesong" if not.
        """

        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_associations()
        document.pre_save_rolls()
        if document.music_ not in [
            "battle",
            "suspense",
            "celebratory",
            "restful",
            "creepy",
            "relaxed",
            "skirmish",
            "themesong",
        ]:
            document.music_ = "themesong"

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)
        document.post_save_pcmessages()

    # def clean(self):
    #     super().clean()

    ################### verification methods ##################

    def pre_save_associations(self):
        """
        Prepares the associations, NPCs, combatants, loot, places, and factions
        by removing duplicates and sorting them.
        This method performs the following steps:
        1. Removes duplicate entries from the associations, NPCs, combatants, loot, places, and factions lists.
        2. Sorts the associations list by the title and name attributes.
        Returns:
            None
        """

        self.associations = list(set(self.associations))
        self.npcs = list(set(self.npcs))
        self.combatants = list(set(self.combatants))
        self.loot = list(set(self.loot))
        self.places = list(set(self.places))
        self.factions = list(set(self.factions))
        self.associations.sort(key=lambda x: (x.title, x.name))

    def post_save_pcmessages(self):
        """
        Pre-save player messages for the scene.
        This method iterates over all players in the party and checks if a message
        for each player already exists. If a message does not exist, it creates a new
        AutoGMMessage for the player and the current scene, saves it, and adds it to
        the player_messages list.
        Attributes:
            self (AutoGMScene): The instance of the AutoGMScene class.
        Methods:
            get_player_message(player): Checks if a message for the given player exists.
            AutoGMMessage(player, scene): Creates a new AutoGMMessage instance.
            save(): Saves the AutoGMMessage instance.
        """

        for player in self.party.players:
            if not self.get_player_message(player):
                msg = AutoGMMessage(player=player, scene=self)
                msg.save()
                self.player_messages += [msg]
                self.save()

    def pre_save_rolls(self):
        """
        Attempts to convert the roll_result attribute to an integer before saving.
        If the conversion fails, logs the exception and the current roll_result,
        then sets roll_result to 0.
        Raises:
            Exception: If an error occurs during the conversion of roll_result.
        Logs:
            The exception and the current roll_result if the conversion fails.
        """

        try:
            self.roll_result = int(self.roll_result)
        except Exception:
            self.roll_result = 0
