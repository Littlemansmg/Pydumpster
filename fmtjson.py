import os, json


def read_json(file_name):
    if not file_name.endswith('.json'):
        file_name = file_name + '.json'
    if not os.path.isfile(file_name):
        list_name = {}
    else:
        try:
            with open(file_name) as f:
                list_name = json.load(f)
        except ValueError:
            list_name = {}
    return list_name


def edit_json(file_name, items):
    if not file_name.endswith('.json'):
        file_name = file_name + '.json'
    with open(file_name, "w") as f:
        json.dump(items, f, indent=4, sort_keys=True)
