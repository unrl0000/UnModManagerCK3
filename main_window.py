import os
import sys
import time
import threading
import concurrent.futures
from collections import defaultdict
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog, QMenu, QTableWidgetItem, QHeaderView
                
class ModManagerUI(QtWidgets.QMainWindow):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.conflict_finder = ConflictFinder(manager, self)
        self.setWindowTitle("CK3 UnMod Manager")
        self.setGeometry(100, 100, 1000, 600)

        self.disabled_search_vars = {}
        self.enabled_search_vars = {}
        
        self.initUI()
        self.load_mods()
        self.apply_stylesheet()

    def initUI(self):
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        self.profile_frame = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.profile_frame)

        self.save_profile_button = QtWidgets.QPushButton("Save Profile")
        self.save_profile_button.clicked.connect(self.save_profile)
        self.profile_frame.addWidget(self.save_profile_button)

        self.save_profile_var = QtWidgets.QLineEdit()
        self.profile_frame.addWidget(self.save_profile_var)

        self.delete_profile_button = QtWidgets.QPushButton("Delete Profile")
        self.delete_profile_button.clicked.connect(self.delete_profile)
        self.profile_frame.addWidget(self.delete_profile_button)

        self.load_profile_button = QtWidgets.QPushButton("Load Profile")
        self.load_profile_button.clicked.connect(self.load_profile)
        self.profile_frame.addWidget(self.load_profile_button)

        self.load_profile_var = QtWidgets.QComboBox()
        self.load_profile_var.addItems(list(self.manager.profiles.keys()))
        self.profile_frame.addWidget(self.load_profile_var)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.layout.addWidget(self.splitter)

        self.left_frame = QtWidgets.QWidget()
        self.left_layout = QtWidgets.QVBoxLayout(self.left_frame)
        self.splitter.addWidget(self.left_frame)

        self.right_frame = QtWidgets.QWidget()
        self.right_layout = QtWidgets.QVBoxLayout(self.right_frame)
        self.splitter.addWidget(self.right_frame)

        self.disabled_mods_table = QtWidgets.QTableWidget()
        self.disabled_mods_table.setColumnCount(5)
        self.disabled_mods_table.setHorizontalHeaderLabels(["Name", "Version", "Comment", "Path", "Size"])
        self.disabled_mods_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Name
        self.disabled_mods_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Version
        self.disabled_mods_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)  # Comment
        self.disabled_mods_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Path
        self.disabled_mods_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Size
        self.disabled_mods_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.disabled_mods_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.disabled_mods_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.disabled_mods_table.customContextMenuRequested.connect(self.show_context_menu)

        self.disabled_mods_table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.disabled_mods_table.setDragEnabled(True)
        self.disabled_mods_table.setAcceptDrops(True)
        self.disabled_mods_table.setDropIndicatorShown(True)
        self.disabled_mods_table.viewport().setAcceptDrops(True)
        self.disabled_mods_table.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.disabled_mods_table.dropEvent = lambda event: self.drop_event(event, self.disabled_mods_table)

        self.left_layout.addWidget(self.disabled_mods_table)

        self.enabled_mods_table = QtWidgets.QTableWidget()
        self.enabled_mods_table.setColumnCount(5)
        self.enabled_mods_table.setHorizontalHeaderLabels(["Name", "Version", "Comment", "Path", "Size"])
        self.enabled_mods_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Name
        self.enabled_mods_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Version
        self.enabled_mods_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)  # Comment
        self.enabled_mods_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Path
        self.enabled_mods_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Size
        self.enabled_mods_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.enabled_mods_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.enabled_mods_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.enabled_mods_table.customContextMenuRequested.connect(self.show_context_menu)

        self.enabled_mods_table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.enabled_mods_table.setDragEnabled(True)
        self.enabled_mods_table.setAcceptDrops(True)
        self.enabled_mods_table.setDropIndicatorShown(True)
        self.enabled_mods_table.viewport().setAcceptDrops(True)
        self.enabled_mods_table.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.enabled_mods_table.dropEvent = lambda event: self.drop_event(event, self.enabled_mods_table)

        self.right_layout.addWidget(self.enabled_mods_table)

        self.button_frame = QtWidgets.QHBoxLayout()
        self.left_layout.addLayout(self.button_frame)

        self.install_button = QtWidgets.QPushButton("Install")
        self.install_button.clicked.connect(self.install_mod)
        self.button_frame.addWidget(self.install_button)

        self.refresh_button = QtWidgets.QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_mods)
        self.button_frame.addWidget(self.refresh_button)

        self.enable_button = QtWidgets.QPushButton("Enable Mod")
        self.enable_button.clicked.connect(self.enable_mod)
        self.button_frame.addWidget(self.enable_button)

        self.move_buttons_frame = QtWidgets.QHBoxLayout()
        self.right_layout.addLayout(self.move_buttons_frame)

        self.disable_button = QtWidgets.QPushButton("Disable Mod")
        self.disable_button.clicked.connect(self.disable_mod)
        self.move_buttons_frame.addWidget(self.disable_button)

        self.up_button = QtWidgets.QPushButton("Move Up")
        self.up_button.clicked.connect(self.move_up)
        self.move_buttons_frame.addWidget(self.up_button)

        self.down_button = QtWidgets.QPushButton("Move Down")
        self.down_button.clicked.connect(self.move_down)
        self.move_buttons_frame.addWidget(self.down_button)

        self.conflict_button = QtWidgets.QPushButton("Find Conflicts")
        self.conflict_button.clicked.connect(self.find_conflicts)
        self.move_buttons_frame.addWidget(self.conflict_button)

        # self.toggle_preview_button = QtWidgets.QPushButton("Toggle Preview")
        # self.toggle_preview_button.clicked.connect(self.toggle_preview)
        # self.move_buttons_frame.addWidget(self.toggle_preview_button)

        self.preview_on_hover = True
        self.last_conflict_check_time = 0
        self.disabled_mods_table.itemDoubleClicked.connect(self.handle_double_click)
        self.enabled_mods_table.itemDoubleClicked.connect(self.handle_double_click)
        self.disabled_mods_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.disabled_mods_table.customContextMenuRequested.connect(self.show_context_menu)
        self.enabled_mods_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.enabled_mods_table.customContextMenuRequested.connect(self.show_context_menu)

        self.create_search_button(self.left_layout, self.disabled_mods_table, self.disabled_search_vars, QtCore.Qt.AlignLeft)
        self.create_search_button(self.right_layout, self.enabled_mods_table, self.enabled_search_vars, QtCore.Qt.AlignLeft)

        self.disabled_mods_table.viewport().installEventFilter(self)
        self.enabled_mods_table.viewport().installEventFilter(self)

        self.disabled_mods_table.setMinimumWidth(int(self.width() / 1))
        self.enabled_mods_table.setMinimumWidth(int(self.width() / 1))

        self.disabled_mods_table.horizontalHeader().sectionResized.connect(self.save_column_width)
        self.enabled_mods_table.horizontalHeader().sectionResized.connect(self.save_column_width)

        self.load_column_width()
        
    def create_search_button(self, parent, table, search_vars, alignment):
        button_frame = QtWidgets.QFrame()
        button_layout = QtWidgets.QHBoxLayout(button_frame)
        button_layout.setAlignment(alignment)
        parent.addWidget(button_frame)

        toggle_button = QtWidgets.QPushButton("Show Search")
        toggle_button.setStyleSheet("background-color: #444444; color: #ffffff;")
        toggle_button.clicked.connect(lambda: self.toggle_search(button_frame, table, search_vars, toggle_button))
        button_layout.addWidget(toggle_button)

    def toggle_search(self, parent, table, search_vars, button):
        if button.text() == "Show Search":
            button.setText("Hide Search")
            self.show_search_entries(parent, table, search_vars)
        else:
            button.setText("Show Search")
            self.hide_search_entries(parent)

    def show_search_entries(self, parent, table, search_vars):
        for index, column_name in enumerate(["Name", "Version", "Comment", "Path"]):
            self.create_search_entry(parent, index, column_name, table, search_vars)

    def hide_search_entries(self, parent):
        for widget in parent.children():
            if isinstance(widget, QtWidgets.QWidget) and any(isinstance(child, QtWidgets.QLineEdit) for child in widget.children()):
                widget.deleteLater()

    def create_search_entry(self, parent, column_index, column_name, table, search_vars):
        search_frame = QtWidgets.QFrame()
        search_layout = QtWidgets.QHBoxLayout(search_frame)
        parent.layout().insertWidget(1, search_frame)

        search_label = QtWidgets.QLabel(f"Search {column_name}")
        search_label.setStyleSheet("color: #ffffff;")
        search_layout.addWidget(search_label)

        search_var = QtWidgets.QLineEdit()
        search_var.setStyleSheet("background-color: #444444; color: #ffffff;")
        search_var.textChanged.connect(lambda: self.filter_table(table, search_vars))
        search_layout.addWidget(search_var)

        search_vars[column_index] = search_var

    def apply_filter(self, table, search_vars):
        search_terms = {index: var.text().lower() for index, var in search_vars.items()}
        for row in range(table.rowCount()):
            match = True
            for index, term in search_terms.items():
                item = table.item(row, index)
                if term not in item.text().lower():
                    match = False
                    break
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if match:
                    item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
                else:
                    item.setForeground(QtGui.QBrush(QtGui.QColor(128, 128, 128)))

    def filter_table(self, table, search_vars):
        self.apply_filter(table, search_vars)

    def drop_event(self, event, target):
        source = event.source()

        if source == target:
            selected_items = source.selectedItems()
            selected_rows = sorted(set(item.row() for item in selected_items))

            drop_row = target.rowAt(event.pos().y())
            if drop_row == -1:
                drop_row = target.rowCount()

            if drop_row < target.rowCount() - len(selected_rows):
                row_data_list = []
                for row in selected_rows:
                    row_data = []
                    for col in range(source.columnCount()):
                        item = source.item(row, col)
                        row_data.append(item.text() if item else "")
                    row_data_list.append(row_data)

                for row in reversed(selected_rows):
                    source.removeRow(row)

                for offset, row_data in enumerate(row_data_list):
                    target.insertRow(drop_row + offset)
                    for col, data in enumerate(row_data):
                        target.setItem(drop_row + offset, col, QTableWidgetItem(data))
            else:
                row_data_list = []
                for row in selected_rows:
                    row_data = []
                    for col in range(source.columnCount()):
                        item = source.item(row, col)
                        row_data.append(item.text() if item else "")
                    row_data_list.append(row_data)

                for row in reversed(selected_rows):
                    source.removeRow(row)

                for row_data in row_data_list:
                    target.insertRow(target.rowCount())
                    for col, data in enumerate(row_data):
                        target.setItem(target.rowCount() - 1, col, QTableWidgetItem(data))

            self.update_enabled_mods_order()
            event.accept()
            self.manager.sync_enabled_mods()
            return

        selected_items = source.selectedItems()
        selected_rows = sorted(set(item.row() for item in selected_items))

        drop_row = target.rowAt(event.pos().y())
        if drop_row == -1:
            drop_row = target.rowCount()

        row_data_list = []
        for row in selected_rows:
            row_data = []
            for col in range(source.columnCount()):
                item = source.item(row, col)
                row_data.append(item.text() if item else "")
            row_data_list.append(row_data)

        for row in reversed(selected_rows):
            source.removeRow(row)

        for offset, row_data in enumerate(row_data_list):
            target.insertRow(drop_row + offset)
            for col, data in enumerate(row_data):
                target.setItem(drop_row + offset, col, QTableWidgetItem(data))

        self.update_enabled_mods_order()
        event.accept()
        self.manager.sync_enabled_mods()

    def dropEvent(self, event):
        source = event.source()
        if source not in [self.disabled_mods_table, self.enabled_mods_table]:
            return super().dropEvent(event)

        target = self.enabled_mods_table if source == self.disabled_mods_table else self.disabled_mods_table

        selected_rows = source.selectionModel().selectedRows()
        if not selected_rows:
            return

        drop_row = target.rowAt(event.pos().y())
        if drop_row == -1:
            drop_row = target.rowCount()

        selected_data = []
        for row in selected_rows:
            row_data = []
            for column in range(source.columnCount()):
                item = source.item(row.row(), column)
                row_data.append(item.text() if item else "")
            selected_data.append(row_data)

        for row in selected_data:
            target.insertRow(drop_row)
            for column, data in enumerate(row):
                target.setItem(drop_row, column, QTableWidgetItem(data))

        for row in reversed(sorted(selected_rows)):
            source.removeRow(row.row())

        self.update_enabled_mods_order()
        event.accept()
        self.manager.sync_enabled_mods()

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def save_profile(self):
        profile_name = self.save_profile_var.text()
        if not profile_name:
            profile_name = f"Profile {len(self.manager.profiles) + 1}"
        self.manager.save_profile(profile_name)
        self.load_profile_var.clear()
        self.load_profile_var.addItems(list(self.manager.profiles.keys()))

    def delete_profile(self):
        profile_name = self.load_profile_var.currentText()
        if profile_name:
            self.manager.delete_profile(profile_name)
            self.load_profile_var.clear()
            self.load_profile_var.addItems(list(self.manager.profiles.keys()))

    def load_profile(self):
        profile_name = self.load_profile_var.currentText()
        self.manager.load_profile(profile_name)
        self.load_mods()

    def install_mod(self):
        options = QFileDialog.Options()
        zip_path, _ = QFileDialog.getOpenFileName(self, "Open your mod_name.zip", "", "ZIP Files (*.zip)", options=options)
        if zip_path:
            self.manager.install_mod(zip_path)
            self.load_mods()

    def load_mods(self):
        self.disabled_mods_table.setRowCount(0)
        self.enabled_mods_table.setRowCount(0)

        mods = self.manager.list_mods()
        enabled_mods = sorted([mod for mod in mods if mod.get('enabled')],
                            key=lambda x: self.get_mod_index(f"mod/{x['path']}"))
        disabled_mods = [mod for mod in mods if not mod.get('enabled')]

        self.create_table(self.disabled_mods_table, disabled_mods)
        self.create_table(self.enabled_mods_table, enabled_mods)
        self.update_enabled_mods_order()

    def get_mod_index(self, mod_path):
        try:
            return self.manager.dlc_data["enabled_mods"].index(mod_path)
        except ValueError:
            return float('inf')
        
    def save_column_width(self):
        settings = QtCore.QSettings("MyCompany", "CK3UnModManager")
        comment_width = self.disabled_mods_table.columnWidth(2)
        settings.setValue("comment_column_width", comment_width)

    def load_column_width(self):
        settings = QtCore.QSettings("MyCompany", "CK3UnModManager")
        comment_width = settings.value("comment_column_width", type=int, defaultValue=200)
        self.disabled_mods_table.setColumnWidth(2, comment_width) 
        self.enabled_mods_table.setColumnWidth(2, comment_width)

    def create_table(self, table, mods):
        for mod in mods:
            row_position = table.rowCount()
            table.insertRow(row_position)
            table.setItem(row_position, 0, QTableWidgetItem(mod['name']))
            table.setItem(row_position, 1, QTableWidgetItem(mod['version']))
            table.setItem(row_position, 2, QTableWidgetItem(mod['comment']))
            table.item(row_position, 2).setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
            table.setItem(row_position, 3, QTableWidgetItem(mod['path']))

            mod_folder_path = os.path.join(self.manager.mods_directory, mod['path'].split('.')[0])
            size_display = self.calculate_folder_size(mod_folder_path)
            table.setItem(row_position, 4, QTableWidgetItem(size_display))

    def calculate_folder_size(self, folder_path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        size_in_mb = total_size / (1024 * 1024)
        if size_in_mb > 99:
            return f"{size_in_mb / 1024:.2f} GB"
        else:
            return f"{size_in_mb:.2f} MB"

    def enable_mod(self):
        selected_items = self.disabled_mods_table.selectedItems()
        mod_names = {self.disabled_mods_table.item(item.row(), 0).text() for item in selected_items}

        if mod_names:
            self.toggle_thread = ModToggleThread(self.manager, mod_names, True)
            self.toggle_thread.finished.connect(lambda: self.move_rows(self.disabled_mods_table, self.enabled_mods_table, mod_names))
            self.toggle_thread.start()

    def disable_mod(self):
        selected_items = self.enabled_mods_table.selectedItems()
        mod_names = {self.enabled_mods_table.item(item.row(), 0).text() for item in selected_items}

        if mod_names:
            self.toggle_thread = ModToggleThread(self.manager, mod_names, False)
            self.toggle_thread.finished.connect(lambda: self.move_rows(self.enabled_mods_table, self.disabled_mods_table, mod_names))
            self.toggle_thread.start()

    def move_rows(self, source_table, target_table, mod_names):
        rows_to_move = []
        for row in range(source_table.rowCount()):
            mod_name = source_table.item(row, 0).text()
            if mod_name in mod_names:
                row_data = []
                for col in range(source_table.columnCount()):
                    item = source_table.takeItem(row, col)
                    row_data.append(item)
                rows_to_move.append((row, row_data))

        for row, row_data in reversed(rows_to_move):
            source_table.removeRow(row)
            target_table.insertRow(target_table.rowCount())
            for col, item in enumerate(row_data):
                target_table.setItem(target_table.rowCount() - 1, col, item)

        self.update_enabled_mods_order()

    def move_up(self):
        selected_items = self.enabled_mods_table.selectedItems()
        if not selected_items:
            return

        selected_rows = {item.row() for item in selected_items}
        for row in sorted(selected_rows):
            if row == 0:
                continue
            self.enabled_mods_table.insertRow(row - 1)
            for col in range(self.enabled_mods_table.columnCount()):
                self.enabled_mods_table.setItem(row - 1, col, self.enabled_mods_table.takeItem(row + 1, col))
            self.enabled_mods_table.removeRow(row + 1)

        self.update_enabled_mods_order()

        for row in sorted(selected_rows):
            for col in range(self.enabled_mods_table.columnCount()):
                item = self.enabled_mods_table.item(row - 1, col)
                if item:
                    item.setSelected(True)

    def move_down(self):
        selected_items = self.enabled_mods_table.selectedItems()
        if not selected_items:
            return

        selected_rows = {item.row() for item in selected_items}
        for row in sorted(selected_rows, reverse=True):
            if row == self.enabled_mods_table.rowCount() - 1:
                continue
            self.enabled_mods_table.insertRow(row + 2)
            for col in range(self.enabled_mods_table.columnCount()):
                self.enabled_mods_table.setItem(row + 2, col, self.enabled_mods_table.takeItem(row, col))
            self.enabled_mods_table.removeRow(row)

        self.update_enabled_mods_order()

        for row in sorted(selected_rows, reverse=True):
            for col in range(self.enabled_mods_table.columnCount()):
                item = self.enabled_mods_table.item(row + 1, col)
                if item:
                    item.setSelected(True)

    def update_enabled_mods_order(self):
        new_order = []
        for row in range(self.enabled_mods_table.rowCount()):
            mod_name = self.enabled_mods_table.item(row, 0).text()
            for mod in self.manager.mods:
                if mod.get('name') == mod_name:
                    mod_file_path = f"mod/{mod['path']}"
                    new_order.append(mod_file_path)
                    break
        self.manager.dlc_data["enabled_mods"] = new_order
        self.manager.save_dlc_load()

    def toggle_preview(self):
        self.preview_on_hover = not self.preview_on_hover

    def show_context_menu(self, position):
        menu = QMenu()

        open_folder_action = menu.addAction("Open folder in File Explorer")
        open_steam_action = menu.addAction("Open Steam page")
        find_smods_action = menu.addAction("Find Skymods page")
        view_image_action = menu.addAction("View Image")

        table = self.sender()
        global_position = table.viewport().mapToGlobal(position)
        selected_items = table.selectedItems()
        if selected_items:
            self.selected_mod_paths = [table.item(item.row(), 3).text() for item in selected_items if item.column() == 0]

        action = menu.exec_(global_position)

        if action == open_folder_action:
            self.open_folder()
        elif action == open_steam_action:
            self.open_steam_page()
        elif action == find_smods_action:
            self.open_smods_page()
        elif action == view_image_action:
            self.view_image()

    def open_folder(self):
        for mod_path in self.selected_mod_paths:
            folder_path = os.path.join(self.manager.mods_directory, mod_path.split('.')[0])
            if os.path.isdir(folder_path):
                os.startfile(folder_path)

    def open_steam_page(self):
        for mod_path in self.selected_mod_paths:
            mod_id = mod_path.split('.')[0]
            steam_url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"
            os.system(f'start {steam_url}')
        
    def open_smods_page(self):
        for mod_path in self.selected_mod_paths:
            mod_id = mod_path.split('.')[0]
            smods_url = f"https://catalogue.smods.ru/?s={mod_id}&app=1158310"
            os.system(f'start {smods_url}')

    def view_image(self):
        for mod_path in self.selected_mod_paths:
            mod_folder = os.path.join(self.manager.mods_directory, mod_path.split('.')[0])
            image_path = os.path.join(mod_folder, 'thumbnail.png')
            if os.path.isfile(image_path):
                self.show_image_window(image_path)

    def show_image_window(self, image_path):
        image_window = QtWidgets.QDialog(self)
        image_window.setWindowTitle("Mod Image")
        image_window.resize(400, 400)
        layout = QtWidgets.QVBoxLayout(image_window)

        label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap(image_path)
        label.setPixmap(pixmap.scaled(400, 400, QtCore.Qt.KeepAspectRatio))
        layout.addWidget(label)

        image_window.exec_()

    def selected_mod_path(self):
        selected_item = self.disabled_mods_table.selectedItems()
        if not selected_item:
            selected_item = self.enabled_mods_table.selectedItems()
        if selected_item:
            return selected_item[0].text()
        return None

    def handle_double_click(self, item):
        table = item.tableWidget()
        mod_name = table.item(item.row(), 0).text()
        
        if item.column() == 2:
            self.edit_comment(table)
        else:
            if table == self.disabled_mods_table:
                self.manager.enable_mod(mod_name)
                self.move_row(self.disabled_mods_table, self.enabled_mods_table, item.row())
            else:
                self.manager.disable_mod(mod_name)
                self.move_row(self.enabled_mods_table, self.disabled_mods_table, item.row())

    def move_row(self, source_table, target_table, row_index):
        row_data = []
        for col in range(source_table.columnCount()):
            item = source_table.takeItem(row_index, col)
            row_data.append(item)

        source_table.removeRow(row_index)
        target_table.insertRow(target_table.rowCount())

        for col, item in enumerate(row_data):
            target_table.setItem(target_table.rowCount() - 1, col, item)

        self.update_enabled_mods_order()

    def update_enabled_mods_order(self):
        new_order = []
        for row in range(self.enabled_mods_table.rowCount()):
            mod_name = self.enabled_mods_table.item(row, 0).text()
            for mod in self.manager.mods:
                if mod.get('name') == mod_name:
                    mod_file_path = f"mod/{mod['path']}"
                    new_order.append(mod_file_path)
                    break
        self.manager.dlc_data["enabled_mods"] = new_order
        self.manager.save_dlc_load()

    def edit_comment(self, table):
        selected_item = table.currentItem()
        if not selected_item or selected_item.column() != 2:
            return

        table.editItem(selected_item)
        table.cellChanged.connect(self.update_comment)

    def update_comment(self, row, column):
        if column == 2: 
            table = self.sender()
            item = table.item(row, column)
            if item is not None:
                new_comment = item.text()

                mod_path_item = table.item(row, 3)
                if mod_path_item is not None:
                    mod_path = mod_path_item.text()
                    self.manager.comments[mod_path] = new_comment 
                    self.manager.save_comments()
                    table.cellChanged.disconnect(self.update_comment)
                    table.cellChanged.connect(self.update_comment)

    def apply_stylesheet(self):
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            stylesheet_path = os.path.join(base_path, 'modmanager/ui/dark_theme.qss') # for build
            # stylesheet_path = os.path.join(base_path, 'dark_theme.qss') # for dev
            with open(stylesheet_path, "r") as stylesheet:
                self.setStyleSheet(stylesheet.read())
        except Exception as e:
            print(f"Error applying stylesheet: {e}")

    def find_conflicts(self):
        self.conflict_finder.find_conflicts()

class ConflictFinder(QtCore.QObject):
    update_progress_signal = QtCore.pyqtSignal(int)
    display_conflicts_signal = QtCore.pyqtSignal(dict, dict, list)

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.last_conflict_check_time = 0
        self.conflict_window = None

    def find_conflicts(self):
        current_time = time.time()
        if current_time - self.last_conflict_check_time < 3:
            return
        self.last_conflict_check_time = current_time

        if hasattr(self, 'progress_window') and self.progress_window:
            self.progress_window.close()

        self.progress_window = QtWidgets.QProgressDialog("Finding Conflicts, Please Wait...", "Cancel", 0, 100, self.parent())
        self.progress_window.setWindowModality(QtCore.Qt.WindowModal)
        self.progress_window.show()

        self.update_progress_signal.connect(self.progress_window.setValue)
        self.display_conflicts_signal.connect(self.display_conflicts)

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

        update_progress(2, 100)

        self.display_conflicts_signal.emit(red_conflicts, yellow_conflicts, missing_russian)

    def display_conflicts(self, red_conflicts, yellow_conflicts, missing_russian):
        if self.conflict_window:
            self.conflict_window.close()

        self.conflict_window = QtWidgets.QDialog(self.parent())
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
                os.system(f'explorer /select,"{file_path}"')

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

        if table_width > max_width:
            table_width = max_width
        if table_height >= max_height:
            table_height = max_height - 100

        self.conflict_window.resize(table_width, table_height)
        self.conflict_window.exec_()

class ModToggleThread(QtCore.QThread):
    def __init__(self, manager, mod_names, enable):
        super().__init__()
        self.manager = manager
        self.mod_names = mod_names
        self.enable = enable

    def run(self):
        for mod_name in self.mod_names:
            if self.enable:
                self.manager.enable_mod(mod_name)
            else:
                self.manager.disable_mod(mod_name)
