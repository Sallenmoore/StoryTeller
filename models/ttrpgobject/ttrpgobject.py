from copy import deepcopy

from autonomous import log
from autonomous.db import ValidationError
from autonomous.model.autoattr import BoolAttr, ListAttr, ReferenceAttr
from models.base.ttrpgbase import TTRPGBase

MAX_NUM_IMAGES_IN_GALLERY = 100
IMAGES_BASE_PATH = "static/images/tabletop"


class TTRPGObject(TTRPGBase):
    meta = {"abstract": True, "allow_inheritance": True, "strict": False}
    world = ReferenceAttr(choices=["World"])
    associations = ListAttr(ReferenceAttr(choices=[TTRPGBase]))
    parent = ReferenceAttr(choices=[TTRPGBase])
    parent_list = []

    _no_copy = TTRPGBase._no_copy | {
        "associations": [],
        "events": [],
    }

    @classmethod
    def update_system_references(cls, pk):
        log(f"Updating AI reference data for ({cls}:{pk})...")
        try:
            from models.world import World

            return cls().get(pk).world.update_system_references(pk)
        except Exception as e:
            log(e, cls, "Object has no world")
            return False

    @property
    def characters(self):
        return [a for a in self.associations if a.model_name() == "Character"]

    @property
    def children(self):
        return [obj for obj in self.associations if obj.parent == self]

    @property
    def cities(self):
        return [a for a in self.associations if a.model_name() == "City"]

    @property
    def creatures(self):
        return [a for a in self.associations if a.model_name() == "Creature"]

    @property
    def districts(self):
        return [a for a in self.associations if a.model_name() == "District"]

    @property
    def encounters(self):
        return [a for a in self.associations if a.model_name() == "Encounter"]

    @property
    def factions(self):
        return [a for a in self.associations if a.model_name() == "Faction"]

    @property
    def genre(self):
        return self.get_world().genre.lower()

    @property
    def geneology(self):
        ancestry = []
        if self.parent:
            ancestry.append(self.parent)
            ancestor = self.parent
            while ancestor.parent:
                ancestry.append(ancestor.parent)
                ancestor = ancestor.parent
        if self.world not in ancestry:
            ancestry.append(self.world)
        return ancestry

    @property
    def gm(self):
        return self.get_world().gm

    @property
    def items(self):
        return [a for a in self.associations if a.model_name() == "Item"]

    @property
    def locations(self):
        return [a for a in self.associations if a.model_name() == "Location"]

    @property
    def regions(self):
        return [a for a in self.associations if a.model_name() == "Region"]

    @property
    def system(self):
        return self.get_world().system

    @property
    def title(self):
        return self.get_title(self)

    @property
    def titles(self):
        return self.get_world().system._titles

    @property
    def user(self):
        return self.get_world().user

    ############# Boolean Methods #############

    def is_owner(self, user):
        try:
            return self.get_world().is_owner(user)
        except Exception as e:
            log(e, self, "Object has no world")
            raise e

    ########## Object Data ######################
    def get_world(self):
        # IMPORTANT: this is here to register the model
        # without it, the model may not have been registered yet and it will fail
        from models.world import World

        return self.world

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                   ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     super().auto_post_init(sender, document, **kwargs)

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_world()
        document.pre_save_associations()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()
    def pre_save_associations(self):
        if self in self.associations:
            self.associations.remove(self)

        if not self.parent:
            if self.associations and self.parent_list:
                for parent_model in self.parent_list:
                    for a in self.associations:
                        if a.model_name() == parent_model:
                            self.parent = a
                            break
                    if self.parent:
                        break

    def pre_save_world(self):
        if not self.get_world():
            raise ValidationError("Must be associated with a World object")
