from autonomous import log
from autonomous.auth.user import AutoUser
from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    BoolAttr,
    ListAttr,
    ReferenceAttr,
)
from models.world import World


class User(AutoUser):
    worlds = ListAttr(ReferenceAttr(choices=[World]))
    admin = BoolAttr(default=False)

    def world_user(self, world):
        return self in world.users

    def add_world(self, obj):
        if isinstance(obj, str):
            obj = World.get(obj)
        if obj and obj not in self.worlds:
            obj.user = self
            obj.save()
            self.worlds.append(obj)
            self.save()

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.verify_worlds()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################
    def verify_worlds(self):
        for w in self.worlds:
            if not self.world_user(w):
                raise ValidationError(f"{self} is not a user of {w}")
