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


class AutoGMInitiativeAction(AutoModel):
    type = StringAttr(default="action", choices=["action", "bonus"])
    description = StringAttr(default="")
    attack_roll = IntAttr(default="")
    damage_roll = IntAttr(default="")
    saving_throw = IntAttr(default="")
    target = ReferenceAttr(choices=["Character", "Creature"])
    result = StringAttr(default="")


class AutoGMInitiative(AutoModel):
    actor = ReferenceAttr(choices=["Character", "Creature"])
    hp = IntAttr()
    description = StringAttr(default="")
    image = ReferenceAttr(choices=[Image])
    position = IntAttr(default=0)
    status = StringAttr(default="healthy")
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
        target,
        result,
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
            attack_roll=attack_roll,
            damage_roll=damage_roll,
            saving_throw=saving_throw,
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
        return ini_actor

    def next_combat_turn(self, hp, status, action, bonus_action, movement):
        ini_actor = self.order[self.current_turn]
        while not ini_actor.hp:
            self.current_turn = (self.current_turn + 1) % len(self.order)
            ini_actor = self.order[self.current_turn]
        ini_actor.hp = hp
        ini_actor.status = status
        ini_actor.action = action
        ini_actor.bonus_action = bonus_action
        ini_actor.movement = movement
        ini_actor.save()
        self.current_turn = (self.current_turn + 1) % len(self.order)
        self.save()
        return ini_actor
