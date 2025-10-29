import sqlite3
from tkinter import *
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText


def get_rotation_config_list() -> list[str]:
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


id = None


def load_rotation_config(
    listbox: ttk.Combobox,
    display_config: ScrolledText,
    save_name: StringVar,
    info_label: ttk.Label,
    sidebar_frame: ttk.Frame,
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

    # change wordwrap before displaying text
    info_label.configure(wraplength=sidebar_frame.winfo_width() - 20)
    info_label.configure(foreground="green")
    info_label.configure(text=f"Rotation {listbox.get()} loaded successfully.")
    global id
    if id:
        info_label.after_cancel(id)
    id = info_label.after(5000, lambda: info_label.configure(text=""))


def delete_rotation_config(
    listbox: ttk.Combobox,
    save_name: StringVar,
    info_label: ttk.Label,
    sidebar_frame: ttk.Frame,
):
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

    # change wordwrap before displaying text
    info_label.configure(wraplength=sidebar_frame.winfo_width() - 20)
    info_label.configure(foreground="green")
    info_label.configure(text=f"Rotation {listbox.get()} deleted successfully.")
    global id
    if id:
        info_label.after_cancel(id)
    id = info_label.after(5000, lambda: info_label.configure(text=""))

    listbox.set("")
    save_name.set("")


def save_rotation_config(
    display_config: ScrolledText,
    save_name: StringVar,
    info_label: ttk.Label,
    sidebar_frame: ttk.Frame,
):
    if not save_name.get():
        return

    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM Rotation_Configs
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
            INSERT OR REPLACE INTO Rotation_Configs (config_name, config)
            VALUES (?, ?)
            """,
            (save_name.get(), display_config.get("1.0", "end")),
        )

    # change wordwrap before displaying text
    info_label.configure(wraplength=sidebar_frame.winfo_width() - 20)
    info_label.configure(foreground="green")
    info_label.configure(text=f"Rotation {save_name.get()} saved successfully.")
    global id
    if id:
        info_label.after_cancel(id)
    id = info_label.after(5000, lambda: info_label.configure(text=""))


def setup_rotation_manager_frame(root: Tk, notebook: ttk.Notebook) -> ttk.Frame:
    rotation_manager_frame = ttk.Frame(notebook)
    rotation_manager_frame.grid(column=0, row=0, sticky=(N, S, E, W))
    rotation_manager_frame.grid_rowconfigure(0, weight=1)
    rotation_manager_frame.grid_columnconfigure(0, weight=1)

    main_rotation_manager_frame = ttk.Frame(rotation_manager_frame)
    main_rotation_manager_frame.grid(
        column=0, row=0, sticky=(N, S, E, W), padx=10, pady=10
    )

    # button sidebar
    sidebar_frame = ttk.Frame(rotation_manager_frame)
    sidebar_frame.grid(column=1, row=0, sticky=(N, S, E, W), pady=10)

    info_label = ttk.Label(
        sidebar_frame,
        text="",
        font=("TkDefaultFont", 16),
    )
    info_label.grid(column=0, row=3, columnspan=5, sticky=(N, S, E, W))

    # main

    display_config = ScrolledText(main_rotation_manager_frame)
    display_config.configure(undo=True)
    display_config.grid(column=0, row=0, sticky=(N, E, W, S))

    main_rotation_manager_frame.grid_columnconfigure(0, weight=1)
    main_rotation_manager_frame.grid_rowconfigure(0, weight=1)

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
        command=lambda: load_rotation_config(
            listbox, display_config, save_name, info_label, sidebar_frame
        ),
    ).grid(column=3, row=0, sticky=(E, W))

    ttk.Button(
        sidebar_frame,
        text="Delete Rotation",
        command=lambda: delete_rotation_config(
            listbox, save_name, info_label, sidebar_frame
        ),
    ).grid(column=4, row=0, sticky=(E, W))

    ttk.Button(
        sidebar_frame,
        text="Save Rotation",
        command=lambda: save_rotation_config(
            display_config, save_name, info_label, sidebar_frame
        ),
    ).grid(column=3, row=1, columnspan=2, sticky=(E, W))

    ttk.Separator(sidebar_frame, orient=HORIZONTAL).grid(
        column=0, row=2, columnspan=5, sticky=(E, W), pady=5
    )

    return rotation_manager_frame
