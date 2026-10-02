import json
import os
from pathlib import Path


CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"


def get_default_config():
    return {
        "theme": "dark",
        "last_folder": os.path.expanduser("~"),
    }


def load_config():
    """Carga la configuración y devuelve los valores predeterminados si falla."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as config_file:
                config = json.load(config_file)
                defaults = get_default_config()
                for key in defaults:
                    if key not in config:
                        config[key] = defaults[key]
                return config
        except Exception as error:
            print(f"Error leyendo config.json: {error}")
            return get_default_config()
    return get_default_config()


def save_config(config_data):
    """Guarda el diccionario de configuración en config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as config_file:
            json.dump(config_data, config_file, indent=4)
    except Exception as error:
        print(f"Error guardando config.json: {error}")