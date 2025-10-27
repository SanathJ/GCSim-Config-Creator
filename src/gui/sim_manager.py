import os
import sqlite3
import subprocess
import sys
import tempfile
from tkinter import *
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText

from .config_manager import get_full_config_list


def add_sim_config(config_list: ttk.Treeview, selected_config: str):
    if not selected_config:
        return

    if config_list.exists(selected_config):
        print(f"Config {selected_config} already exists in the list.", file=sys.stderr)
        return

    config_list.insert("", "end", iid=selected_config, text=selected_config)


def remove_sim_config(config_list: ttk.Treeview):
    if not config_list.selection():
        return
    config_list.delete(config_list.selection()[0])


def exe_selector(entry: Entry):
    exefile = filedialog.askopenfilename(
        title="Select GCSim Executable",
        filetypes=[("GCSim Executable", ["*.exe"])],
    )
    if not os.path.isfile(exefile):
        print("This file does not exist.", file=sys.stderr)
        return
    entry.configure(state="normal")
    entry.delete(0, "end")
    entry.insert(0, exefile)
    entry.configure(state="disabled")


def launch_handler(
    config_list: ttk.Treeview,
    exe_path: str,
    single: bool = False,
    browser: bool = False,
):
    maindir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )

    os.makedirs(os.path.join(maindir, "out"), exist_ok=True)

    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()

        for item in config_list.get_children(""):
            selected_config = item
            cursor.execute(
                f""" 
                SELECT character1, character2, character3, character4, rotation
                FROM Full_Configs
                WHERE config_name = ?
                """,
                (selected_config,),
            )
            row = cursor.fetchone()
            if not row:
                print(f"Config {selected_config} not found.", file=sys.stderr)
                return
            characters = [x for x in row[:4] if x]
            rotation = row[4]
            full_config = ""

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
                (rotation,),
            )
            row = cursor.fetchone()
            if not row:
                print(f"Config rotation not found.", file=sys.stderr)
                return
            full_config += "\n" + row[0]

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", encoding="utf-8", delete_on_close=False
            ) as temp_config_file:
                temp_config_file.write(full_config)
                temp_config_file.close()

                arglist = [
                    exe_path,
                    "-c",
                    temp_config_file.name,
                    "-out",
                    os.path.join(maindir, "out", f"{selected_config}.json"),
                ]
                if browser:
                    arglist.append("-s")
                sim = subprocess.run(
                    args=arglist,
                    capture_output=True,
                )
                print(f"{selected_config}:\n" + sim.stdout.decode("utf-8"))


def refresh_textbox(display_config: ScrolledText, selected_config: str):
    display_config.configure(state="normal")
    display_config.delete("1.0", "end")

    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()

        cursor.execute(
            f""" 
            SELECT character1, character2, character3, character4, rotation
            FROM Full_Configs
            WHERE config_name = ?
            """,
            (selected_config,),
        )
        row = cursor.fetchone()
        if not row:
            display_config.insert("1.0", "Config not found.")
            display_config.configure(state="disabled")
            return
        characters = [x for x in row[:4] if x]
        rotation = row[4]
        full_config = ""

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
            (rotation,),
        )
        row = cursor.fetchone()
        if row:
            full_config += "\n" + row[0]

    display_config.insert("1.0", full_config)
    display_config.configure(state="disabled")


def setup_sim_manager_frame(root: Tk, notebook: ttk.Notebook) -> ttk.Frame:
    sim_manager_frame = ttk.Frame(notebook)
    sim_manager_frame.grid(column=0, row=0, sticky=(N, S, E, W))
    sim_manager_frame.grid_columnconfigure(1, weight=1)
    sim_manager_frame.grid_rowconfigure(0, weight=1)

    config_list_sidebar_frame = ttk.Frame(sim_manager_frame)
    config_list_sidebar_frame.grid(column=0, row=0, sticky=(N, S, E, W), pady=(20, 10))
    config_list_sidebar_frame.grid_rowconfigure(0, weight=1)

    main_sim_manager_frame = ttk.Frame(sim_manager_frame)
    main_sim_manager_frame.grid(column=1, row=0, sticky=(N, S, E, W))

    # button sidebar
    right_sidebar_frame = ttk.Frame(sim_manager_frame)
    right_sidebar_frame.grid(column=2, row=0, sticky=(N), pady=(20, 0))

    # Left Sidebar
    config_list = ttk.Treeview(config_list_sidebar_frame)
    config_list.configure(selectmode="browse", show="tree")
    config_list.grid(column=0, row=0, columnspan=4, sticky=(N, S, E, W))
    config_list.bind(
        "<<TreeviewSelect>>",
        lambda e: config_list.selection()
        and refresh_textbox(preview, config_list.selection()[0]),
    )

    # Middle
    preview_frame = ttk.Frame(main_sim_manager_frame)
    preview_frame.grid(column=0, row=0, sticky=(N, S, E, W))

    preview_frame.grid_columnconfigure(0, weight=1)
    preview_frame.grid_rowconfigure(1, weight=1)

    ttk.Label(preview_frame, text="Config").grid(column=0, row=0)
    preview = ScrolledText(preview_frame)
    preview.configure(state="disabled")
    preview.grid(column=0, row=1, sticky=(N, S, E, W), padx=10, pady=(0, 10))

    main_sim_manager_frame.grid_columnconfigure(0, weight=1)
    main_sim_manager_frame.grid_rowconfigure(0, weight=1)

    # Right Sidebar

    ttk.Button(
        right_sidebar_frame,
        text="Remove Selected Config",
        command=lambda: remove_sim_config(config_list),
    ).grid(column=0, row=0, columnspan=4, sticky=(E, W))

    listbox = ttk.Combobox(
        right_sidebar_frame,
        width=40,
        height=10,
        values=get_full_config_list(),
        state="readonly",
        postcommand=lambda: listbox.configure(values=get_full_config_list()),
    )
    listbox.grid(column=0, row=1, columnspan=3, sticky=(E, W))
    listbox.bind(
        "<<ComboboxSelected>>",
        lambda e: config_list.selection_remove(config_list.selection())
        or refresh_textbox(preview, listbox.get()),
    )

    ttk.Button(
        right_sidebar_frame,
        text="Add Config",
        command=lambda: add_sim_config(config_list, listbox.get()),
    ).grid(column=3, row=1, sticky=(E, W))

    exepath = ttk.Entry(right_sidebar_frame, width=30)
    exepath.grid(column=0, row=3, columnspan=3, sticky=(E, W), pady=(15, 0))
    exepath.configure(state="disabled")
    ttk.Button(
        right_sidebar_frame,
        text="Select GCSim EXE",
        command=lambda: exe_selector(exepath),
    ).grid(column=3, row=3, sticky=(E, W), pady=(15, 0))

    ttk.Button(
        right_sidebar_frame,
        text="Run all in browser",
        command=lambda: launch_handler(config_list, exepath.get(), browser=True),
    ).grid(column=0, row=4, columnspan=2, sticky=(E, W))
    ttk.Button(
        right_sidebar_frame,
        text="Run all in CLI",
        command=lambda: launch_handler(config_list, exepath.get()),
    ).grid(column=2, row=4, columnspan=2, sticky=(E, W))

    return sim_manager_frame
