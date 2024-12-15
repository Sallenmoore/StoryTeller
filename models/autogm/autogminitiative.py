import random

from bs4 import BeautifulSoup

from autonomous import log
from autonomous.model.autoattr import (
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
    position = IntAttr(default=0)
    action = ReferenceAttr(choices=[AutoGMInitiativeAction])
    bonus_action = ReferenceAttr(choices=[AutoGMInitiativeAction])
    movement = StringAttr(default="")

    @property
    def max_hp(self):
        return self.actor.hitpoints

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
            target = Character.get(target) or Creature.get(target)
        action = AutoGMInitiativeAction(
            type="bonus" if bonus else "action",
            description=description,
            attack_roll=attack_roll or 0,
            damage_roll=damage_roll or 0,
            saving_throw=saving_throw or 0,
            skill_check=skill_check or 0,
            target=target,
            result=result,
        )
        action.save()
        if bonus:
            self.bonus_action = action
        else:
            self.action = action
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
        # log(self.order)
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
        return self.current_combat_turn()
