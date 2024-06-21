# logic/mod_operations.py

import json
from pathlib import Path
from typing import List, Dict
from .file_operations import load_json, save_json, load_config, save_config, scan_mod_files, extract_zip

class ModOperations:
    def __init__(self, mods_directory: str, dlc_load_path: str, profiles_path: str):
        self.mods_directory = Path(mods_directory)
        self.dlc_load_path = Path(dlc_load_path)
        self.profiles_path = Path(profiles_path)
        self.comments_path = self.mods_directory / 'comments.json'
        self.groups_path = self.mods_directory / 'groups.json'
        self.colors_file = self.mods_directory / 'mod_colors.json'
        self.temp_mods_file = self.mods_directory / 'temp_mods.json'
        
        self.mods_data = self.load_mods()
        self.mods = scan_mod_files(self.mods_directory)
        self.profiles = load_config(self.profiles_path)
        self.comments = load_json(self.comments_path)
        self.groups = load_json(self.groups_path)
        self.colors = load_json(self.colors_file)

        self.sync_enabled_mods()

    def save_colors(self):
        save_json(self.colors_file, self.colors)

    def save_groups(self):
        save_json(self.groups_path, self.groups)

    def save_comments(self):
        save_json(self.comments_path, self.comments)

    def save_mods(self):
        dlc_load_data = {
            "disabled_dlcs": self.mods_data["disabled_dlcs"],
            "enabled_mods": [mod for mod, enabled in self.mods_data["enabled_mods"].items() if enabled and mod != "mod/"]
        }
        save_json(self.dlc_load_path, dlc_load_data)
        self.save_temp_mods()

    def save_temp_mods(self):
        temp_mods_data = self.mods_data.copy()
        temp_mods_data["enabled_mods"] = {k: v for k, v in temp_mods_data["enabled_mods"].items() if k != "mod/"}
        save_json(self.temp_mods_file, temp_mods_data)

    def load_mods(self) -> Dict:
        temp_mods_data = load_json(self.temp_mods_file)
        self.groups = load_json(self.groups_path)
        self.colors = load_json(self.colors_file)
        if not temp_mods_data:
            dlc_load_data = load_json(self.dlc_load_path)
            temp_mods_data = {
                "disabled_dlcs": dlc_load_data.get("disabled_dlcs", []),
                "enabled_mods": {mod: True for mod in dlc_load_data.get("enabled_mods", []) if mod != "mod/"}
            }
            save_json(self.temp_mods_file, temp_mods_data)
        else:
            # Ensure enabled_mods is a dictionary
            if isinstance(temp_mods_data.get("enabled_mods"), list):
                temp_mods_data["enabled_mods"] = {mod: True for mod in temp_mods_data["enabled_mods"] if mod != "mod/"}
            # Remove empty mod entry if it exists
            temp_mods_data["enabled_mods"].pop("mod/", None)
        return temp_mods_data

    def enable_mod(self, mod_name: str) -> None:
        for mod in self.mods:
            if mod.get('name') == mod_name:
                mod['enabled'] = True
                mod_file_path = f"mod/{mod['path']}"
                self.mods_data["enabled_mods"][mod_file_path] = True
                self.save_mods()

    def disable_mod(self, mod_name: str) -> None:
        for mod in self.mods:
            if mod.get('name') == mod_name:
                mod['enabled'] = False
                mod_file_path = f"mod/{mod['path']}"
                if mod_file_path in self.mods_data["enabled_mods"]:
                    del self.mods_data["enabled_mods"][mod_file_path]
                self.save_mods()
                self.save_temp_mods()

    def sync_enabled_mods(self) -> None:
        for mod in self.mods:
            mod_path = f"mod/{mod['path']}"
            mod['enabled'] = self.mods_data["enabled_mods"].get(mod_path, False)

    def list_mods(self) -> List[Dict]:
        return [
            {
                "name": mod.get("name"),
                "version": mod.get("version"),
                "comment": self.comments.get(mod.get("path"), ""),
                "path": mod.get("path"),
                "enabled": mod.get("enabled", False)
            }
            for mod in self.mods
        ]

    def save_profile(self, profile_name: str) -> None:
        self.profiles[profile_name] = {
            "enabled_mods": json.dumps(self.mods_data["enabled_mods"]),
            "groups": json.dumps(self.groups)
        }
        save_config(self.profiles_path, self.profiles)
        self.profiles = load_config(self.profiles_path)

    def load_profile(self, profile_name: str) -> None:
        profile = self.profiles.get(profile_name, {})
        if profile:
            self.mods_data["enabled_mods"] = json.loads(profile.get("enabled_mods", "{}"))
            self.groups = json.loads(profile.get("groups", "{}"))
            self.save_mods()
            self.save_temp_mods()
            self.save_groups()
            self.sync_enabled_mods()

    def delete_profile(self, profile_name: str) -> None:
        if profile_name in self.profiles:
            del self.profiles[profile_name]
            save_config(self.profiles_path, self.profiles)

    def install_mod(self, zip_path: str) -> None:
        extract_zip(zip_path, self.mods_directory)
        self.mods = scan_mod_files(self.mods_directory)
        self.sync_enabled_mods()
