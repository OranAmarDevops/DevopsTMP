import json
import os
from functools import lru_cache


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


@lru_cache(maxsize=1)
def load_settings():
    config_path = os.environ.get(
        "APP_CONFIG_FILE",
        os.path.join(PROJECT_ROOT, "config.json")
    )

    with open(config_path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)