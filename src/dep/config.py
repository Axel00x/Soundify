import os, json

from .settings import log_debug, log_error, log_info

_config_path = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    if not os.path.exists(_config_path):
        default = {"playlists": {}}
        with open(_config_path, 'w') as f:
            json.dump(default, f, indent=4)
        return default

    try:
        with open(_config_path) as f:
            return json.load(f)
    except json.JSONDecodeError:
        default = {"playlists": {}}
        with open(_config_path, 'w') as f:
            json.dump(default, f, indent=4)
        return default

def save_config(data):
    with open(_config_path, 'w') as f:
        json.dump(data, f, indent=4)

def save_config_rt(playlists):
    clean_playlists = {}
    for pname, songs in playlists.items():
        clean_list = []
        for s in songs:
            clean_list.append({
                "id":   s["id"],
                "name": s["name"],
                "file": s["file"]
            })
        clean_playlists[pname] = clean_list

    data_to_save = { "playlists": clean_playlists }
    log_debug(f"Saving config: {data_to_save}")
    save_config(data_to_save)