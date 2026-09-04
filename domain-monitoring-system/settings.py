import json
import os
from functools import lru_cache


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


@lru_cache(maxsize=None)
def load_settings(service=None):
    if service:
        environment_variable = (
            f"{service.upper()}_CONFIG_FILE"
        )
        config_path = os.environ.get(
            environment_variable,
            os.path.join(
                PROJECT_ROOT,
                service,
                "config.json"
            )
        )
    else:
        config_path = os.environ.get(
            "APP_CONFIG_FILE",
            os.path.join(PROJECT_ROOT, "config.json")
        )

    with open(config_path, "r", encoding="utf-8") as config_file:
        return json.load(config_file)
