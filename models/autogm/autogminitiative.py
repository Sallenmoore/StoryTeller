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


class AutoGMInitiative(AutoModel):
    actor = ReferenceAttr(choices=["Character", "Creature"])
    hp = IntAttr()
    position = IntAttr(default=0)
    status = StringAttr(default="healthy")
    action = StringAttr(default="")
    bonus_action = StringAttr(default="")
    movement = StringAttr(default="")


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
        log(self.order)
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
