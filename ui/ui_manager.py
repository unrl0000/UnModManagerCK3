# ui/ui_manager.py

from PyQt5 import QtWidgets, QtGui, QtCore
from ui.ui_operations import UIManagerOperations
import sys
import os

class ModManagerUI(QtWidgets.QMainWindow):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.operations = UIManagerOperations(manager, self)
        self.setWindowTitle("UnModManagerCK3")
        self.setGeometry(100, 100, 1000, 600)
        self.dark_theme_enabled = True
        self.initUI()
        self.operations.load_mods()
        self.apply_stylesheet()
        self.operations.load_mods()
        self.operations.load_colors()

    def initUI(self):
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        self.profile_frame = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.profile_frame)

        self.save_profile_button = QtWidgets.QPushButton("Save Profile")
        self.save_profile_button.clicked.connect(self.operations.save_profile)
        self.profile_frame.addWidget(self.save_profile_button)

        self.save_profile_var = QtWidgets.QLineEdit()
        self.profile_frame.addWidget(self.save_profile_var)

        self.delete_profile_button = QtWidgets.QPushButton("Delete Profile")
        self.delete_profile_button.clicked.connect(self.operations.delete_profile)
        self.profile_frame.addWidget(self.delete_profile_button)

        self.load_profile_button = QtWidgets.QPushButton("Load Profile")
        self.load_profile_button.clicked.connect(self.operations.load_profile)
        self.profile_frame.addWidget(self.load_profile_button)

        self.load_profile_var = QtWidgets.QComboBox()
        self.load_profile_var.addItems(list(self.manager.profiles.keys()))
        self.profile_frame.addWidget(self.load_profile_var)

        self.toggle_theme_button = QtWidgets.QPushButton("Light Theme")
        self.toggle_theme_button.clicked.connect(self.operations.toggle_theme)
        self.profile_frame.addWidget(self.toggle_theme_button)

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
        self.disabled_mods_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.disabled_mods_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.disabled_mods_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Interactive)
        self.disabled_mods_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.disabled_mods_table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
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
        self.disabled_mods_table.dropEvent = lambda event: self.operations.drop_event(event, self.disabled_mods_table)

        self.left_layout.addWidget(self.disabled_mods_table)

        self.enabled_mods_table = QtWidgets.QTableWidget()
        self.enabled_mods_table.setColumnCount(5)
        self.enabled_mods_table.setHorizontalHeaderLabels(["Name", "Version", "Comment", "Path", "Size"])
        self.enabled_mods_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.enabled_mods_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.enabled_mods_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Interactive)
        self.enabled_mods_table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.enabled_mods_table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
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
        self.enabled_mods_table.dropEvent = lambda event: self.operations.drop_event(event, self.enabled_mods_table)

        self.right_layout.addWidget(self.enabled_mods_table)

        self.button_frame = QtWidgets.QHBoxLayout()
        self.left_layout.addLayout(self.button_frame)

        self.install_button = QtWidgets.QPushButton("Install")
        self.install_button.clicked.connect(self.operations.install_mod)
        self.button_frame.addWidget(self.install_button)

        self.refresh_button = QtWidgets.QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.operations.load_mods)
        self.button_frame.addWidget(self.refresh_button)

        self.enable_button = QtWidgets.QPushButton("Enable Mod")
        self.enable_button.clicked.connect(self.operations.enable_mod)
        self.button_frame.addWidget(self.enable_button)

        self.move_buttons_frame = QtWidgets.QHBoxLayout()
        self.right_layout.addLayout(self.move_buttons_frame)

        self.disable_button = QtWidgets.QPushButton("Disable Mod")
        self.disable_button.clicked.connect(self.operations.disable_mod)
        self.move_buttons_frame.addWidget(self.disable_button)

        self.up_button = QtWidgets.QPushButton("Move Up")
        self.up_button.clicked.connect(lambda: self.operations.move_items(self.enabled_mods_table.selectedItems(), -1))
        self.move_buttons_frame.addWidget(self.up_button)

        self.down_button = QtWidgets.QPushButton("Move Down")
        self.down_button.clicked.connect(lambda: self.operations.move_items(self.enabled_mods_table.selectedItems(), 1))
        self.move_buttons_frame.addWidget(self.down_button)

        self.conflict_button = QtWidgets.QPushButton("Find Conflicts")
        self.conflict_button.clicked.connect(self.operations.find_conflicts)
        self.move_buttons_frame.addWidget(self.conflict_button)

        self.preview_on_hover = True
        self.last_conflict_check_time = 0
        self.disabled_mods_table.itemDoubleClicked.connect(self.handle_double_click)
        self.enabled_mods_table.itemDoubleClicked.connect(self.handle_double_click)
        self.disabled_mods_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.disabled_mods_table.customContextMenuRequested.connect(self.show_context_menu)
        self.enabled_mods_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.enabled_mods_table.customContextMenuRequested.connect(self.show_context_menu)

        self.operations.create_search_button(self.left_layout, self.disabled_mods_table, {}, QtCore.Qt.AlignLeft)
        self.operations.create_search_button(self.right_layout, self.enabled_mods_table, {}, QtCore.Qt.AlignLeft)

        self.disabled_mods_table.viewport().installEventFilter(self)
        self.enabled_mods_table.viewport().installEventFilter(self)

        self.disabled_mods_table.setMinimumWidth(int(self.width() / 1))
        self.enabled_mods_table.setMinimumWidth(int(self.width() / 1))

        self.disabled_mods_table.horizontalHeader().sectionResized.connect(self.operations.save_column_width)
        self.enabled_mods_table.horizontalHeader().sectionResized.connect(self.operations.save_column_width)

        self.operations.load_column_width()

    def show_context_menu(self, position):
        self.operations.show_context_menu(position)

    def handle_double_click(self, item):
        self.operations.handle_double_click(item)

    def apply_stylesheet(self):
        self.operations.apply_stylesheet()
