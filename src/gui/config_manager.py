from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from .import_manager import get_character_config_list
from .rotation_manager import get_rotation_config_list

import sqlite3


def refresh_preview(
    characters: list[ttk.Combobox], rotation: ttk.Combobox, preview: ScrolledText
):
    full_config = ""
    characters = [x.get() for x in characters if x.get()]

    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()
        cursor.execute(
            f""" 
            SELECT config
            FROM Character_Configs
            WHERE config_name IN({','.join(['?'] * len(characters))})
            """,
            tuple(characters),
        )
        full_config += "\n".join([x for (x,) in cursor.fetchall()])

        cursor.execute(
            f""" 
            SELECT config
            FROM Rotation_Configs
            WHERE config_name = ?
            """,
            (rotation.get(),),
        )
        row = cursor.fetchone()
        if row:
            full_config += "\n" + row[0]

    preview.configure(state="normal")
    preview.delete("1.0", "end"),
    preview.insert("1.0", full_config)
    preview.configure(state="disabled")


def save_full_config(
    characters: list[ttk.Combobox], rotation: ttk.Combobox, save_name: StringVar
):
    if not save_name.get():
        return
    characters = [x.get() if x.get() else None for x in characters]
    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO Full_Configs (config_name, rotation, character1, character2, character3, character4)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (save_name.get(), rotation.get() if rotation.get() else None, *characters),
        )


def get_full_config_list():
    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()
        cursor.execute(
            """ 
            SELECT config_name
            FROM Full_Configs
            """
        )
        configs = [x for (x,) in cursor.fetchall()]
    return configs


def delete_full_config(listbox: ttk.Combobox, save_name: StringVar):
    if not listbox.get():
        return

    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()
        cursor.execute(
            """ 
            DELETE FROM Full_Configs
            WHERE config_name = ?
            """,
            (listbox.get(),),
        )

    listbox.set("")
    save_name.set("")


def load_full_config(
    listbox: ttk.Combobox,
    characters: list[ttk.Combobox],
    rotation: ttk.Combobox,
    save_name: StringVar,
    preview: ScrolledText,
):
    if not listbox.get():
        return

    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()

        cursor.execute(
            """
            SELECT character1, character2, character3, character4, rotation
            FROM Full_Configs
            WHERE Full_Configs.config_name = ?
            """,
            (listbox.get(),),
        )

        row = cursor.fetchone()
        if not row:
            return
        for cb, v in zip([*characters, rotation], row):
            if v:
                cb.set(v)
            else:
                cb.set("")

        refresh_preview(characters, rotation, preview)
        save_name.set(listbox.get())


def setup_config_manager_frame(root, notebook):
    config_manager_frame = ttk.Frame(notebook)
    config_manager_frame.grid(column=0, row=0, sticky=(N, S, E, W))
    config_manager_frame.grid_columnconfigure(0, weight=1)
    config_manager_frame.grid_rowconfigure(1, weight=1)

    main_rotation_manager_frame = ttk.Frame(config_manager_frame)
    main_rotation_manager_frame.grid(column=0, row=1, sticky=(N, S, E, W))

    # options bar
    options_frame = ttk.Frame(config_manager_frame)
    options_frame.grid(column=0, row=0, sticky=(E, W))
    options_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="column")

    # button sidebar
    sidebar_frame = ttk.Frame(config_manager_frame)
    sidebar_frame.grid(column=1, row=0, rowspan=2)

    # main
    char_array = []
    for i in range(4):
        ttk.Label(options_frame, text=f"Character {i + 1}").grid(
            column=i, row=0, padx=10
        )
        cb = ttk.Combobox(
            options_frame,
            state="readonly",
            postcommand=lambda: [
                x.configure(values=get_character_config_list()) for x in char_array
            ],
        )
        char_array.append(cb)
        cb.grid(column=i, row=1, padx=10)
        cb.bind(
            "<<ComboboxSelected>>",
            lambda e: refresh_preview(char_array, rotation, preview),
        )

    ttk.Label(options_frame, text=f"Rotation").grid(column=4, row=0, padx=10)
    rotation = ttk.Combobox(
        options_frame,
        state="readonly",
        postcommand=lambda: rotation.configure(values=get_rotation_config_list()),
    )
    rotation.grid(column=4, row=1, padx=10)
    rotation.bind(
        "<<ComboboxSelected>>",
        lambda e: refresh_preview(char_array, rotation, preview),
    )

    preview = ScrolledText(main_rotation_manager_frame)
    preview.configure(state="disabled")
    preview.grid(column=0, row=0, sticky=(N, S, E, W), padx=10, pady=10)

    main_rotation_manager_frame.grid_columnconfigure(0, weight=1)
    main_rotation_manager_frame.grid_rowconfigure(0, weight=1)

    listbox = ttk.Combobox(
        sidebar_frame,
        width=40,
        height=10,
        values=get_full_config_list(),
        state="readonly",
        postcommand=lambda: listbox.configure(values=get_full_config_list()),
    )
    listbox.grid(column=0, row=0, columnspan=3, sticky=(E, W))

    save_name = StringVar()
    ttk.Entry(sidebar_frame, textvariable=save_name).grid(
        column=0, row=1, columnspan=3, sticky=(E, W)
    )

    ttk.Button(
        sidebar_frame,
        text="Load Config",
        command=lambda: load_full_config(
            listbox, char_array, rotation, save_name, preview
        ),
    ).grid(column=3, row=0, sticky=(E, W))

    ttk.Button(
        sidebar_frame,
        text="Delete Config",
        command=lambda: delete_full_config(listbox, save_name),
    ).grid(column=4, row=0, sticky=(E, W))

    ttk.Button(
        sidebar_frame,
        text="Save Full Config",
        command=lambda: save_full_config(char_array, rotation, save_name),
    ).grid(column=3, row=1, columnspan=2, sticky=(E, W))

    return config_manager_frame
