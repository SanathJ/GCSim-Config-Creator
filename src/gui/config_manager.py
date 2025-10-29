import sqlite3
from tkinter import *
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .import_manager import get_character_config_list
from .rotation_manager import get_rotation_config_list


def refresh_preview(
    characters: list[ttk.Combobox],
    rotation: ttk.Combobox,
    preview: ScrolledText,
    info_label: Label,
    sidebar_frame: ttk.Frame,
):
    full_config = ""
    characters = [x.get() for x in characters if x.get()]

    info_list = []

    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()

        char_configs = []
        for i in range(len(characters)):
            cursor.execute(
                f""" 
                SELECT config, character
                FROM Character_Configs
                WHERE config_name = ?
                """,
                (characters[i],),
            )
            char_configs.append(cursor.fetchone())
        full_config += "\n".join([x for (x, _) in char_configs if x])

        if len(set([c for (_, c) in char_configs if c])) < len(char_configs):
            info_list.append(
                "Warning: Duplicate characters detected in the configuration."
            )

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
        else:
            info_list.append("Warning: No rotation selected.")

        if len(characters) == 0 and row:
            info_list.append("Warning: No characters selected.")

    # change wordwrap before displaying text
    info_label.configure(wraplength=sidebar_frame.winfo_width() - 20)

    if info_list:
        info_label.configure(text="\n".join(info_list))
    else:
        info_label.configure(text="")

    if info_label.cget("text").startswith("Warning"):
        info_label.configure(foreground="red")
    else:
        info_label.configure(foreground="green")

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

        # warning messagebox for existing name
        cursor.execute(
            """
            SELECT 1
            FROM Full_Configs
            WHERE config_name = ?
            """,
            (save_name.get(),),
        )
        if cursor.fetchone():
            res = messagebox.askokcancel(
                "Overwrite Config",
                f"A config with the name {save_name.get()} already exists. Saving will overwrite the existing config. Proceed?",
            )
            if not res:
                return

        cursor.execute(
            """
            INSERT OR REPLACE INTO Full_Configs (config_name, rotation, character1, character2, character3, character4)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (save_name.get(), rotation.get() if rotation.get() else None, *characters),
        )


def get_full_config_list() -> list[str]:
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
    info_label: Label,
    sidebar_frame: ttk.Frame,
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

        refresh_preview(characters, rotation, preview, info_label, sidebar_frame)
        save_name.set(listbox.get())


def setup_config_manager_frame(root: Tk, notebook: ttk.Notebook) -> ttk.Frame:
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
    sidebar_frame.grid(column=1, row=1, rowspan=1, sticky=(N, S), pady=10)

    info_label = ttk.Label(
        sidebar_frame,
        text="",
        font=("TkDefaultFont", 16),
    )
    info_label.grid(column=0, row=3, columnspan=5, sticky=(N, S, E, W))

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
            lambda e: refresh_preview(
                char_array, rotation, preview, info_label, sidebar_frame
            ),
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
        lambda e: refresh_preview(
            char_array, rotation, preview, info_label, sidebar_frame
        ),
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
    listbox.grid(column=0, row=0, columnspan=3, sticky=(N, E, W))

    save_name = StringVar()
    ttk.Entry(sidebar_frame, textvariable=save_name).grid(
        column=0, row=1, columnspan=3, sticky=(E, W)
    )

    ttk.Button(
        sidebar_frame,
        text="Load Config",
        command=lambda: load_full_config(
            listbox, char_array, rotation, save_name, preview, info_label, sidebar_frame
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

    ttk.Separator(sidebar_frame, orient=HORIZONTAL).grid(
        column=0, row=2, columnspan=5, sticky=(E, W), pady=5
    )

    # ttk.Button(
    #     sidebar_frame,
    #     text="Run Config in Browser",
    #     # command=lambda: ,
    # ).grid(column=0, row=3, columnspan=5, sticky=(E, W)),

    # ttk.Separator(sidebar_frame, orient=HORIZONTAL).grid(
    #     column=0, row=4, columnspan=5, sticky=(E, W), pady=5
    # )

    return config_manager_frame
