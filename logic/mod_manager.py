# logic/mod_manager.py

from logic.mod_operations import ModOperations

def main():
    mods_directory = 'path_to_mods'
    dlc_load_path = 'path_to_dlc_load'
    profiles_path = 'path_to_profiles'
    manager = ModOperations(mods_directory, dlc_load_path, profiles_path)
    manager.load_profile('default_profile')
    mods = manager.list_mods()
    for mod in mods:
        print(mod)

if __name__ == '__main__':
    main()
