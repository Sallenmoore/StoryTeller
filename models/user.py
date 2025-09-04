import traceback

from autonomous import log
from autonomous.auth.user import AutoUser
from autonomous.model.autoattr import (
    BoolAttr,
    ListAttr,
    ReferenceAttr,
)
from models.world import World


class User(AutoUser):
    admin = BoolAttr(default=False)
    current_screen = ReferenceAttr("Screen", default=None)
    screens = ListAttr(ReferenceAttr("Screen"), default=[])

    @property
    def worlds(self):
        for w in World.all():
            if self in w.users:
                yield w

    def world_user(self, obj):
        return self in obj.world.users

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    # @classmethod
    # def auto_pre_save(cls, sender, document, **kwargs):
    #     super().auto_pre_save(sender, document, **kwargs)

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()
