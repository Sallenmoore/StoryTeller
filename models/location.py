from autonomous import log
from models.abstracts.place import Scene


class Location(Scene):
    parent_list = ["Region", "City", "Location"]
