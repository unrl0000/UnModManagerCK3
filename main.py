import os
import sys
from PyQt5 import QtWidgets

from func import mod_manager as manager
from ui import main_window as ui

if __name__ == "__main__":
    user_name = os.getlogin()
    mods_directory = f"C:\\Users\\{user_name}\\Documents\\Paradox Interactive\\Crusader Kings III\\mod"
    dlc_load_path = f"C:\\Users\\{user_name}\\Documents\\Paradox Interactive\\Crusader Kings III\\dlc_load.json"
    profiles_path = f"C:\\Users\\{user_name}\\Documents\\Paradox Interactive\\Crusader Kings III\\profiles.ini"
    
    manager = manager.ModManager(mods_directory, dlc_load_path, profiles_path)
    root = QtWidgets.QApplication(sys.argv)
    ui = ui.ModManagerUI(manager)
    ui.show()
    sys.exit(root.exec_())
