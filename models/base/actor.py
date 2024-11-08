from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    IntAttr,
    ListAttr,
    StringAttr,
)
from models.abstracts.ttrpgobject import TTRPGObject


class Actor(TTRPGObject):
    meta = {"abstract": True, "allow_inheritance": True, "strict": False}
    goal = StringAttr(default="Unknown")
    hitpoints = IntAttr(default=30)
    ac = IntAttr(default=10)
    current_hitpoints = IntAttr(default=10)
    strength = IntAttr(default=10)
    dexterity = IntAttr(default=10)
    constitution = IntAttr(default=10)
    wisdom = IntAttr(default=10)
    intelligence = IntAttr(default=10)
    charisma = IntAttr(default=10)

    @property
    def map(self):
        for a in self.geneology:
            if a.map:
                return a.map

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    # @classmethod
    # def auto_pre_save(cls, sender, document, **kwargs):
    #     super().auto_pre_save(sender, document, **kwargs)

    @classmethod
    def auto_post_save(cls, sender, document, **kwargs):
        super().auto_post_save(sender, document, **kwargs)
        document.post_save_ac()

    # def clean(self):
    #     super().clean()

    ############### Verification Methods ##############

    def post_save_ac(self):
        if not self.ac:
            self.ac = max(
                10,
                (int(self.dexterity) - 10) // 2 + (int(self.strength) - 10) // 2 + 10,
            )
