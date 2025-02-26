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

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION HOOKS                     ##
    ###############################################################
    # @classmethod
    # def auto_post_init(cls, sender, document, **kwargs):
    #     # log("Auto Pre Save World")
    #     super().auto_post_init(sender, document, **kwargs)
    #     =

    @classmethod
    def auto_pre_save(cls, sender, document, **kwargs):
        from models.gmscreen.gmscreen import GMScreen

        super().auto_pre_save(sender, document, **kwargs)
        document.pre_save_calendar()

    # @classmethod
    # def auto_post_save(cls, sender, document, **kwargs):
    #     super().auto_post_save(sender, document, **kwargs)

    # def clean(self):
    #     super().clean()

    ################### verification methods ##################

    def pre_save_calendar(self):
        if not self.months:
            self.months = [
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
            ]
        if not self.days:
            self.days = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
