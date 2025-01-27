from autonomous.model.autoattr import IntAttr, ListAttr, ReferenceAttr, StringAttr
from autonomous.model.automodel import AutoModel
from models.calendar.date import Date


class Calendar(AutoModel):
    world = ReferenceAttr(choices=["World"])
    age = StringAttr(default="")
    dates = ListAttr(ReferenceAttr(choices=["Date"]))
    months = ListAttr(StringAttr(default=""))
    days = ListAttr(StringAttr(default=""))
    days_per_year = IntAttr(default=365)

    @property
    def days_per_month(self):
        return self.days_per_year // len(self.months)

    @property
    def days_per_week(self):
        return len(self.days)

    @property
    def current_date(self):
        self.dates.sort()
        return self.dates[-1] if self.dates else None

    def add_date(self, year, month, day):
        date = Date(year=year, month=month, day=day, calendar=self)
        date.save()
        self.dates += [date]
        self.save()
