from autonomous import log


def organize_models(models, by_attr):
    if not isinstance(by_attr, list):
        by_attr = [by_attr]
    # log(models, by_attr)
    # for m in models:
    #     for attr in by_attr:
    #         log(getattr(m, attr))
    models.sort(key=lambda x: [getattr(x, attr) for attr in by_attr])
    return models


def in_list(list_item, obj_item):
    return any([li.pk == obj_item.pk for li in list_item if li])
