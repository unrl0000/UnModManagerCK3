# logic/conflict_finder.py

import os
import time
import threading
import subprocess
import concurrent.futures
from collections import defaultdict
from PyQt5 import QtWidgets, QtCore, QtGui

class ConflictFinder(QtCore.QObject):
    update_progress_signal = QtCore.pyqtSignal(int)
    display_conflicts_signal = QtCore.pyqtSignal(dict, dict, list)
    display_missing_translations_signal = QtCore.pyqtSignal(dict)

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.last_conflict_check_time = 0
        self.conflict_window = None
        self.missing_translations_window = None
        self.finding_conflicts = False 

    def find_conflicts(self):
        current_time = time.time()
        if current_time - self.last_conflict_check_time < 3 or self.finding_conflicts:
            return
        self.last_conflict_check_time = current_time
        self.finding_conflicts = True 

        if hasattr(self, 'progress_window') and self.progress_window.isVisible():
            self.progress_window.close()

        self.progress_window = QtWidgets.QProgressDialog("Finding Conflicts, Please Wait...", "Cancel", 0, 100, self.parent())
        self.progress_window.setWindowModality(QtCore.Qt.WindowModal)
        self.progress_window.show()

        self.update_progress_signal.connect(self.progress_window.setValue)
        self.display_conflicts_signal.connect(self.display_conflicts)
        self.display_missing_translations_signal.connect(self.display_missing_translations)

        threading.Thread(target=self.find_conflicts_thread).start()

    def find_conflicts_thread(self):
        num_mods = len(self.manager.mods)
        file_paths = defaultdict(list)
        mod_localizations = defaultdict(list)
        processed_mods = 0

        def update_progress(stage, progress):
            total_stages = 2
            overall_progress = ((stage - 1) + (progress / 100)) / total_stages * 100
            self.update_progress_signal.emit(int(overall_progress))

        def process_mod(mod):
            local_file_paths = defaultdict(list)
            local_mod_localizations = defaultdict(list)

            if not mod.get('enabled'):
                return local_file_paths, local_mod_localizations

            mod_folder = mod['path'].split('.')[0]
            mod_path = os.path.join(self.manager.mods_directory, mod_folder)
            if os.path.isdir(mod_path):
                for root, _, files in os.walk(mod_path):
                    for file in files:
                        rel_path = os.path.relpath(os.path.join(root, file), mod_path)
                        local_file_paths[rel_path].append(mod_folder)
                        if rel_path.startswith('localization'):
                            local_mod_localizations[mod_folder].append(rel_path)
            return local_file_paths, local_mod_localizations

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_mod, mod): mod for mod in self.manager.mods}
            for future in concurrent.futures.as_completed(futures):
                mod_file_paths, mod_localizations = future.result()
                processed_mods += 1
                update_progress(1, (processed_mods / num_mods) * 100)
                if mod_file_paths:
                    for key, value in mod_file_paths.items():
                        file_paths[key].extend(value)
                    for key, value in mod_localizations.items():
                        mod_localizations[key].extend(value)

        update_progress(2, 0)

        red_conflicts = {}
        yellow_conflicts = {}
        missing_russian = []

        for path, mods in file_paths.items():
            if os.path.basename(path) in ["descriptor.mod", "thumbnail.png", "thumbnail.ico", "Steam desc.txt"]:
                pass
            elif len(mods) > 1:
                conflicting_paths = [file_path for file_path in file_paths if os.path.basename(file_path) == os.path.basename(path)]
                if any(os.path.dirname(file_path) == os.path.dirname(path) for file_path in conflicting_paths):
                    red_conflicts[path] = mods
                else:
                    yellow_conflicts[path] = mods

        for mod_folder in mod_localizations:
            mod_path = os.path.join(self.manager.mods_directory, mod_folder, 'localization')
            if 'russian' not in os.listdir(mod_path):
                missing_russian.append(mod_folder)

        missing_translations = self.find_missing_translations()

        update_progress(2, 100)

        self.display_conflicts_signal.emit(red_conflicts, yellow_conflicts, missing_russian)
        self.display_missing_translations_signal.emit(missing_translations)
        self.finding_conflicts = False

    def find_missing_translations(self):
        missing_translations = {}
        for mod in self.manager.mods:
            if not mod.get('enabled'):
                continue

            mod_folder = mod['path'].split('.')[0]
            mod_path = os.path.join(self.manager.mods_directory, mod_folder)
            english_path = os.path.join(mod_path, 'localization', 'english')
            russian_path = os.path.join(mod_path, 'localization', 'russian')

            if not os.path.exists(english_path) or not os.path.exists(russian_path):
                continue

            english_files = [f for f in os.listdir(english_path) if f.endswith('_l_english.yml')]
            russian_files = [f for f in os.listdir(russian_path) if f.endswith('_l_russian.yml')]

            for eng_file in english_files:
                rus_file = eng_file.replace('_l_english.yml', '_l_russian.yml')
                if rus_file not in russian_files:
                    if mod_folder not in missing_translations:
                        missing_translations[mod_folder] = []
                    missing_translations[mod_folder].append(('missing', eng_file))
                else:
                    eng_content = self.read_file_content(os.path.join(english_path, eng_file))
                    rus_content = self.read_file_content(os.path.join(russian_path, rus_file))
                    if self.compare_contents(eng_content, rus_content):
                        if mod_folder not in missing_translations:
                            missing_translations[mod_folder] = []
                        missing_translations[mod_folder].append(('identical', rus_file))

        return missing_translations

    def read_file_content(self, file_path):
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            return file.read()

    def compare_contents(self, eng_content, rus_content):
        eng_lines = eng_content.split('\n')
        rus_lines = rus_content.split('\n')

        if len(eng_lines) != len(rus_lines):
            return False

        different_lines = 0
        for eng_line, rus_line in zip(eng_lines, rus_lines):
            if eng_line.strip() != rus_line.strip():
                different_lines += 1

        # Если менее 10% строк отличаются, считаем содержимое идентичным
        return different_lines / len(eng_lines) < 0.1
    
    def display_conflicts(self, red_conflicts, yellow_conflicts, missing_russian):
        if self.conflict_window is None:
            self.conflict_window = QtWidgets.QDialog(self.parent(), QtCore.Qt.Window)
            self.conflict_window.setWindowTitle("Mod Conflicts")
            self.conflict_window.rejected.connect(self.conflict_window.hide)
        elif self.conflict_window.isVisible():
            self.conflict_window.hide()

        self.conflict_window = QtWidgets.QDialog(self.parent(), QtCore.Qt.Window)
        self.conflict_window.setWindowTitle("Mod Conflicts")

        screen_geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
        max_width = screen_geometry.width()
        max_height = screen_geometry.height()

        self.conflict_window.resize(min(800, max_width), min(600, max_height))
        layout = QtWidgets.QVBoxLayout(self.conflict_window)

        max_mods = 0
        for conflicts in (red_conflicts, yellow_conflicts):
            for mods in conflicts.values():
                if len(mods) > max_mods:
                    max_mods = len(mods)

        table = QtWidgets.QTableWidget()
        total_columns = 2 + max_mods
        table.setColumnCount(total_columns)
        headers = ["", "Mod 1"] + [f"Mod {i+2}" for i in range(max_mods - 1)] + ["Path"]
        table.setHorizontalHeaderLabels(headers)
        layout.addWidget(table)

        def remove_conflict(row_id):
            for row in range(table.rowCount()):
                if table.item(row, 1) and table.item(row, 1).data(QtCore.Qt.UserRole) == row_id:
                    table.removeRow(row)
                    break

        def open_file_explorer(mod_id, mod_path):
            mod_folder = os.path.join(self.manager.mods_directory, mod_id)
            file_path = os.path.join(mod_folder, mod_path)
            folder_path = os.path.dirname(file_path)
            if os.path.isdir(folder_path):
                subprocess.Popen(f'explorer /select,"{file_path}"')

        row_id_counter = 0

        def add_conflict_row(conflicts, table):
            nonlocal row_id_counter
            for path, mods in conflicts.items():
                row_position = table.rowCount()
                table.insertRow(row_position)

                row_id_counter += 1
                row_id = row_id_counter

                remove_button = QtWidgets.QPushButton("X")
                remove_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                remove_button.clicked.connect(lambda _, rid=row_id: remove_conflict(rid))

                widget = QtWidgets.QWidget()
                layout = QtWidgets.QHBoxLayout(widget)
                layout.addWidget(remove_button)
                layout.setContentsMargins(0, 0, 0, 0)
                widget.setLayout(layout)
                table.setCellWidget(row_position, 0, widget)

                for i, mod in enumerate(mods):
                    mod_button = QtWidgets.QPushButton(mod)
                    mod_button.clicked.connect(lambda _, m=mod, p=path: open_file_explorer(m, p))
                    table.setCellWidget(row_position, 1 + i, mod_button)

                id_item = QtWidgets.QTableWidgetItem()
                id_item.setData(QtCore.Qt.UserRole, row_id)
                table.setItem(row_position, 1, id_item)

                path_button = QtWidgets.QPushButton(path)
                path_button.setStyleSheet("text-align: right;")
                table.setCellWidget(row_position, total_columns - 1, path_button)

        add_conflict_row(red_conflicts, table)
        add_conflict_row(yellow_conflicts, table)

        if missing_russian:
            for mod in missing_russian:
                row_position = table.rowCount()
                table.insertRow(row_position)

                missing_label = QtWidgets.QLabel(f"Missing Russian Localization: {mod}")
                table.setCellWidget(row_position, 0, missing_label)
                table.setSpan(row_position, 0, 1, table.columnCount())

                for col in range(table.columnCount()):
                    item = table.item(row_position, col)
                    if item:
                        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsSelectable)
                    widget = table.cellWidget(row_position, col)
                    if widget:
                        widget.setDisabled(True)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        header.setStretchLastSection(False)

        table.resizeColumnsToContents()
        table.setColumnWidth(0, 30)
        table_width = sum(table.columnWidth(i) for i in range(table.columnCount())) + table.verticalHeader().width() + table.verticalScrollBar().sizeHint().width() + 60
        table_height = sum(table.rowHeight(i) for i in range(table.rowCount())) + table.horizontalHeader().height() + table.horizontalScrollBar().sizeHint().height() + 60

        screen_geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
        max_width = screen_geometry.width()
        max_height = screen_geometry.height()

        if table_width > max_width:
            table_width = max_width
        if table_height >= max_height:
            table_height = max_height - 100

        self.conflict_window.resize(table_width, table_height)
        self.conflict_window.show()

    def display_missing_translations(self, missing_translations):
        if self.missing_translations_window is None:
            self.missing_translations_window = QtWidgets.QDialog(self.parent(), QtCore.Qt.Window)
            self.missing_translations_window.setWindowTitle("Missing or Identical Russian Translations")
            self.missing_translations_window.rejected.connect(self.missing_translations_window.hide)
        elif self.missing_translations_window.isVisible():
            self.missing_translations_window.hide()

        layout = QtWidgets.QVBoxLayout(self.missing_translations_window)

        table = QtWidgets.QTableWidget()
        table.setColumnCount(4) 
        table.setHorizontalHeaderLabels(["", "Mod", "Name", "Status"])
        layout.addWidget(table)

        row = 0
        for mod, files in missing_translations.items():
            for status, file in files:
                table.insertRow(row)

                # Колонка X (кнопка удаления)
                remove_button = QtWidgets.QPushButton("X")
                remove_button.clicked.connect(lambda _, r=row: table.removeRow(r))
                table.setCellWidget(row, 0, remove_button)

                # Колонка File 1
                mod_button = QtWidgets.QPushButton(mod)
                mod_button.clicked.connect(lambda _, m=mod, f=file: self.open_file_explorer(m, f))
                table.setCellWidget(row, 1, mod_button)

                # Колонка Path
                path_button = QtWidgets.QPushButton(file)
                path_button.clicked.connect(lambda _, m=mod, f=file: self.open_file_explorer(m, f))
                table.setCellWidget(row, 2, path_button)

                # Колонка Status
                status_text = "Missing Russian Translation" if status == 'missing' else "Identical Content (eng content too)"
                status_item = QtWidgets.QTableWidgetItem(status_text)
                status_item.setForeground(QtGui.QColor(QtCore.Qt.red if status == 'missing' else QtGui.QColor(255, 165, 0)))
                table.setItem(row, 3, status_item)

                row += 1

        header = table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        table.resizeColumnsToContents()
        table.setColumnWidth(0, 30)

        screen_geometry = QtWidgets.QApplication.primaryScreen().availableGeometry()
        table_width = sum(table.columnWidth(i) for i in range(table.columnCount())) + table.verticalHeader().width() + table.verticalScrollBar().sizeHint().width() + 50
        table_height = sum(table.rowHeight(i) for i in range(table.rowCount())) + table.horizontalHeader().height() + table.horizontalScrollBar().sizeHint().height() + 30

        self.missing_translations_window.resize(table_width, table_height)
        self.missing_translations_window.show()

    def open_file_explorer(self, mod_id, file_name):
        mod_folder = os.path.join(self.manager.mods_directory, mod_id)
        english_file_path = os.path.join(mod_folder, 'localization', 'english', file_name)
        russian_file_path = os.path.join(mod_folder, 'localization', 'russian', file_name.replace('_l_english.yml', '_l_russian.yml'))
        
        if os.path.isfile(russian_file_path):
            file_path = russian_file_path
        else:
            file_path = english_file_path
        
        folder_path = os.path.dirname(file_path)
        if os.path.isdir(folder_path):
            subprocess.Popen(f'explorer /select,"{file_path}"', shell=True)
