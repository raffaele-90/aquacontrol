# AquaControl
# Copyright (C) 2026 Raffaele Schiavone
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import json

CONFIG_DIR = os.path.expanduser("~/.config/aquacontrol")
CONFIG_FILE = os.path.join(CONFIG_DIR, "aquacontrol.json")

def load_config():
    """Deserializes JSON settings file. Provides default dictionary if missing."""
    default_config = {
        "lang": "it",
        "use_fahrenheit": False,
        "sensors": {},
        "channels_names": {},
        "profiles": {"Default": {}},
        "last_profile": "Default",
        "autostart_min": False,
        "osd_export": False,
        "osd_scale": 1.0,
        "autoswitch_enabled": False,
        "process_profiles": {},
        "security": {},
        "osd_config": {}
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                default_config.update(data)
            return default_config
        except Exception:
            pass
    return default_config

def save_config(cfg):
    """Serializes the current settings dictionary to the user configuration file."""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)

# Variabile globale esportata per il resto dei moduli
global_config = load_config()
