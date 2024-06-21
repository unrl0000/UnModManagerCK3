# main.py

import os
import sys
from PyQt5 import QtWidgets
from ui.ui_manager import ModManagerUI
from logic.mod_manager import ModOperations

def main():
    user_name = os.getlogin()
    mods_directory = f"C:\\Users\\{user_name}\\Documents\\Paradox Interactive\\Crusader Kings III\\mod"
    dlc_load_path = f"C:\\Users\\{user_name}\\Documents\\Paradox Interactive\\Crusader Kings III\\dlc_load.json"
    profiles_path = f"C:\\Users\\{user_name}\\Documents\\Paradox Interactive\\Crusader Kings III\\profiles.ini"

    manager = ModOperations(mods_directory, dlc_load_path, profiles_path)
    app = QtWidgets.QApplication(sys.argv)
    ui = ModManagerUI(manager)
    ui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
