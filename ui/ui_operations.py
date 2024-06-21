# ui/ui_operations.py

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QThread, pyqtSignal
from ui.ui_helpers import UIHelpers
from .conflict_finder import ConflictFinder 

class ModToggleThread(QThread):
    finished = pyqtSignal()

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
        self.finished.emit()

class UIManagerOperations:
    def __init__(self, manager, ui):
        self.manager = manager
        self.ui = ui
        self.helpers = UIHelpers(manager, ui)
        self.conflict_finder = ConflictFinder(manager, ui)

    def load_mods(self):
        self.ui.disabled_mods_table.setRowCount(0)
        self.ui.enabled_mods_table.setRowCount(0)
        mods = self.manager.list_mods()
        
        # Sort mods based on their order in temp_mods
        sorted_mods = sorted(mods, key=lambda x: list(self.manager.mods_data["enabled_mods"].keys()).index(f"mod/{x['path']}")
                            if f"mod/{x['path']}" in self.manager.mods_data["enabled_mods"] else float('inf'))
        
        enabled_mods = [mod for mod in sorted_mods if f"mod/{mod['path']}" in self.manager.mods_data["enabled_mods"]]
        disabled_mods = [mod for mod in sorted_mods if f"mod/{mod['path']}" not in self.manager.mods_data["enabled_mods"]]
        
        self.helpers.create_table(self.ui.disabled_mods_table, disabled_mods)
        self.helpers.create_table(self.ui.enabled_mods_table, enabled_mods)
        self.helpers.update_enabled_mods_order()
        self.helpers.save_groups_to_manager()
        self.load_colors()

    def save_profile(self):
        profile_name = self.ui.save_profile_var.text()
        if not profile_name:
            profile_name = f"Profile {len(self.manager.profiles) + 1}"
        self.manager.save_profile(profile_name)
        self.ui.load_profile_var.clear()
        self.ui.load_profile_var.addItems(list(self.manager.profiles.keys()))
        self.manager.save_profile(self.ui.load_profile_var.currentText())

    def delete_profile(self):
        profile_name = self.ui.load_profile_var.currentText()
        if profile_name:
            self.manager.delete_profile(profile_name)
            self.ui.load_profile_var.clear()
            self.ui.load_profile_var.addItems(list(self.manager.profiles.keys()))

    def load_profile(self):
        profile_name = self.ui.load_profile_var.currentText()
        self.manager.load_profile(profile_name)
        self.load_mods()

    def install_mod(self):
        options = QtWidgets.QFileDialog.Options()
        zip_path, _ = QtWidgets.QFileDialog.getOpenFileName(self.ui, "Open your mod_name.zip", "", "ZIP Files (*.zip)", options=options)
        if zip_path:
            self.manager.install_mod(zip_path)
            self.load_mods()

    def enable_mod(self):
        selected_items = self.ui.disabled_mods_table.selectedItems()
        mod_names = {self.ui.disabled_mods_table.item(item.row(), 0).text() for item in selected_items}
        rows = {item.row() for item in selected_items}

        for row in rows:
            if self.helpers.is_header_row(self.ui.disabled_mods_table, row):
                return 
            
        if mod_names:
            self.toggle_thread = ModToggleThread(self.manager, mod_names, True)
            self.toggle_thread.finished.connect(lambda: self.helpers.move_rows(self.ui.disabled_mods_table, self.ui.enabled_mods_table, rows))
            self.toggle_thread.start()

    def disable_mod(self):
        selected_items = self.ui.enabled_mods_table.selectedItems()
        mod_names = {self.ui.enabled_mods_table.item(item.row(), 0).text() for item in selected_items}
        rows = {item.row() for item in selected_items}

        for row in rows:
            if self.helpers.is_header_row(self.ui.enabled_mods_table, row):
                return
                
        if mod_names:
            self.toggle_thread = ModToggleThread(self.manager, mod_names, False)
            self.toggle_thread.finished.connect(lambda: self.helpers.move_rows(self.ui.enabled_mods_table, self.ui.disabled_mods_table, rows))
            self.toggle_thread.start()

    def move_items(self, selected_items, direction):
        selected_rows = sorted(set(item.row() for item in selected_items))
        
        if direction < 0:  # Moving up
            for row in selected_rows:
                if row == 0 or self.helpers.is_header_row(self.ui.enabled_mods_table, row) or self.helpers.is_header_row(self.ui.enabled_mods_table, row - 1):
                    continue
                self.ui.enabled_mods_table.insertRow(row - 1)
                for col in range(self.ui.enabled_mods_table.columnCount()):
                    self.ui.enabled_mods_table.setItem(row - 1, col, self.ui.enabled_mods_table.takeItem(row + 1, col))
                self.ui.enabled_mods_table.removeRow(row + 1)

        elif direction > 0:  # Moving down
            for row in reversed(selected_rows):
                if row == self.ui.enabled_mods_table.rowCount() - 1 or self.helpers.is_header_row(self.ui.enabled_mods_table, row) or self.helpers.is_header_row(self.ui.enabled_mods_table, row + 1):
                    continue
                self.ui.enabled_mods_table.insertRow(row + 2)
                for col in range(self.ui.enabled_mods_table.columnCount()):
                    self.ui.enabled_mods_table.setItem(row + 2, col, self.ui.enabled_mods_table.takeItem(row, col))
                self.ui.enabled_mods_table.removeRow(row)

        self.helpers.update_enabled_mods_order()
        self.helpers.save_groups_to_manager()

        for row in selected_rows:
            for col in range(self.ui.enabled_mods_table.columnCount()):
                item = self.ui.enabled_mods_table.item(row + direction, col)
                if item:
                    item.setSelected(True)

    def handle_double_click(self, item):
        table = item.tableWidget()
        if self.helpers.is_header_row(table, item.row()):
            table.editItem(item)
            self.helpers.save_groups_to_manager()
            return
        mod_name = table.item(item.row(), 0).text()
        if item.column() == 2:
            self.helpers.edit_comment(table)
        else:
            if table == self.ui.disabled_mods_table:
                self.manager.enable_mod(mod_name)
                self.helpers.move_rows(self.ui.disabled_mods_table, self.ui.enabled_mods_table, {item.row()})
            else:
                self.manager.disable_mod(mod_name)
                self.helpers.move_rows(self.ui.enabled_mods_table, self.ui.disabled_mods_table, {item.row()})
        self.helpers.save_groups_to_manager()

    def drop_event(self, event, target):
        source = event.source()

        if source == target:
            selected_items = source.selectedItems()
            selected_rows = sorted(set(item.row() for item in selected_items))
            
            if any(self.helpers.is_header_row(source, row) for row in selected_rows):
                event.ignore()
                return

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
                    new_row = drop_row + offset
                    target.insertRow(new_row)
                    for col, data in enumerate(row_data):
                        item = QtWidgets.QTableWidgetItem(data)
                        target.setItem(new_row, col, item)

                    # Обновляем mods_data и стиль
                    mod_path = f"mod/{row_data[3]}"
                    if target == self.ui.disabled_mods_table:
                        if mod_path in self.manager.mods_data["enabled_mods"]:
                            del self.manager.mods_data["enabled_mods"][mod_path]
                    else:
                        is_temp_disabled = not self.manager.mods_data["enabled_mods"].get(mod_path, True)
                        self.manager.mods_data["enabled_mods"][mod_path] = True
                        if is_temp_disabled:
                            self.helpers.toggle_temp_disable(target, new_row)
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
                        target.setItem(target.rowCount() - 1, col, QtWidgets.QTableWidgetItem(data))

            self.helpers.update_enabled_mods_order()
            event.accept()
            self.manager.sync_enabled_mods()
            self.helpers.save_groups_to_manager()
            self.helpers.refresh_toggle_buttons(target)
            self.load_colors()
            return
        else:
            # Это случай, когда мы перетаскиваем между таблицами (включение/отключение модов)
            selected_items = source.selectedItems()
            selected_rows = sorted(set(item.row() for item in selected_items))

            if any(self.helpers.is_header_row(source, row) for row in selected_rows):
                event.ignore()
                return

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
                    target.setItem(drop_row + offset, col, QtWidgets.QTableWidgetItem(data))

                # Обновляем mods_data
                mod_path = f"mod/{row_data[3]}"  # Предполагается, что путь мода находится в 4-м столбце
                if target == self.ui.disabled_mods_table:
                    # Мод отключен
                    if mod_path in self.manager.mods_data["enabled_mods"]:
                        del self.manager.mods_data["enabled_mods"][mod_path]
                else:
                    # Мод включен
                    self.manager.mods_data["enabled_mods"][mod_path] = True

        self.helpers.update_enabled_mods_order()
        event.accept()
        self.manager.sync_enabled_mods()
        self.manager.save_mods()  # Сохраняем изменения
        self.manager.save_temp_mods()  # Сохраняем изменения в temp_mods
        self.helpers.save_groups_to_manager()
        self.helpers.refresh_toggle_buttons(target)
        self.load_colors()

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def find_conflicts(self):
        self.conflict_finder.find_conflicts()

    def show_context_menu(self, position):
        table = self.ui.sender()
        global_position = table.viewport().mapToGlobal(position)
        selected_items = table.selectedItems()
        if not selected_items:
            return

        selected_item = table.itemAt(position)
        column = table.columnAt(position.x())
        self.helpers.create_context_menu(table, selected_item, column, global_position, selected_items)

    def apply_stylesheet(self):
        self.helpers.apply_stylesheet()

    def create_search_button(self, parent, table, search_vars, alignment):
        self.helpers.create_search_button(parent, table, search_vars, alignment)

    def save_column_width(self):
        self.helpers.save_column_width()

    def load_column_width(self):
        self.helpers.load_column_width()

    def load_colors(self):
        self.helpers.load_colors()

    def toggle_theme(self):
        self.helpers.toggle_theme()

    def save_theme_preference(self):
        self.helpers.save_theme_preference()

    def update_theme_button_text(self):
        self.helpers.update_theme_button_text()

    def load_theme_preference(self):
        self.helpers.load_theme_preference()
