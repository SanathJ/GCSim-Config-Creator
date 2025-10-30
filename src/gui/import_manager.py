import json
import os
import sqlite3
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Literal

import loader
import maker

from .character_manager import refresh_character_manager_tree

id = None


def timed_info_label(
    sidebar_frame: ttk.Frame,
    info_label: ttk.Label,
    message: str,
    type: Literal["success", "warning"],
    delay: int = 5000,
):
    info_label.configure(wraplength=sidebar_frame.winfo_width() - 20)
    if type == "success":
        info_label.configure(foreground="green")
    else:
        info_label.configure(foreground="red")
    info_label.configure(text=message)
    global id
    if id:
        info_label.after_cancel(id)
    id = info_label.after(delay, lambda: info_label.configure(text=""))


def refresh_character_list(tree: ttk.Treeview):
    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()
        cursor.execute(
            """
            SELECT Characters.name, constellation, Characters.level, talent, Weapons.name, Weapons.refinement
            FROM Characters
            JOIN Weapons
            ON Characters.weapon = Weapons.id
            ORDER BY Characters.name ASC
            """
        )
        characters = cursor.fetchall()

        for item in tree.get_children(""):
            tree.delete(item)

        for character in characters:
            tree.insert("", "end", text=character[0], values=character[1:])


def refresh_new_config(new_config: ScrolledText, tree: ttk.Treeview):
    new_config.configure(state="normal")
    new_config.delete("1.0", "end")
    if tree.selection():
        new_config.insert(
            "1.0", maker.makeCharConfig((tree.item(tree.selection())["text"]))["config"]
        )
    new_config.configure(state="disabled")


def refresh_old_config(config_name: StringVar, mode: str, old_config: ScrolledText):
    if mode == "not":
        return

    old_config.configure(state="normal")
    old_config.delete("1.0", "end")

    if config_name.get():
        with sqlite3.connect("configs.db") as con:
            cursor = con.cursor()
            cursor.execute(
                """
                SELECT config
                FROM Character_Configs
                WHERE config_name = ?
                """,
                (config_name.get(),),
            )
            characters = cursor.fetchone()

            if characters:
                old_config.insert("1.0", characters[0])
    old_config.configure(state="disabled")


def get_character_config_list() -> list[str]:
    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()
        cursor.execute(
            """ 
            SELECT config_name
            FROM Character_Configs
            """
        )
        configs = [""] + [x for (x,) in cursor.fetchall()]
        return configs


def get_clipboard(
    root: Tk, sidebar_frame: ttk.Frame, info_label: ttk.Label
) -> str | None:
    try:
        # Access clipboard content
        clipboard_content = root.clipboard_get()
        return clipboard_content
    except TclError:
        timed_info_label(
            sidebar_frame,
            info_label,
            "Clipboard is empty or can't be accessed.",
            "warning",
        )


def load_button_handler(
    root: Tk,
    from_json: bool,
    tree: ttk.Treeview,
    new_config: ScrolledText,
    sidebar_frame: ttk.Frame,
    info_label: ttk.Label,
):
    db = {}
    if from_json:
        jsonfile = filedialog.askopenfilename(
            title="JSON file",
            filetypes=[("GOOD JSON File", ["*.json"])],
        )
        if not os.path.isfile(jsonfile):
            timed_info_label(
                sidebar_frame, info_label, "This file does not exist.", "warning"
            )
            return

        with open(jsonfile, "r") as f:
            try:
                db = json.load(f)
            except:
                timed_info_label(
                    sidebar_frame,
                    info_label,
                    "Error loading JSON from file.",
                    "warning",
                )
                return
    else:
        try:
            db = json.loads(get_clipboard(root, sidebar_frame, info_label))
        except:
            timed_info_label(
                sidebar_frame,
                info_label,
                "Error loading JSON from clipboard.",
                "warning",
            )
            return

    if not db:
        timed_info_label(sidebar_frame, info_label, "Failed to load.", "warning")
        return

    if db.get("format") != "GOOD":
        timed_info_label(
            sidebar_frame, info_label, "Incorrect database format.", "warning"
        )
        return

    try:
        loader.load(db)
    except KeyError as e:
        timed_info_label(
            sidebar_frame,
            info_label,
            f"Error importing character data: missing key {e}. Incomplete exports from scanners may result in unexpected errors. Use a complete GOOD export or import from Genshin Optimizer.",
            "warning",
            10000,
        )
        return
    loader.export()
    refresh_character_list(tree)
    refresh_new_config(new_config, tree)

    timed_info_label(
        sidebar_frame, info_label, "Character(s) imported successfully.", "success"
    )


def save_character_config(
    cb_entry: StringVar,
    tree: ttk.Treeview,
    old_config: ScrolledText,
    sidebar_frame: ttk.Frame,
    info_label: ttk.Label,
):
    if not cb_entry.get() or not tree.selection():
        return

    # warning messagebox for existing name
    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()

        # warning messagebox for existing name
        cursor.execute(
            """
            SELECT 1
            FROM Character_Configs
            WHERE config_name = ?
            """,
            (cb_entry.get(),),
        )
        if cursor.fetchone():
            res = messagebox.askokcancel(
                "Overwrite Config",
                f"A config with the name {cb_entry.get()} already exists. Saving will overwrite the existing config. Proceed?",
            )
            if not res:
                return

    maker.saveConfig((tree.item(tree.selection())["text"]), cb_entry.get())
    refresh_old_config(cb_entry, "write", old_config)
    refresh_character_manager_tree()

    timed_info_label(
        sidebar_frame, info_label, f"{cb_entry.get()} saved successfully.", "success"
    )


