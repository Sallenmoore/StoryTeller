import random

from bs4 import BeautifulSoup

from autonomous import log
from autonomous.ai.audioagent import AudioAgent
from autonomous.model.autoattr import (
    FileAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.images.image import Image
from models.ttrpgobject.character import Character


class AutoGMInitiativeAction(AutoModel):
    type = StringAttr(default="action", choices=["action", "bonus"])
    description = StringAttr(default="")
    attack_roll = IntAttr(default="")
    damage_roll = IntAttr(default="")
    saving_throw = IntAttr(default="")
    skill_check = IntAttr(default="")
    target = ReferenceAttr(choices=["Character", "Creature"])
    result = StringAttr(default="")

    def __str__(self):
        return f"{"\n".join([f"{k}:  {v}" for k, v in self.action_dict().items()])}"

    def is_bonus_action(self):
        return self.type == "bonus"

    def action_dict(self):
        rolls = {}
        if self.attack_roll:
            rolls["Attack Roll"] = self.attack_roll
        if self.damage_roll:
            rolls["Damage Roll"] = self.damage_roll
        if self.saving_throw:
            rolls["Saving Throw"] = self.saving_throw
        if self.skill_check:
            rolls["Skill Check"] = self.skill_check
        if self.target:
            rolls["Target"] = f"{self.target.name} [pk: {self.target.pk}]"
        rolls["Description"] = self.description
        return rolls


class AutoGMInitiative(AutoModel):
    actor = ReferenceAttr(choices=["Character", "Creature"])
    hp = IntAttr()
    status = StringAttr(default="")
    description = StringAttr(default="")
    image = ReferenceAttr(choices=[Image])
    audio = FileAttr()
    position = IntAttr(default=0)
    action = ReferenceAttr(choices=[AutoGMInitiativeAction])
    bonus_action = ReferenceAttr(choices=[AutoGMInitiativeAction])
    movement = StringAttr(default="")

    @property
    def max_hp(self):
        return self.actor.hitpoints

    @property
    def ready(self):
        return (
            self.action.description and self.bonus_action.description and self.movement
        )

    @property
    def scene_description(self):
        return f"""{self.description}
{self.action.result}
{self.bonus_action.result}
{self.movement}
"""

    def delete(self):
        for item in [self.action, self.bonus_action, self.image]:
            if item:
                item.delete()
        return super().delete()

    def add_action(
        self,
        description,
        attack_roll,
        damage_roll,
        saving_throw,
        skill_check,
        target,
        result="",
        bonus=False,
    ):
        from models.ttrpgobject.character import Character
        from models.ttrpgobject.creature import Creature

        """
        Add an action to the initiative object
        """
        if not isinstance(target, (Character, Creature)):
            # log(target, _print=True)
            target = Character.get(target) or Creature.get(target)
            # log(target, _print=True)
        log(result, _print=True)
        if bonus:
            if self.bonus_action:
                self.bonus_action.description = description
                self.bonus_action.attack_roll = attack_roll or 0
                self.bonus_action.damage_roll = damage_roll or 0
                self.bonus_action.saving_throw = saving_throw or 0
                self.bonus_action.skill_check = skill_check or 0
                self.bonus_action.target = target
                self.bonus_action.result = result or self.action.result
            else:
                self.bonus_action = AutoGMInitiativeAction(
                    type="bonus",
                    description=description,
                    attack_roll=attack_roll or 0,
                    damage_roll=damage_roll or 0,
                    saving_throw=saving_throw or 0,
                    skill_check=skill_check or 0,
                    target=target,
                    result=result,
                )
            self.bonus_action.save()
            log(self.bonus_action.result, _print=True)
        else:
            if self.action:
                self.action.description = description
                self.action.attack_roll = attack_roll or 0
                self.action.damage_roll = damage_roll or 0
                self.action.saving_throw = saving_throw or 0
                self.action.skill_check = skill_check or 0
                self.action.target = target
                self.action.result = result or self.action.result
                self.action.save()
            else:
                self.action = AutoGMInitiativeAction(
                    type="action",
                    description=description,
                    attack_roll=attack_roll or 0,
                    damage_roll=damage_roll or 0,
                    saving_throw=saving_throw or 0,
                    skill_check=skill_check or 0,
                    target=target,
                    result=result,
                )
            self.action.save()
            log(self.action.result, _print=True)
        self.save()

    def generate_audio(self, voice=None):
        if self.scene_description:
            description = BeautifulSoup(
                self.scene_description, "html.parser"
            ).get_text()
            voiced_result = AudioAgent().generate(description, voice=voice or "echo")
            if self.audio:
                self.audio.delete()
                self.audio.replace(voiced_result, content_type="audio/mpeg")
            else:
                self.audio.put(voiced_result, content_type="audio/mpeg")
            self.save()

    def generate_image(self, image_style):
        desc = f"""Based on the below description of the character, setting, and event in a scene of a {self.actor.genre} TTRPG combat round, generate a single graphic novel style panel in the art style of {image_style} for the scene.

DESCRIPTION OF CHARACTERS IN THE SCENE
-{self.actor.age} year old {self.actor.species} {self.actor.gender} {self.actor.archetype}. {self.actor.description_summary or self.actor.description}
- Motif: {self.actor.motif}
"""
        desc += f"""
SCENE DESCRIPTION
{self.scene_description}
"""
        log(desc, _print=True)
        img = Image.generate(
            desc,
            tags=[
                "scene",
                "combat",
                self.actor.name,
                self.actor.world.name,
                self.actor.genre,
            ],
        )
        img.save()
        self.image = img
        self.save()

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    # log("Auto Pre Save World")
    # super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_action()
        document.pre_save_bonus_action()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verification methods ##################

    def pre_save_action(self):
        if isinstance(self.action, str):
            self.action = None

    def pre_save_bonus_action(self):
        if isinstance(self.bonus_action, str):
            self.bonus_action = None

    def pre_save_actor(self):
        if isinstance(self.actor, Character) or not self.actor.group:
            self.actor.current_hp = self.hp
            self.actor.status = self.status
            self.actor.save()
        else:
            raise ValueError("Actor must be a character or creature")


class AutoGMInitiativeList(AutoModel):
    party = ReferenceAttr(choices=["Faction"])
    combatants = ListAttr(ReferenceAttr(choices=["Character", "Creature"]))
    allies = ListAttr(ReferenceAttr(choices=["Character", "Creature"]))
    order = ListAttr(ReferenceAttr(choices=[AutoGMInitiative]))
    current_round = IntAttr(default=1)
    current_turn = IntAttr(default=0)
    scene = ReferenceAttr(choices=["AutoGMScene"])

    @property
    def combat_ended(self):
        for ini in self.order:
            if ini.actor in self.combatants and ini.hp > 0:
                return False
        return True

    def delete(self):
        for item in self.order:
            item.delete()
        return super().delete()

    def index(self, combatant):
        return self.order.index(combatant)

    def start_combat(self):
        if self.order:
            for o in self.order:
                o.delete()
            self.order = []
        for actor in [*self.party.players, *self.combatants, *self.allies]:
            pos = random.randint(1, 20) + ((actor.dexterity - 10) // 2)
            ini = AutoGMInitiative(actor=actor, position=pos)
            ini.hp = (
                actor.current_hitpoints
                if actor in self.party.players
                else actor.hitpoints
            )
            ini.save()
            self.order += [ini]
        self.order.sort(key=lambda x: x.position, reverse=True)
        self.save()

    def current_combat_turn(self):
        # log(self.order, self.current_turn)
        ini_actor = self.order[self.current_turn]
        while not ini_actor.hp:
            self.current_turn = (self.current_turn + 1) % len(self.order)
            ini_actor = self.order[self.current_turn]
        self.save()
        return ini_actor

    def next_combat_turn(self):
        if self.combat_ended:
            return None
        self.current_turn = (self.current_turn + 1) % len(self.order)
        result = self.current_combat_turn()
        result.description = f"{result.actor.name} is up next."
        result.movement = ""
        if result.audio:
            result.audio.delete()
        if result.image:
            result.image.delete()
        result.save()
        if result.action:
            result.action.result = ""
            result.action.description = ""
            result.action.attack_roll = 0
            result.action.damage_roll = 0
            result.action.saving_throw = 0
            result.action.skill_check = 0
            result.action.save()
        if result.bonus_action:
            result.bonus_action.result = ""
            result.bonus_action.description = ""
            result.bonus_action.attack_roll = 0
            result.bonus_action.damage_roll = 0
            result.bonus_action.saving_throw = 0
            result.bonus_action.skill_check = 0
            result.bonus_action.save()
        return result
