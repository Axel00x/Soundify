import os, json

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
