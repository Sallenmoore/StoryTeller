from autonomous.model.autoattr import (
    StringAttr,
)
from models.abstracts.place import Scene
from models.location import Location


class POI(Scene):
    district = StringAttr(default="")

    parent_list = ["City", "Location"]

    def get_location(self):
        obj = Location(
            name=self.name,
            desc=self.desc,
            backstory=self.backstory,
            image=self.image,
            map=self.map,
            owner=self.owner,
            world=self.world,
            parent=self.parent,
            events=self.events,
            backstory_summary=self.backstory_summary,
            traits=self.traits,
            end_date=self.end_date,
            current_age=self.current_age,
            history=self.history,
            journal=self.journal,
        )
        obj.save()
        for a in self.associations:
            a.add_association(obj)
        return obj

    def page_data(self):
        result = super().page_data()
        if self.district:
            result |= {
                "district": self.district,
            }
        return result

    ## MARK: - Verification Methods
    ###############################################################
    ##                    VERIFICATION METHODS                   ##
    ###############################################################

    # def clean(self):
    #     if self.attrs:
    #         self.verify_attr()

    # ################### verify associations ##################
    # def verify_attr(self):
    #     pass
