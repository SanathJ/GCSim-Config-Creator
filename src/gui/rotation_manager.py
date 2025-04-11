from tkinter import *
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

import sqlite3


def get_rotation_config_list():
    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()
        cursor.execute(
            """ 
            SELECT config_name
            FROM Rotation_Configs
            """
        )
        configs = [x for (x,) in cursor.fetchall()]
    return configs


def load_rotation_config(
    listbox: ttk.Combobox, display_config: ScrolledText, save_name: StringVar
):
    if not listbox.get():
        return
    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()
        cursor.execute(
            """ 
            SELECT config
            FROM Rotation_Configs
            WHERE config_name = ?
            """,
            (listbox.get(),),
        )
        (config,) = cursor.fetchone()

    display_config.delete("1.0", "end")
    display_config.insert("1.0", config)
    save_name.set(listbox.get())


def delete_rotation_config(listbox: ttk.Combobox, save_name: StringVar):
    if not listbox.get():
        return

    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()
        cursor.execute(
            """ 
            DELETE FROM Rotation_Configs
            WHERE config_name = ?
            """,
            (listbox.get(),),
        )

    listbox.set("")
    save_name.set("")


def save_rotation_config(display_config: ScrolledText, save_name: StringVar):
    if not save_name.get():
        return

    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()
        cursor.execute(
            """ 
            INSERT OR REPLACE INTO Rotation_Configs (config_name, config)
            VALUES (?, ?)
            """,
            (save_name.get(), display_config.get("1.0", "end")),
        )


def setup_rotation_manager_frame(root, notebook):
    rotation_manager_frame = ttk.Frame(notebook)
    rotation_manager_frame.grid(column=0, row=0, sticky=(N, S, E, W))

    main_rotation_manager_frame = ttk.Frame(rotation_manager_frame)
    main_rotation_manager_frame.grid(column=0, row=0)

    # button sidebar
    sidebar_frame = ttk.Frame(rotation_manager_frame)
    sidebar_frame.grid(column=1, row=0)

    # main

    display_config = ScrolledText(main_rotation_manager_frame)
    display_config.configure(undo=True)
    display_config.grid(column=0, row=0, sticky=(N, E, W, S))

    listbox = ttk.Combobox(
        sidebar_frame,
        width=40,
        height=10,
        values=get_rotation_config_list(),
        state="readonly",
        postcommand=lambda: listbox.configure(values=get_rotation_config_list()),
    )
    listbox.grid(column=0, row=0, columnspan=3, sticky=(E, W))

    save_name = StringVar()
    ttk.Entry(sidebar_frame, textvariable=save_name).grid(
        column=0, row=1, columnspan=3, sticky=(E, W)
    )

    ttk.Button(
        sidebar_frame,
        text="Load Rotation",
        command=lambda: load_rotation_config(listbox, display_config, save_name),
    ).grid(column=3, row=0, sticky=(E, W))

    ttk.Button(
        sidebar_frame,
        text="Delete Rotation",
        command=lambda: delete_rotation_config(listbox, save_name),
    ).grid(column=4, row=0, sticky=(E, W))

    ttk.Button(
        sidebar_frame,
        text="Save Rotation",
        command=lambda: save_rotation_config(display_config, save_name),
    ).grid(column=3, row=1, columnspan=2, sticky=(E, W))

    return rotation_manager_frame
