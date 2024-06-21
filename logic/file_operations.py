# logic/file_operations.py

import json
import zipfile
import configparser
from pathlib import Path
from typing import Dict, List

def save_json(file_path: Path, data: dict) -> None:
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving {file_path}: {e}")

def load_json(file_path: Path) -> dict:
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    return {}

def save_config(file_path: Path, data: Dict[str, Dict[str, str]]) -> None:
    config = configparser.ConfigParser()
    for section, values in data.items():
        config[section] = values
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            config.write(f)
    except Exception as e:
        print(f"Error saving config {file_path}: {e}")

def load_config(file_path: Path) -> Dict[str, Dict[str, str]]:
    config = configparser.ConfigParser()
    if file_path.exists():
        config.read(file_path)
    return {section: dict(config.items(section)) for section in config.sections()}

def scan_mod_files(mods_directory: Path) -> List[Dict]:
    mods = []
    for mod_file in mods_directory.glob('*.mod'):
        mod_data = read_mod_file(mod_file)
        mods.append(mod_data)
    return mods

def read_mod_file(file_path: Path) -> Dict:
    mod_data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if '=' in line:
                    key, value = line.split('=', 1)
                    mod_data[key.strip()] = value.strip().strip('"')
        mod_data['path'] = file_path.name
    except Exception as e:
        print(f"Error reading mod file {file_path}: {e}")
    return mod_data

def extract_zip(zip_path: str, extract_to: str) -> None:
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    except Exception as e:
        print(f"Error extracting zip file {zip_path}: {e}")
