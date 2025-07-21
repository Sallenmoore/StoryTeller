from autonomous.model.autoattr import (
    BoolAttr,
    DictAttr,
    FileAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel


class PlayerAction(AutoModel):
    description = StringAttr(default="")
    target = StringAttr(default="")
    method = StringAttr(default="")
    focus_on_coordination = BoolAttr(default=False)


class PlayerResponse(AutoModel):
    player = ReferenceAttr(choices=["Character"])
    response = StringAttr(default="")
    observed_details = ListAttr(StringAttr(default=""))
    reaction_to_party = StringAttr(default="")
    action = ReferenceAttr(choices=["PlayerAction"])

    def delete(self):
        if self.action and isinstance(self.action, PlayerAction):
            self.action.delete()
        super().delete()

    def add_action(self, description, target, method, focus_on_coordination=False):
        if self.action and isinstance(self.action, PlayerAction):
            self.action.delete()
        action = PlayerAction(
            description=description,
            target=target,
            method=method,
            focus_on_coordination=focus_on_coordination,
        )
        action.save()
        self.action = action
        self.save()
        return action
