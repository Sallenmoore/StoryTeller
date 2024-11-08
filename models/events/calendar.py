from autonomous import log
from autonomous.model.autoattr import (
    IntAttr,
    ListAttr,
    ReferenceAttr,
    StringAttr,
)
from autonomous.model.automodel import AutoModel
from models.events.event import Event


class Calendar(AutoModel):
    year_string = StringAttr(default="CE")
    current_date = ReferenceAttr(choices=[Event])
    months = ListAttr(
        StringAttr(),
        default=lambda: [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
    )
    days = ListAttr(
        StringAttr(),
        default=lambda: [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ],
    )
    days_per_year = IntAttr(default=365)

    @property
    def num_days_per_year(self):
        return self.days_per_year

    @property
    def num_months_per_year(self):
        return len(self.months)

    @property
    def num_days_per_week(self):
        return len(self.days)

    @property
    def num_days_per_month(self):
        return self.days_per_year // self.num_months_per_year

    ################### Instance Methods #####################
    def get_month_str(self, month_num=None):
        # log(self.num_months_per_year)
        if month_num >= self.num_months_per_year:
            month_num = self.num_months_per_year - 1
        if month_num:
            return self.months[int(month_num)]
        if not self.current_date:
            self.current_date = Event()
            self.current_date.day = 1
            self.current_date.month = 0
            self.current_date.year = 0
            self.current_date.save()
            self.save()
        return self.months[self.current_date.month]

    def stringify(self, date, sep=" ", order=None):
        if (
            not date
            or not date.year
            or (date.month == 0 and date.day == 1 and date.year == 1)
        ):
            return "Unknown"
        month = self.get_month_str(date.month)
        return {
            "mdy": f"{month}{sep}{date.day}{sep}{date.year}",
            "ymd": f"{date.year}{sep}{month}{sep}{date.day}",
        }.get(order, f"{date.day}{sep}{month}{sep}{date.year}")

    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_current_date()

    # def clean(self):
    #     self.verify_current_date()

    ################### verify functions ##################
    def pre_save_current_date(self):
        log(self.current_date)
        if not self.current_date:
            self.current_date = Event()
            self.current_date.day = 1
            self.current_date.month = 0
            self.current_date.year = 0
            self.current_date.save()
