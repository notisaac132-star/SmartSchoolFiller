"""Small JSON settings store in the user's home directory."""

import json
from pathlib import Path

SETTINGS_PATH = Path.home() / ".smartschoolfiller.json"

DEFAULTS = {
    "schoology_url": "https://app.schoology.com",
    "profile_name": "school",
    "consumer_key": "",
    "consumer_secret": "",
    "done": [],
}


def load(path=SETTINGS_PATH):
    settings = dict(DEFAULTS)
    try:
        settings.update(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return settings


def save(settings, path=SETTINGS_PATH):
    Path(path).write_text(json.dumps(settings, indent=2), encoding="utf-8")
