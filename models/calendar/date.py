import random

from autonomous.model.autoattr import IntAttr, ReferenceAttr
from autonomous.model.automodel import AutoModel


class Date(AutoModel):
    obj = ReferenceAttr(choices=["TTRPGObject"], required=True)
    year = IntAttr(default=0)
    day = IntAttr(default=0)
    month = IntAttr(default=-1)
    calendar = ReferenceAttr(choices=["Calendar"], required=True)

    def __str__(self):
        month = self.calendar.months[self.month] if self.calendar.months else "Unknown"
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
        if isinstance(other, Date):
            return (int(self.year), self.month, self.day) < (
                int(other.year),
                other.month,
                other.day,
            )
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Date):
            return (self.year, self.month, self.day) <= (
                other.year,
                other.month,
                other.day,
            )
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Date):
            return (self.year, self.month, self.day) > (
                other.year,
                other.month,
                other.day,
            )
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Date):
            return (self.year, self.month, self.day) >= (
                other.year,
                other.month,
                other.day,
            )
        return NotImplemented
