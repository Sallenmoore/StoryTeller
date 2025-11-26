from datetime import datetime

from autonomous.db import ValidationError
from autonomous.model.autoattr import (
    DateTimeAttr,
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel

from autonomous import log
from models.utility.parse_attributes import parse_text


class JournalEntry(AutoModel):
    world = ReferenceAttr(choices=["World"], required=True)
    title = StringAttr(default="")
    text = StringAttr(default="")
    tags = ListAttr(StringAttr(default=""))
    date = DateTimeAttr(default=lambda: datetime.now())
    importance = IntAttr(default=0)
    associations = ListAttr(ReferenceAttr(choices=["TTRPGObject"]))

    @property
    def genre(self):
        return self.world.genre if self.world else "default"

    ############## Instance Methods ##############

    def add_association(self, obj):
        if obj not in self.associations:
            self.associations.append(obj)
            self.save()
        return self

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
        document.pre_save_importance()
        document.pre_save_text()
        document.pre_save_date()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify associations ##################
    def pre_save_date(self):
        if not isinstance(self.date, datetime):
            self.date = datetime.now()

    def pre_save_text(self):
        if self.text:
            self.text = parse_text(self, self.text)

    def pre_save_importance(self):
        self.importance = int(self.importance)
        if not (0 <= self.importance <= 5):
            raise ValidationError(
                f"Importance must be an integer '0-5', not {self.importance}"
            )


class Journal(AutoModel):
    entries = ListAttr(ReferenceAttr(choices=[JournalEntry]))
    world = ReferenceAttr(choices=["World"], required=True)
    parent = ReferenceAttr(choices=["TTRPGBase"], required=True)

    def delete(self):
        for entries in self.entries:
            entries.delete()
        super().delete()

    def add_entry(
        self,
        title=None,
        text=None,
        importance=None,
        associations=None,
    ):
        entry = JournalEntry()
        entry.save()
        self.entries += [entry]
        self.save()
        return self.update_entry(entry.pk, title, text, importance, associations)

    def update_entry(
        self,
        pk,
        title=None,
        text=None,
        importance=None,
        associations=[],
    ):
        if entry := JournalEntry.get(pk):
            entry.title = title or entry.title
            if text and entry.text != text:
                entry.text = text
                self.save()
            entry.importance = (
                int(importance) if importance is not None else entry.importance
            )
            if associations:
                for assoc in associations:
                    entry.add_association(assoc)
            entry.date = datetime.now()
            entry.save()
            # update current object's entries
            self.entries = [e if e != entry else entry for e in self.entries]
            self.save()
        return entry

    def get_entry(self, entry_pk):
        entry = JournalEntry.get(entry_pk)
        return entry if entry in self.entries else None

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION hooks                     ##
    ###############################################################

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_entries()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify methods ##################
    def pre_save_entries(self):
        for entry in self.entries:
            entry.world = self.world
            entry.save()
        self.entries = sorted(self.entries, key=lambda x: x.date, reverse=True)
