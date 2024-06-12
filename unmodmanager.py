import os
import json
import tkinter as tk
import threading
import time
import configparser
import concurrent.futures
from pathlib import Path
from typing import List, Dict
from collections import defaultdict
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk

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

    def save_profile(self, profile_name: str) -> None:
        config = configparser.ConfigParser()
        self.profiles[profile_name] = {"enabled_mods": self.dlc_data["enabled_mods"]}
        for profile in self.profiles:
            config[profile] = self.profiles[profile]
        with open(self.profiles_path, 'w') as file:
            config.write(file)

    def delete_profile(self, profile_name: str) -> None:
        if profile_name in self.profiles:
            del self.profiles[profile_name]
            config = configparser.ConfigParser()
            for profile in self.profiles:
                config[profile] = self.profiles[profile]
            with open(self.profiles_path, 'w') as file:
                config.write(file)

    def load_profile(self, profile_name: str) -> None:
        profile = self.profiles.get(profile_name, {})
        if profile:
            self.dlc_data["enabled_mods"] = profile["enabled_mods"]
            self.save_dlc_load()
            self.sync_enabled_mods()

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

class ModManagerUI:
    def __init__(self, root, manager):
        self.manager = manager
        self.root = root
        self.root.title("CK3 UnMod Manager")

        self.apply_dark_theme(root)

        self.image_window = None
        self.hovered_item = None
        self.preview_on_hover = tk.BooleanVar(value=True)

        self.profile_frame = tk.Frame(root, bg='#2e2e2e')
        self.profile_frame.pack(fill=tk.X, pady=5)

        self.save_profile_button = tk.Button(self.profile_frame, text="Save Profile", command=self.save_profile, bg='#444444', fg='#ffffff')
        self.save_profile_button.pack(side=tk.LEFT, padx=5)

        self.save_profile_var = tk.StringVar()
        self.save_profile_entry = tk.Entry(self.profile_frame, textvariable=self.save_profile_var, bg='#2e2e2e', fg='#ffffff')
        self.save_profile_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.delete_profile_button = tk.Button(self.profile_frame, text="Delete Profile", command=self.delete_profile, bg='#444444', fg='#ffffff')
        self.delete_profile_button.pack(side=tk.RIGHT, padx=5)

        self.load_profile_button = tk.Button(self.profile_frame, text="Load Profile", command=self.load_profile, bg='#444444', fg='#ffffff')
        self.load_profile_button.pack(side=tk.LEFT, padx=5)

        self.load_profile_var = tk.StringVar()
        self.load_profile_menu = ttk.Combobox(self.profile_frame, textvariable=self.load_profile_var, values=list(manager.profiles.keys()), state='readonly')
        self.load_profile_menu.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.left_frame = tk.Frame(root, bg='#2e2e2e')
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_frame = tk.Frame(root, bg='#2e2e2e')
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.disabled_mods_table = ttk.Treeview(self.left_frame, columns=("name", "version", "comment", "path"), show='headings')
        self.style_table(self.disabled_mods_table)
        self.disabled_mods_table.pack(fill=tk.BOTH, expand=True)

        self.enabled_mods_table = ttk.Treeview(self.right_frame, columns=("name", "version", "comment", "path"), show='headings')
        self.style_table(self.enabled_mods_table)
        self.enabled_mods_table.pack(fill=tk.BOTH, expand=True)

        self.enabled_mods_table.bind("<Double-1>", self.edit_comment)
        self.disabled_mods_table.bind("<Double-1>", self.edit_comment)
        
        self.enabled_mods_table.bind("<Button-3>", self.show_context_menu)
        self.disabled_mods_table.bind("<Button-3>", self.show_context_menu)

        self.enabled_mods_table.bind("<Motion>", self.on_hover) 
        self.disabled_mods_table.bind("<Motion>", self.on_hover)

        self.progress_var = tk.DoubleVar()

        self.enable_button = tk.Button(self.left_frame, text="Enable Mod", command=self.enable_mod, bg='#444444', fg='#ffffff')
        self.enable_button.pack(pady=5)

        self.move_buttons_frame = tk.Frame(self.right_frame, bg='#2e2e2e')
        self.move_buttons_frame.pack(fill=tk.X, pady=5)

        self.up_button = tk.Button(self.move_buttons_frame, text="Move Up", command=self.move_up, bg='#444444', fg='#ffffff')
        self.up_button.pack(side=tk.LEFT, padx=5)

        self.down_button = tk.Button(self.move_buttons_frame, text="Move Down", command=self.move_down, bg='#444444', fg='#ffffff')
        self.down_button.pack(side=tk.LEFT, padx=5)

        self.disable_button = tk.Button(self.move_buttons_frame, text="Disable Mod", command=self.disable_mod, bg='#444444', fg='#ffffff')
        self.disable_button.pack(side=tk.LEFT, padx=5)

        self.conflict_button = tk.Button(self.move_buttons_frame, text="Find Conflicts", command=self.find_conflicts, bg='#444444', fg='#ffffff')
        self.conflict_button.pack(side=tk.LEFT, padx=5)

        self.toggle_preview_button = tk.Button(self.move_buttons_frame, text="Toggle Preview", command=self.toggle_preview, bg='#444444', fg='#ffffff')
        self.toggle_preview_button.pack(side=tk.LEFT, padx=5)
        
        self.last_conflict_check_time = 0
        self.load_mods()
    
    def show_context_menu(self, event):
        widget = event.widget
        selection = widget.selection()
        if not selection:
            return
        item = widget.identify_row(event.y)
        if not item:
            return
        widget.selection_set(item)
        
        context_menu = tk.Menu(self.root, tearoff=0, bg='#2e2e2e', fg='#ffffff')
        context_menu.add_command(label="Open folder in File Explorer", command=lambda: self.open_folder(widget, item))
        context_menu.add_command(label="Open Steam page", command=lambda: self.open_steam_page(widget, item))
        context_menu.add_command(label="Find Skymods page", command=lambda: self.open_smods_page(widget, item))
        context_menu.add_command(label="View Image", command=lambda: self.view_image(widget, item, event))
        context_menu.post(event.x_root, event.y_root)

    def view_image(self, widget, item, event):
        mod_path = widget.item(item, "values")[3]
        mod_folder = os.path.join(self.manager.mods_directory, mod_path.split('.')[0])
        image_path = os.path.join(mod_folder, 'thumbnail.png')
        if os.path.isfile(image_path):
            self.show_image_window(image_path, event)

    def toggle_preview(self):
        self.preview_on_hover.set(not self.preview_on_hover.get())

    def on_hover(self, event):
        if self.preview_on_hover.get():
            return

        widget = event.widget
        row_id = widget.identify_row(event.y)
        
        if row_id != self.hovered_item:
            self.hovered_item = row_id
            if row_id:
                mod_path = widget.item(row_id, "values")[3]
                mod_folder = os.path.join(self.manager.mods_directory, mod_path.split('.')[0])
                image_path = os.path.join(mod_folder, 'thumbnail.png')
                if os.path.isfile(image_path):
                    self.show_image_window(image_path, event)
                else:
                    if self.image_window:
                        self.image_window.destroy()
                        self.image_window = None
            else:
                if self.image_window:
                    self.image_window.destroy()
                    self.image_window = None

    def show_image_window(self, image_path, event):
        if self.image_window:
            self.image_window.destroy()

        self.image_window = tk.Toplevel(self.root)
        self.image_window.title("Mod Image")
        self.image_window.configure(bg='#2e2e2e')
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        initial_width = int(screen_width * 0.25)
        initial_height = int(screen_height * 0.25)

        x_position = event.x_root + 250
        if x_position + initial_width > screen_width:
            x_position = event.x_root - initial_width - 250
        y_position = event.y_root
        if y_position + initial_height > screen_height:
            y_position = event.y_root - initial_height

        self.image_window.geometry(f"{initial_width}x{initial_height}+{x_position}+{y_position}")
        self.image_window.minsize(200, 200)

        img = self.load_resized_image(image_path, initial_width, initial_height)
        img_label = tk.Label(self.image_window, image=img, bg='#2e2e2e')
        img_label.image = img
        img_label.pack(fill=tk.BOTH, expand=True)

        self.image_window.bind('<Configure>', lambda e: self.resize_image(img_label, image_path, e.width, e.height))

    def load_resized_image(self, image_path, width, height):
        image = Image.open(image_path)
        image.thumbnail((width, height))
        return ImageTk.PhotoImage(image)

    def resize_image(self, img_label, image_path, width, height):
        img = self.load_resized_image(image_path, width, height)
        img_label.configure(image=img)
        img_label.image = img

    def open_folder(self, widget, item):
        mod_path = widget.item(item, "values")[3]
        folder_path = os.path.join(self.manager.mods_directory, mod_path.split('.')[0])
        if os.path.isdir(folder_path):
            os.startfile(folder_path)

    def open_steam_page(self, widget, item):
        mod_path = widget.item(item, "values")[3]
        mod_id = mod_path.split('.')[0]
        steam_url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"
        os.system(f'start {steam_url}')
        
    def open_smods_page(self, widget, item):
        mod_path = widget.item(item, "values")[3]
        mod_id = mod_path.split('.')[0]
        smods_url = f"https://catalogue.smods.ru/?s={mod_id}&app=1158310"
        os.system(f'start {smods_url}')

    def save_profile(self):
        profile_name = self.save_profile_var.get()
        if not profile_name:
            profile_name = f"Profile {len(self.manager.profiles) + 1}"
        self.manager.save_profile(profile_name)
        self.load_profile_menu['values'] = list(self.manager.profiles.keys())

    def delete_profile(self):
        profile_name = self.load_profile_var.get()
        if profile_name:
            self.manager.delete_profile(profile_name)
            self.load_profile_menu['values'] = list(self.manager.profiles.keys())

    def load_profile(self):
        profile_name = self.load_profile_var.get()
        self.manager.load_profile(profile_name)
        self.load_mods()

    def apply_dark_theme(self, root):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#2e2e2e",
                        foreground="white",
                        rowheight=25,
                        fieldbackground="#2e2e2e")
        style.map('Treeview', background=[('selected', '#4e4e4e')])

        root.configure(bg='#2e2e2e')
        root.option_add("*TCombobox*Listbox*Background", '#2e2e2e')
        root.option_add("*TCombobox*Listbox*Foreground", 'white')

    def style_table(self, table):
        table.heading("name", text="Name")
        table.heading("version", text="Version")
        table.heading("comment", text="Comment")
        table.heading("path", text="Path")
        table.tag_configure('oddrow', background='#2e2e2e')
        table.tag_configure('evenrow', background='#383838')

    def create_table(self, table, mods):
        for i, mod in enumerate(mods):
            if i % 2 == 0:
                tags = ('evenrow',)
            else:
                tags = ('oddrow',)
            table.insert("", tk.END, values=(mod['name'], mod['version'], mod['comment'], mod['path']), tags=tags)

    def update_comment(self, event):
        selected_table = event.widget
        item = selected_table.focus()
        if not item:
            return
        values = selected_table.item(item, "values")
        if len(values) < 4:
            return
        mod_path = values[3]
        comment = values[2]
        self.manager.comments[mod_path] = comment
        self.manager.save_comments()

    def edit_comment(self, event):
        selected_item = event.widget.focus()
        column = event.widget.identify_column(event.x)
        if column != '#3':
            return
        
        item_bbox = event.widget.bbox(selected_item, column)
        if not item_bbox:
            return

        current_comment = event.widget.item(selected_item, "values")[2]

        entry_popup = tk.Entry(event.widget)
        entry_popup.place(x=item_bbox[0], y=item_bbox[1], width=item_bbox[2], height=item_bbox[3])
        entry_popup.insert(0, current_comment)

        def save_comment(event, entry_popup=entry_popup, treeview=event.widget, selected_item=selected_item, column=column):
            comment = entry_popup.get()
            values = treeview.item(selected_item, "values")
            if len(values) < 4:
                entry_popup.destroy()
                return
            mod_path = values[3]
            self.manager.comments[mod_path] = comment
            self.manager.save_comments()
            treeview.set(selected_item, column, comment)
            entry_popup.destroy()

        entry_popup.bind('<Return>', save_comment)
        entry_popup.bind('<FocusOut>', lambda e: save_comment(e))
        entry_popup.focus()

    def load_mods(self):
        self.conflict_button.config(command=self.find_conflicts)

        self.disabled_mods_table.delete(*self.disabled_mods_table.get_children())
        self.enabled_mods_table.delete(*self.enabled_mods_table.get_children())

        mods = self.manager.list_mods()
        enabled_mods = [mod for mod in mods if mod.get('enabled')]
        disabled_mods = [mod for mod in mods if not mod.get('enabled')]

        self.create_table(self.disabled_mods_table, disabled_mods)
        self.create_table(self.enabled_mods_table, enabled_mods)
        self.update_enabled_mods_order()

        self.enabled_mods_table.bind('<FocusOut>', self.update_comment)
        self.disabled_mods_table.bind('<FocusOut>', self.update_comment)

    def enable_mod(self):
        selected_items = self.disabled_mods_table.selection()
        for item in selected_items:
            mod_name = self.disabled_mods_table.item(item, "values")[0]
            self.manager.enable_mod(mod_name)
        self.load_mods()

    def disable_mod(self):
        selected_items = self.enabled_mods_table.selection()
        for item in selected_items:
            mod_name = self.enabled_mods_table.item(item, "values")[0]
            self.manager.disable_mod(mod_name)
        self.load_mods()

    def find_conflicts(self):
        current_time = time.time()
        if current_time - self.last_conflict_check_time < 3:
            return
        self.last_conflict_check_time = current_time

        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Finding Conflicts")
        self.progress_window.geometry("300x100")
        tk.Label(self.progress_window, text="Finding Conflicts, Please Wait...").pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(self.progress_window, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        threading.Thread(target=self.find_conflicts_thread).start()

    def find_conflicts_thread(self):
        self.progress_var.set(0)
        num_mods = len(self.manager.mods)
        
        def update_progress(future, processed_mods):
            self.progress_var.set((processed_mods / num_mods) * 100)
            self.root.update_idletasks()

        file_paths = defaultdict(list)
        mod_localizations = defaultdict(list)
        processed_mods = 0
        
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
                self.root.after(0, update_progress, future, processed_mods)
                if mod_file_paths:
                    for key, value in mod_file_paths.items():
                        file_paths[key].extend(value)
                    for key, value in mod_localizations.items():
                        mod_localizations[key].extend(value)

        red_conflicts = {}
        yellow_conflicts = {}
        missing_russian = []

        for path, mods in file_paths.items():
            if os.path.basename(path) in ["descriptor.mod", "thumbnail.png", "thumbnail.ico", "Steam desc.txt"]:
                # yellow_conflicts[path] = mods
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

        self.progress_window.destroy()
        self.root.after(0, self.display_conflicts, red_conflicts, yellow_conflicts, missing_russian)

    def display_conflicts(self, red_conflicts, yellow_conflicts, missing_russian):
        def remove_conflict(path, mods, conflict_type):
            if conflict_type == "red":
                del red_conflicts[path]
            elif conflict_type == "yellow":
                del yellow_conflicts[path]
            update_text_area()

        def open_file_explorer(mod_ids, mod_path):
            for mod_id in mod_ids:
                mod_folder = os.path.join(self.manager.mods_directory, mod_id)
                file_path = os.path.join(mod_folder, mod_path)
                folder_path = os.path.dirname(file_path)
                if os.path.isdir(folder_path):
                    os.system(f'explorer /select,"{file_path}"')

        def update_text_area():
            text_area.configure(state='normal')
            text_area.delete('1.0', tk.END)

            if red_conflicts:
                text_area.insert(tk.END, "Red Conflicts:\n")
                for path, mods in red_conflicts.items():
                    btn = tk.Button(conflict_window, text="[-]", command=lambda p=path, m=mods: remove_conflict(p, m, "red"), bg='#444444', fg='#ffffff')
                    text_area.window_create(tk.END, window=btn)
                    text_area.insert(tk.END, f" [{len(mods)}] rewrite: ")
                    for mod in mods:
                        mod_btn = tk.Button(conflict_window, text=mod, command=lambda m=mod, p=path: open_file_explorer([m], p), bg='#444444', fg='#ffffff')
                        text_area.window_create(tk.END, window=mod_btn)
                        text_area.insert(tk.END, " ")
                    text_area.insert(tk.END, "[file]: ")
                    path_btn = tk.Button(conflict_window, text=path, command=lambda m=mods, p=path: open_file_explorer(m, p), bg='#444444', fg='#ffffff')
                    text_area.window_create(tk.END, window=path_btn)
                    text_area.insert(tk.END, "\n")
                text_area.insert(tk.END, "\n")

            if yellow_conflicts:
                text_area.insert(tk.END, "Yellow Conflicts:\n")
                for path, mods in yellow_conflicts.items():
                    btn = tk.Button(conflict_window, text="[-]", command=lambda p=path, m=mods: remove_conflict(p, m, "yellow"), bg='#444444', fg='#ffffff')
                    text_area.window_create(tk.END, window=btn)
                    text_area.insert(tk.END, f" [{len(mods)}] rewrite: ")
                    for mod in mods:
                        mod_btn = tk.Button(conflict_window, text=mod, command=lambda m=mod, p=path: open_file_explorer([m], p), bg='#444444', fg='#ffffff')
                        text_area.window_create(tk.END, window=mod_btn)
                        text_area.insert(tk.END, " ")
                    text_area.insert(tk.END, "[file]: ")
                    path_btn = tk.Button(conflict_window, text=path, command=lambda m=mods, p=path: open_file_explorer(m, p), bg='#444444', fg='#ffffff')
                    text_area.window_create(tk.END, window=path_btn)
                    text_area.insert(tk.END, "\n")
                text_area.insert(tk.END, "\n")

            if missing_russian:
                text_area.insert(tk.END, "Missing Russian Localization:\n")
                for mod in missing_russian:
                    text_area.insert(tk.END, f"Mod: {mod}\n")
                text_area.insert(tk.END, "\n")

            text_area.configure(state='disabled')

        conflict_window = tk.Toplevel(self.root)
        conflict_window.title("Mod Conflicts")

        conflict_window.rowconfigure(0, weight=1)
        conflict_window.columnconfigure(0, weight=1)

        text_area = scrolledtext.ScrolledText(conflict_window, wrap=tk.WORD, width=150, height=40, bg='#2e2e2e', fg='#ffffff', insertbackground='white')
        text_area.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        update_text_area()


    def move_up(self):
        selected = self.enabled_mods_table.selection()
        if not selected:
            return

        for item in selected:
            index = self.enabled_mods_table.index(item)
            if index == 0:
                continue
            mod = self.enabled_mods_table.item(item, "values")
            self.enabled_mods_table.delete(item)
            new_item = self.enabled_mods_table.insert('', index - 1, values=mod)
            self.enabled_mods_table.selection_add(new_item)

        self.update_enabled_mods_order()

    def move_down(self):
        selected = self.enabled_mods_table.selection()
        if not selected:
            return

        for item in reversed(selected):
            index = self.enabled_mods_table.index(item)
            if index == self.enabled_mods_table.get_children().__len__() - 1:
                continue
            mod = self.enabled_mods_table.item(item, "values")
            self.enabled_mods_table.delete(item)
            new_item = self.enabled_mods_table.insert('', index + 1, values=mod)
            self.enabled_mods_table.selection_add(new_item)

        self.update_enabled_mods_order()

    def update_enabled_mods_order(self):
        new_order = self.enabled_mods_table.get_children()
        mod_paths = []
        for item in new_order:
            mod_name = self.enabled_mods_table.item(item, "values")[0]
            for mod in self.manager.mods:
                if mod.get('name') == mod_name:
                    mod_file_path = f"mod/{mod['path']}"
                    mod_paths.append(mod_file_path)
                    break
        self.manager.dlc_data["enabled_mods"] = mod_paths
        self.manager.save_dlc_load()

if __name__ == "__main__":
    user_name = os.getlogin()
    mods_directory = f"C:\\Users\\{user_name}\\Documents\\Paradox Interactive\\Crusader Kings III\\mod"
    dlc_load_path = f"C:\\Users\\{user_name}\\Documents\\Paradox Interactive\\Crusader Kings III\\dlc_load.json"
    profiles_path = f"C:\\Users\\{user_name}\\Documents\\Paradox Interactive\\Crusader Kings III\\profiles.ini"
    manager = ModManager(mods_directory, dlc_load_path, profiles_path)
    root = tk.Tk()
    app = ModManagerUI(root, manager)
    root.mainloop()
