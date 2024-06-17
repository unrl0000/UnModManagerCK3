import json
import zipfile
import configparser
from pathlib import Path
from typing import List, Dict

class ModManager:
    def __init__(self, mods_directory: str, dlc_load_path: str, profiles_path: str):
        self.mods_directory = Path(mods_directory)
        self.dlc_load_path = Path(dlc_load_path)
        self.profiles_path = Path(profiles_path)
        self.comments_path = self.mods_directory / 'comments.json'
        self.mods = self.load_mods()
        self.dlc_data = self.load_dlc_load()
        self.profiles = self.load_profiles()
        self.comments = self.load_comments()
        self.sync_enabled_mods()

    def load_comments(self) -> Dict[str, str]:
        if self.comments_path.exists():
            with open(self.comments_path, 'r') as file:
                return json.load(file)
        return {}

    def save_comments(self) -> None:
        with open(self.comments_path, 'w') as file:
            json.dump(self.comments, file, indent=4)

    def load_profiles(self) -> Dict[str, Dict]:
        config = configparser.ConfigParser()
        if self.profiles_path.exists():
            config.read(self.profiles_path)
        profiles = {section: dict(config.items(section)) for section in config.sections()}
        return profiles

    def load_profile(self, profile_name: str) -> None:
        profile = self.profiles.get(profile_name, {})
        if profile:
            self.dlc_data["enabled_mods"] = profile["enabled_mods"]
            self.save_dlc_load()
            self.sync_enabled_mods()

    def save_profile(self, profile_name: str) -> None:
        config = configparser.ConfigParser()
        self.profiles[profile_name] = {"enabled_mods": self.dlc_data["enabled_mods"]}
        for profile in self.profiles:
            config[profile] = self.profiles[profile]
        with open(self.profiles_path, 'w') as file:
            config.write(file)
        self.profiles = self.load_profiles()

    def delete_profile(self, profile_name: str) -> None:
        if profile_name in self.profiles:
            del self.profiles[profile_name]
            config = configparser.ConfigParser()
            for profile in self.profiles:
                config[profile] = self.profiles[profile]
            with open(self.profiles_path, 'w') as file:
                config.write(file)

    def load_mods(self) -> List[Dict]:
        mods = []
        for mod_file in self.mods_directory.glob('*.mod'):
            with open(mod_file, 'r') as file:
                mod_data = self.parse_mod_file(file)
                mods.append(mod_data)
        return mods

    def parse_mod_file(self, file) -> Dict:
        mod_data = {}
        for line in file:
            if '=' in line:
                key, value = line.split('=', 1)
                mod_data[key.strip()] = value.strip().strip('"')
        mod_data['path'] = Path(file.name).name
        return mod_data

    def load_dlc_load(self) -> Dict:
        if self.dlc_load_path.exists():
            with open(self.dlc_load_path, 'r') as file:
                dlc_data = json.load(file)
                if isinstance(dlc_data.get("disabled_dlcs"), str):
                    dlc_data["disabled_dlcs"] = json.loads(dlc_data["disabled_dlcs"])
                if not isinstance(dlc_data.get("enabled_mods", []), list):
                    dlc_data["enabled_mods"] = []
                return dlc_data
        else:
            return {"disabled_dlcs": [], "enabled_mods": []}

    def save_dlc_load(self) -> None:
        with open(self.dlc_load_path, 'w') as file:
            json.dump(self.dlc_data, file, indent=4)

    def sync_enabled_mods(self) -> None:
        for mod in self.mods:
            mod['enabled'] = f"mod/{mod['path']}" in self.dlc_data["enabled_mods"]

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

    def enable_mod(self, mod_name: str) -> None:
        for mod in self.mods:
            if mod.get('name') == mod_name:
                mod['enabled'] = True
                mod_file_path = f"mod/{mod['path']}"
                if mod_file_path not in self.dlc_data["enabled_mods"]:
                    self.dlc_data["enabled_mods"].append(mod_file_path)
                self.save_dlc_load()

    def disable_mod(self, mod_name: str) -> None:
        for mod in self.mods:
            if mod.get('name') == mod_name:
                mod['enabled'] = False
                mod_file_path = f"mod/{mod['path']}"
                if mod_file_path in self.dlc_data["enabled_mods"]:
                    self.dlc_data["enabled_mods"].remove(mod_file_path)
                self.save_dlc_load()

    def install_mod(self, zip_path: str) -> None:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.mods_directory)
        self.mods = self.load_mods()
        self.sync_enabled_mods()