def setup_import_manager_frame(root: Tk, notebook: ttk.Notebook) -> ttk.Frame:
    import_manager_frame = ttk.Frame(notebook)
    import_manager_frame.grid(column=0, row=0, sticky=(N, S, E, W))
    import_manager_frame.grid_rowconfigure(0, weight=1)

    main_import_manager_frame = ttk.Frame(import_manager_frame)
    main_import_manager_frame.grid(column=0, row=0, sticky=(N, S, W), padx=10, pady=10)
    main_import_manager_frame.grid_rowconfigure(0, weight=1)

    # button sidebar
    sidebar_frame = ttk.Frame(import_manager_frame)
    sidebar_frame.grid(column=1, row=0, sticky=(N, S), pady=10)

    info_label = ttk.Label(
        sidebar_frame,
        text="",
        font=("TkDefaultFont", 16),
    )
    info_label.grid(column=0, row=3, columnspan=4, sticky=(N, S, E, W))

    # main
    tree = ttk.Treeview(
        main_import_manager_frame,
        columns=(
            "constellation",
            "level",
            "talent",
            "weapon",
            "refine",
            "config",
        ),
        displaycolumns=[x for x in range(0, 5)],
    )

    headings = [
        "#0",
        "constellation",
        "level",
        "talent",
        "weapon",
        "refine",
        "config",
    ]

    column_widths = [200, 80, 50, 65, 300, 50, 200]
    for x, width in zip(headings, column_widths):
        tree.column(x, anchor="center", width=width)
        tree.heading(x, text="Character" if x == "#0" else x.title())
    tree.grid(column=0, row=0, sticky=(N, S, E, W))

    tree_s = ttk.Scrollbar(
        main_import_manager_frame, orient=VERTICAL, command=tree.yview
    )
    tree.configure(yscrollcommand=tree_s.set, selectmode="browse", height=15)
    tree_s.grid(column=1, row=0, sticky=(N, S))
    tree.bind("<<TreeviewSelect>>", lambda e: refresh_new_config(new_config, tree))

    pane = ttk.PanedWindow(main_import_manager_frame)
    style = ttk.Style()
    style.configure("Custom.TPanedwindow", sashrelief="flat", sashthickness=1)
    pane.configure(style="Custom.TPanedwindow")

    old_config_frame = ttk.Label(pane)
    new_config_frame = ttk.Label(pane)

    ttk.Label(old_config_frame, text="Old Config").grid(column=0, row=0)
    old_config = ScrolledText(old_config_frame, height=10)
    old_config.configure(state="disabled")
    old_config.grid(column=0, row=1, sticky=(S, E, W))
    old_config_frame.grid_columnconfigure(0, weight=1)

    ttk.Label(new_config_frame, text="New Config").grid(column=0, row=0)
    new_config = ScrolledText(new_config_frame, height=10)
    new_config.configure(state="disabled")
    new_config.grid(column=0, row=1, sticky=(S, E, W))
    new_config_frame.grid_columnconfigure(0, weight=1)

    pane.add(old_config_frame)
    pane.add(new_config_frame)
    pane.grid(row=1, columnspan=2, sticky=(S, E, W))

    # buttons

    cb_entry = StringVar()
    cb_entry.trace_add(
        "write", lambda a, b, c: refresh_old_config(cb_entry, c, old_config)
    )

    cb = ttk.Combobox(
        sidebar_frame,
        width=35,
        height=10,
        textvariable=cb_entry,
        values=get_character_config_list(),
        postcommand=lambda: cb.configure(values=get_character_config_list()),
    )
    cb.grid(column=0, row=1, columnspan=3, sticky=(E, W))
    cb.bind(
        "<<ComboboxSelected>>",
        lambda e: refresh_old_config(cb_entry, "not", old_config),
    )

    ttk.Button(
        sidebar_frame,
        text="Save Character",
        command=lambda: save_character_config(
            cb_entry, tree, old_config, sidebar_frame, info_label
        ),
    ).grid(column=3, row=1, sticky=(E, W))

    ttk.Button(
        sidebar_frame,
        text="Load from GOOD JSON file",
        command=lambda: load_button_handler(
            root, True, tree, new_config, sidebar_frame, info_label
        ),
    ).grid(column=0, row=0, columnspan=2, sticky=(E, W))
    ttk.Button(
        sidebar_frame,
        text="Load from clipboard",
        command=lambda: load_button_handler(
            root, False, tree, new_config, sidebar_frame, info_label
        ),
    ).grid(column=2, row=0, columnspan=2, sticky=(E, W))

    ttk.Separator(sidebar_frame, orient=HORIZONTAL).grid(
        column=0, row=2, columnspan=4, sticky=(E, W), pady=5
    )

    return import_manager_frame
