# ui/ui_helpers.py

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QBrush, QColor, QGradient, QLinearGradient, QRadialGradient, QConicalGradient
import os
import sys

class UIHelpers:
    def __init__(self, manager, ui):
        self.manager = manager
        self.ui = ui

    def get_mod_index(self, mod_path):
        enabled_mods = list(self.manager.mods_data["enabled_mods"].keys())
        try:
            return enabled_mods.index(mod_path)
        except ValueError:
            return float('inf')

    def create_table(self, table, mods):
        table.setRowCount(0)

        if table == self.ui.enabled_mods_table:
            group_headers = {header: [] for header in self.manager.groups}

            for mod in mods:
                mod_path = mod['path']
                added_to_group = False
                for group, paths in self.manager.groups.items():
                    if mod_path in paths:
                        group_headers[group].append(mod)
                        added_to_group = True
                        break

                if not added_to_group:
                    self.add_mod_row(table, mod)

            for group, group_mods in group_headers.items():
                self.create_group_header(table, group)
                for mod in group_mods:
                    self.add_mod_row(table, mod)
        else:
            for mod in mods:
                self.add_mod_row(table, mod)

        # Apply temporary disable status
        for row in range(table.rowCount()):
            mod_path = f"mod/{table.item(row, 3).text()}"
            if not self.manager.mods_data["enabled_mods"].get(mod_path, True):
                self.toggle_temp_disable(table, row)

    def add_mod_row(self, table, mod):
        row_position = table.rowCount()
        table.insertRow(row_position)
        table.setItem(row_position, 0, QtWidgets.QTableWidgetItem(mod['name']))
        table.setItem(row_position, 1, QtWidgets.QTableWidgetItem(mod['version']))
        table.setItem(row_position, 2, QtWidgets.QTableWidgetItem(mod['comment']))
        table.item(row_position, 2).setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
        table.setItem(row_position, 3, QtWidgets.QTableWidgetItem(mod['path']))
        mod_folder_path = os.path.join(self.manager.mods_directory, mod['path'].split('.')[0])
        size_display = self.calculate_folder_size(mod_folder_path)
        table.setItem(row_position, 4, QtWidgets.QTableWidgetItem(size_display))

    def create_group_header(self, table, group_name):
        if table != self.ui.enabled_mods_table:
            return

        row_position = table.rowCount()
        table.insertRow(row_position)
        header_item = QtWidgets.QTableWidgetItem(group_name)
        header_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
        header_item.setTextAlignment(QtCore.Qt.AlignCenter)
        header_item.setData(QtCore.Qt.UserRole, "header")  # Set custom data to identify header

        font = header_item.font()
        font.setBold(True)
        font.setPointSize(12)
        header_item.setFont(font)

        table.setItem(row_position, 0, header_item)
        table.setSpan(row_position, 0, 1, table.columnCount() - 1)

        toggle_button = QtWidgets.QPushButton("Hide")
        button_item = QtWidgets.QTableWidgetItem()
        button_item.setData(QtCore.Qt.UserRole, "button")
        table.setItem(row_position, table.columnCount() - 1, button_item)
        toggle_button.clicked.connect(lambda: self.toggle_group_visibility(table, row_position))
        table.setCellWidget(row_position, table.columnCount() - 1, toggle_button)

        for col in range(1, table.columnCount() - 1):
            empty_item = QtWidgets.QTableWidgetItem()
            empty_item.setFlags(QtCore.Qt.NoItemFlags)
            table.setItem(row_position, col, empty_item)

        self.save_groups_to_manager()

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

    def toggle_mods(self, mod_names, enable):
        if mod_names:
            for mod_name in mod_names:
                if enable:
                    self.manager.enable_mod(mod_name)
                else:
                    self.manager.disable_mod(mod_name)
            self.ui.operations.load_mods()

    def move_items(self, selected_items, direction):
        selected_rows = {item.row() for item in selected_items}
        for row in sorted(selected_rows, reverse=(direction > 0)):
            if row == 0 and direction < 0:
                continue
            if row == self.ui.enabled_mods_table.rowCount() - 1 and direction > 0:
                continue
            self.ui.enabled_mods_table.insertRow(row + direction)
            for col in range(self.ui.enabled_mods_table.columnCount()):
                self.ui.enabled_mods_table.setItem(row + direction, col, self.ui.enabled_mods_table.takeItem(row, col))
            self.ui.enabled_mods_table.removeRow(row)

        self.update_enabled_mods_order()
        self.save_groups_to_manager()

        for row in sorted(selected_rows, reverse=(direction > 0)):
            for col in range(self.ui.enabled_mods_table.columnCount()):
                item = self.ui.enabled_mods_table.item(row + direction, col)
                if item:
                    item.setSelected(True)

    def move_rows(self, source_table, target_table, row_indices):
        for row_index in sorted(row_indices, reverse=True):
            row_data = []
            for col in range(source_table.columnCount()):
                item = source_table.takeItem(row_index, col)
                row_data.append(item)
            
            source_table.removeRow(row_index)
            target_table.insertRow(target_table.rowCount())

            for col, item in enumerate(row_data):
                target_table.setItem(target_table.rowCount() - 1, col, item)

            mod_path = f"mod/{row_data[3].text()}"
            if target_table == self.ui.disabled_mods_table:
                if mod_path in self.manager.mods_data["enabled_mods"]:
                    del self.manager.mods_data["enabled_mods"][mod_path]
            else:
                self.manager.mods_data["enabled_mods"][mod_path] = True

        self.update_enabled_mods_order()
        self.manager.save_mods()
        self.manager.save_temp_mods()

    def update_enabled_mods_order(self):
        new_order = {}
        for row in range(self.ui.enabled_mods_table.rowCount()):
            mod_path = f"mod/{self.ui.enabled_mods_table.item(row, 3).text()}"
            new_order[mod_path] = self.manager.mods_data["enabled_mods"].get(mod_path, True)
        
        # Добавляем моды, которые были в старом порядке, но не попали в новый
        for mod_path, enabled in self.manager.mods_data["enabled_mods"].items():
            if mod_path not in new_order:
                new_order[mod_path] = enabled
        
        self.manager.mods_data["enabled_mods"] = new_order
        self.manager.save_mods()
        self.manager.save_temp_mods()

    def edit_comment(self, table):
        selected_item = table.currentItem()
        if not selected_item or selected_item.column() != 2:
            return

        table.editItem(selected_item)
        table.cellChanged.connect(self.update_comment)

    def update_comment(self, row, column):
        if column == 2:
            table = self.ui.sender()
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
                        
    def toggle_temp_disable(self, table, row):
        mod_item = table.item(row, 0)
        mod_path = f"mod/{table.item(row, 3).text()}"
        if mod_item.font().strikeOut():
            mod_item.setFont(QtGui.QFont())
            for col in range(table.columnCount()):
                table.item(row, col).setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
            self.manager.mods_data["enabled_mods"][mod_path] = True
        else:
            font = QtGui.QFont()
            font.setStrikeOut(True)
            mod_item.setFont(font)
            for col in range(table.columnCount()):
                table.item(row, col).setForeground(QtGui.QBrush(QtGui.QColor(128, 128, 128)))
            self.manager.mods_data["enabled_mods"][mod_path] = False
        
        # Обновляем файлы
        self.manager.save_temp_mods()
        self.manager.save_mods()

    def create_context_menu(self, table, selected_item, column, global_position, selected_items):
        menu = QtWidgets.QMenu(self.ui)
        if selected_item and selected_item.data(QtCore.Qt.UserRole) == "header":  # Check custom data for header
            self.add_header_context_menu_actions(menu, table, selected_item, column, global_position)
        elif selected_item and selected_item.data(QtCore.Qt.UserRole) == "button":  # Check custom data for button
            return  # No actions for button column
        else:
            self.add_mod_context_menu_actions(menu, table, column, global_position, selected_items)
    

    def add_header_context_menu_actions(self, menu, table, selected_item, column, global_position):
        if column == 0:
            rename_action = menu.addAction("Rename Header")
            delete_action = menu.addAction("Delete Header")
            change_color_action = menu.addAction("Change Color (only light theme)")
            remove_color_action = None
            header_text = selected_item.text()
            if header_text in self.manager.colors:
                remove_color_action = menu.addAction("Remove Color")
            action = menu.exec_(global_position)

            if action == rename_action:
                self.rename_header(table, selected_item.row())
            elif action == delete_action:
                self.delete_header(table, selected_item.row())
            elif action == change_color_action:
                self.change_color(table, [selected_item])
            elif action == remove_color_action:
                self.remove_color(table, [selected_item])
        elif column != table.columnCount() - 1:
            rename_action = menu.addAction("Rename Header")
            delete_action = menu.addAction("Delete Header")
            change_color_action = menu.addAction("Change Color")
            remove_color_action = None
            header_text = selected_item.text()
            if header_text in self.manager.colors:
                remove_color_action = menu.addAction("Remove Color")
            action = menu.exec_(global_position)

            if action == rename_action:
                self.rename_header(table, selected_item.row())
            elif action == delete_action:
                self.delete_header(table, selected_item.row())
            elif action == change_color_action:
                self.change_color(table, [selected_item])
            elif action == remove_color_action:
                self.remove_color(table, [selected_item])

    def add_mod_context_menu_actions(self, menu, table, column, global_position, selected_items):
        if table == self.ui.enabled_mods_table:
            create_header_action = menu.addAction("Create Header")
            temp_disable_action = menu.addAction("Temporarily Disable")
            for item in selected_items:
                if item.font().strikeOut():
                    temp_disable_action.setText("Enable")
                    break
        open_folder_action = menu.addAction("Open folder in File Explorer")
        open_steam_action = menu.addAction("Open Steam page")
        find_smods_action = menu.addAction("Find Skymods page")
        view_image_action = menu.addAction("View Image")
        change_color_action = menu.addAction("Change Color")
        remove_color_action = None
        for item in selected_items:
            mod_path = table.item(item.row(), 3).text()
            if mod_path in self.manager.colors:
                remove_color_action = menu.addAction("Remove Color")
                break

        action = menu.exec_(global_position)

        if table == self.ui.enabled_mods_table:
            if action == create_header_action:
                self.create_header(table, selected_items[0].row())
            elif action == temp_disable_action:
                for item in selected_items:
                    self.toggle_temp_disable(table, item.row())
        self.selected_mod_paths = [table.item(item.row(), 3).text() for item in selected_items if item.column() == 3]
        if action == open_folder_action:
            self.open_folder()
        elif action == open_steam_action:
            self.open_steam_page()
        elif action == find_smods_action:
            self.open_smods_page()
        elif action == view_image_action:
            self.view_image()
        elif action == change_color_action:
            self.change_color(table, selected_items)
        elif action == remove_color_action:
            self.remove_color(table, selected_items)

    def rename_header(self, table, row_index):
        header_item = table.item(row_index, 0)
        header_name, ok = QtWidgets.QInputDialog.getText(self.ui, "Rename Header", "Enter new header name:", text=header_item.text())
        if ok and header_name:
            header_item.setText(header_name)
            self.save_groups_to_manager()

    def delete_header(self, table, row_index):
        table.removeRow(row_index)
        self.save_groups_to_manager()

    def create_header(self, table, row_index):
        if table != self.ui.enabled_mods_table:
            return

        header_name, ok = QtWidgets.QInputDialog.getText(self.ui, "Create Header", "Enter header name:")
        if not ok or not header_name:
            return

        table.insertRow(row_index)
        
        header_item = QtWidgets.QTableWidgetItem(header_name)
        header_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
        header_item.setData(QtCore.Qt.UserRole, "header")  # Set custom data to identify header
        table.setItem(row_index, 0, header_item)
        
        # Set empty items for other columns
        for col in range(1, table.columnCount()):
            empty_item = QtWidgets.QTableWidgetItem()
            empty_item.setFlags(QtCore.Qt.NoItemFlags)
            table.setItem(row_index, col, empty_item)

        toggle_button = QtWidgets.QPushButton("Hide")
        toggle_button.clicked.connect(lambda: self.toggle_group_visibility(table, row_index))
        table.setCellWidget(row_index, table.columnCount() - 1, toggle_button)

        self.save_groups_to_manager()

    def toggle_group_visibility(self, table, header_row):
        toggle_button = table.cellWidget(header_row, 4)
        if not toggle_button:
            return

        if toggle_button.text() == "Hide":
            toggle_button.setText("Show")
            self.set_group_visibility(table, header_row, False)
        else:
            toggle_button.setText("Hide")
            self.set_group_visibility(table, header_row, True)

    def set_group_visibility(self, table, header_row, visible):
        row = header_row + 1
        while row < table.rowCount():
            item = table.item(row, 0)
            if item and item.data(QtCore.Qt.UserRole) == "header":
                break
            table.setRowHidden(row, not visible)
            row += 1


    def is_header_row(self, table, row):
        item = table.item(row, 0)
        return item and item.data(QtCore.Qt.UserRole) == "header"

    def save_groups_to_manager(self):
        groups = {}
        current_group = None
        for row in range(self.ui.enabled_mods_table.rowCount()):
            item = self.ui.enabled_mods_table.item(row, 0)
            if item and item.data(QtCore.Qt.UserRole) == "header":
                current_group = item.text()
                groups[current_group] = []
                self.reassign_toggle_button(self.ui.enabled_mods_table, row)
            elif current_group:
                mod_path_item = self.ui.enabled_mods_table.item(row, 3)
                if mod_path_item:
                    mod_path = mod_path_item.text()
                    groups[current_group].append(mod_path)
        
        if not groups:
            print("Warning: No groups found. Keeping existing groups.")
            return

        self.manager.groups = groups
        self.manager.save_groups()

    def reassign_toggle_button(self, table, row):
        toggle_button = table.cellWidget(row, 4)
        if toggle_button is None:
            toggle_button = QtWidgets.QPushButton("Hide")
            toggle_button.clicked.connect(lambda: self.toggle_group_visibility(table, row))
            table.setCellWidget(row, 4, toggle_button)
        else:
            toggle_button.clicked.disconnect()
            toggle_button.clicked.connect(lambda: self.toggle_group_visibility(table, row))

    def refresh_toggle_buttons(self, table):
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.data(QtCore.Qt.UserRole) == "header":
                self.reassign_toggle_button(table, row)

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
        image_window = QtWidgets.QDialog(self.ui)
        image_window.setWindowTitle("Mod Image")
        image_window.resize(400, 400)
        layout = QtWidgets.QVBoxLayout(image_window)

        label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap(image_path)
        label.setPixmap(pixmap.scaled(400, 400, QtCore.Qt.KeepAspectRatio))
        layout.addWidget(label)

        image_window.exec_()

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
        search_layout.addWidget(search_label)

        search_var = QtWidgets.QLineEdit()
        search_var.setStyleSheet("background-color: #444444; color: #ffffff;")
        search_var.textChanged.connect(lambda: self.filter_table(table, search_vars))
        search_layout.addWidget(search_var)

        search_vars[column_index] = search_var

    def apply_filter(self, table, search_vars):
        search_terms = {index: var.text().lower() for index, var in search_vars.items()}
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.data(QtCore.Qt.UserRole) == "header":
                # Always show header rows
                table.setRowHidden(row, False)
                continue
            
            match = all(
                table.item(row, index) is not None and
                term in table.item(row, index).text().lower()
                for index, term in search_terms.items() if term
            )
            table.setRowHidden(row, not match)

    def filter_table(self, table, search_vars):
        self.apply_filter(table, search_vars)

    def load_colors(self):
        for row in range(self.ui.enabled_mods_table.rowCount()):
            item = self.ui.enabled_mods_table.item(row, 0)
            if item and item.data(QtCore.Qt.UserRole) == "header":
                header_text = item.text()
                color = self.manager.colors.get(header_text)
                if color:
                    self.set_custom_color(item, color)
            else:
                mod_path = self.ui.enabled_mods_table.item(row, 3).text()
                if mod_path in self.manager.colors:
                    color = self.manager.colors[mod_path]
                    for col in range(self.ui.enabled_mods_table.columnCount()):
                        cell_item = self.ui.enabled_mods_table.item(row, col)
                        if cell_item:
                            self.set_custom_color(cell_item, color)

        for row in range(self.ui.disabled_mods_table.rowCount()):
            mod_path = self.ui.disabled_mods_table.item(row, 3).text()
            if mod_path in self.manager.colors:
                color = self.manager.colors[mod_path]
                for col in range(self.ui.disabled_mods_table.columnCount()):
                    cell_item = self.ui.disabled_mods_table.item(row, col)
                    if cell_item:
                        self.set_custom_color(cell_item, color)

    def change_color(self, table, selected_items):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            for item in selected_items:
                if item.data(QtCore.Qt.UserRole) == "header":
                    header_text = item.text()
                    self.set_custom_color(item, color.name())
                    self.manager.colors[header_text] = color.name()
                else:
                    row = item.row()
                    for col in range(table.columnCount()):
                        cell_item = table.item(row, col)
                        if cell_item:
                            self.set_custom_color(cell_item, color.name())
                            # mod_path = table.item(row, 3).text()
                            # self.manager.colors[mod_path] = color.name()
            self.manager.save_colors()

    def set_custom_color(self, item, color):
        brush = QtGui.QBrush(QtGui.QColor(color))
        item.setBackground(brush)
        if item.data(QtCore.Qt.UserRole) == "header":
            header_text = item.text()
            self.manager.colors[header_text] = color
            item.setData(QtCore.Qt.UserRole + 1, color)
        else:
            mod_path = item.tableWidget().item(item.row(), 3).text()
            if mod_path:
                self.manager.colors[mod_path] = color
        text_color = "#000000" if self.is_color_light(color) else "#FFFFFF"
        item.setForeground(QtGui.QBrush(QtGui.QColor(text_color)))

    def is_color_light(self, color):
        r, g, b, _ = QtGui.QColor(color).getRgb()
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness > 186
    
    def remove_color(self, table, selected_items):
        for item in selected_items:
            if item.data(QtCore.Qt.UserRole) == "header":
                header_text = item.text()
                if header_text in self.manager.colors:
                    del self.manager.colors[header_text]
                    item.setBackground(QtGui.QBrush())  # Reset background
                    if self.ui.dark_theme_enabled:
                        item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))  # White text for dark theme
                    else:
                        item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))  # Black text for light theme
            else:
                row = item.row()
                mod_path = table.item(row, 3).text()
                if mod_path in self.manager.colors:
                    del self.manager.colors[mod_path]
                    for col in range(table.columnCount()):
                        cell_item = table.item(row, col)
                        if cell_item:
                            cell_item.setBackground(QtGui.QBrush())  # Reset background
                            if self.ui.dark_theme_enabled:
                                cell_item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))  # White text for dark theme
                            else:
                                cell_item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))  # Black text for light theme

        self.manager.save_colors()
        self.load_colors()  # Refresh colors for all items

        # Update the appearance of affected items in the other table
        other_table = self.ui.disabled_mods_table if table == self.ui.enabled_mods_table else self.ui.enabled_mods_table
        for row in range(other_table.rowCount()):
            mod_path = other_table.item(row, 3).text()
            if mod_path not in self.manager.colors:
                for col in range(other_table.columnCount()):
                    cell_item = other_table.item(row, col)
                    if cell_item:
                        cell_item.setBackground(QtGui.QBrush())
                        if self.ui.dark_theme_enabled:
                            cell_item.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
                        else:
                            cell_item.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))

    def save_column_width(self):
        settings = QtCore.QSettings("unrl0000", "UnModManagerCK3")
        comment_width = self.ui.disabled_mods_table.columnWidth(2)
        settings.setValue("comment_column_width", comment_width)

    def load_column_width(self):
        settings = QtCore.QSettings("unrl0000", "UnModManagerCK3")
        comment_width = settings.value("comment_column_width", type=int, defaultValue=200)
        self.ui.disabled_mods_table.setColumnWidth(2, comment_width)
        self.ui.enabled_mods_table.setColumnWidth(2, comment_width)
    
    def apply_stylesheet(self):
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            if self.ui.dark_theme_enabled:
                stylesheet_path = os.path.join(base_path, 'ui/dark_theme.qss')  # for build
                # stylesheet_path = os.path.join(base_path, 'dark_theme.qss')  # for dev
                with open(stylesheet_path, "r") as stylesheet:
                    self.ui.setStyleSheet(stylesheet.read())
            else:
                self.ui.setStyleSheet("")
        except Exception as e:
            print(f"Error applying stylesheet: {e}")

    def toggle_theme(self):
        self.ui.dark_theme_enabled = not self.ui.dark_theme_enabled
        self.apply_stylesheet()
        self.save_theme_preference()
        self.update_theme_button_text()

    def update_theme_button_text(self):
        if self.ui.dark_theme_enabled:
            self.ui.toggle_theme_button.setText("Light Theme")
        else:
            self.ui.toggle_theme_button.setText("Dark Theme")

    def save_theme_preference(self):
        settings = QtCore.QSettings("unrl0000", "UnModManagerCK3")
        settings.setValue("dark_theme_enabled", self.ui.dark_theme_enabled)

    def load_theme_preference(self):
        settings = QtCore.QSettings("unrl0000", "UnModManagerCK3")
        self.ui.dark_theme_enabled = settings.value("dark_theme_enabled", type=bool, defaultValue=False)
