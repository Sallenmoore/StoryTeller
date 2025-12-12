import random

from flask import get_template_attribute

from autonomous.model.autoattr import ListAttr, ReferenceAttr, StringAttr

from .gmscreenarea import GMScreenArea


class GMScreenNonCanon(GMScreenArea):
    _macro = "screen_noncanon_area"
    name = StringAttr(default="Non Canon")
    objs = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))
    filter = StringAttr(default="Character")

    def get_objs(self, num=100):
        objs = []
        for o in self.screen.world.associations:
            if o.model_name().lower() == self.filter.lower() and not o.canon:
                objs += [o]
        return random.sample(objs, min(num, len(objs)))

    # MARK: Verification
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_objs()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # log([p.name for p in document.players])

    # def clean(self):
    #     super().clean()

    ################### Verification Methods ##################

    def pre_save_objs(self):
        self.objs = []
        for ass in self.screen.world.associations:
            if not ass.canon:
                self.objs += [ass]
