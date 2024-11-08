# Add the 'app' directory to the Python path
import os
import sys

sys.path.append("..")

import pdoc

from api import views as api_views
from api.views import character as character_api
from api.views import city as city_api
from api.views import creature as creature_api
from api.views import encounter as encounter_api
from api.views import faction as faction_api
from api.views import item as item_api
from api.views import location as location_api
from api.views import poi as poi_api
from api.views import region as region_api
from api.views import world as world_api

# from ..task.views import (
#     character,
#     city,
#     creature,
#     encounter,
#     faction,
#     item,
#     location,
#     poi,
#     region,
#     world,
# )
from tasks import views as task_views


def main():
    print("This is the main function of the docs module.")
    results = []

    modules = {
        "index": pdoc.doc.Module(api_views),
        "Character": pdoc.doc.Module(character_api),
        "Creature": pdoc.doc.Module(creature_api),
        "City": pdoc.doc.Module(city_api),
        "POI": pdoc.doc.Module(poi_api),
        "Encounter": pdoc.doc.Module(encounter_api),
        "Faction": pdoc.doc.Module(faction_api),
        "Item": pdoc.doc.Module(item_api),
        "Location": pdoc.doc.Module(location_api),
        "Region": pdoc.doc.Module(region_api),
        "World": pdoc.doc.Module(world_api),
    }
    for name, module in modules.items():
        out = pdoc.render.html_module(module=module, all_modules=modules)
    results.append(out)
    with open(f"docs/{name}.html", "w") as f:
        f.write(out)


if __name__ == "__main__":
    main()
