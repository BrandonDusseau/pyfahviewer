import json
import os

config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.json")
config = None


def __load_config():
    global config

    try:
        with open(config_path, "r") as jsonfile:
            config = json.load(jsonfile)
    except FileNotFoundError:
        print("Configuration file not found; generating one.")
        config = {}
        __save_config()


def __save_config():
    global config
    with open(config_path, "w") as jsonfile:
        json.dump(config, jsonfile)


def get_config(key):
    global config

    if config is None:
        try:
            __load_config()
        except Exception as ex:
            print("Unable to load configuration!\n" + str(ex))
            return None

    return config.get(key)


def set_config(key, value):
    config[key] = value
    __save_config()
