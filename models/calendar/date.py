import random

from autonomous.model.autoattr import IntAttr, ReferenceAttr
from autonomous.model.automodel import AutoModel

from autonomous import log


class Date(AutoModel):
    obj = ReferenceAttr(
        choices=["TTRPGBase", "Episode", "Event", "Lore"], required=True
    )
    year = IntAttr(default=0)
    day = IntAttr(default=0)
    month = IntAttr(default=-1)
    calendar = ReferenceAttr(choices=["Calendar"], required=True)

    def __str__(self):
        if self.year <= 0:
            return "Unknown"
        try:
            month = (
                self.calendar.months[self.month] if self.calendar.months else "Unknown"
            )
        except IndexError:
            month = "Unknown"
        return f"{self.day:02d} {month} {self.year}"

    def __repr__(self):
        return f"Date(day={self.day:02d}, month={self.month}, year={self.year})"

    def __eq__(self, other):
        if isinstance(other, Date):
            return (
                int(self.year) == int(other.year)
                and self.month == other.month
                and self.day == other.day
            )
        return False

    def __lt__(self, other):
        # log("Comparing Dates: {} < {}".format(self, other))
        if isinstance(other, Date):
            return (int(self.year), self.month, self.day) < (
                int(other.year),
                other.month,
                other.day,
            )
        return False

    def __le__(self, other):
        if isinstance(other, Date):
            return (self.year, self.month, self.day) <= (
                other.year,
                other.month,
                other.day,
            )
        return False

    def __gt__(self, other):
        if isinstance(other, Date):
            return (self.year, self.month, self.day) > (
                other.year,
                other.month,
                other.day,
            )
        return False

    def __ge__(self, other):
        if isinstance(other, Date):
            return (self.year, self.month, self.day) >= (
                other.year,
                other.month,
                other.day,
            )
        return False

    @classmethod
    def from_string(cls, obj, calendar, date_string):
        parts = date_string.split(" ")
        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2])
        return cls(obj=obj, calendar=calendar, day=day, month=month, year=year)

    ## MARK: - Verification Hooks
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
        document.pre_save_month()
        document.pre_save_day()
        document.pre_save_year()
        document.pre_save_calendar()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verify methods ##################

    def pre_save_day(self):
        if self.day and isinstance(self.day, str):
            self.day = int(self.day)
        if not self.day or self.day < 1:
            self.day = random.randint(1, 28)

    def pre_save_year(self):
        if self.year and isinstance(self.year, str):
            self.year = int(self.year)
        if not self.year:
            self.year = 0

    def pre_save_month(self):
        if self.month and isinstance(self.month, str):
            self.month = self.calendar.months.index(self.month)
        if not self.month or self.month < 0:
            self.month = random.randint(0, 11)

    def pre_save_calendar(self):
        if not self.calendar and self.obj:
            self.calendar = self.obj.world.calendar
