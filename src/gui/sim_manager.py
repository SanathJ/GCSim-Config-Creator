import os
import sqlite3
import subprocess
import sys
import tempfile
from tkinter import *
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Literal

from .config_manager import get_full_config_list

id = None
results = {}


def timed_info_label(
    sidebar_frame: ttk.Frame,
    info_label: ttk.Label,
    message: str,
    type: Literal["success", "warning", "info"],
    delay: int | None = 5000,
):
    info_label.configure(wraplength=sidebar_frame.winfo_width() - 20)
    if type == "success":
        info_label.configure(foreground="green")
    elif type == "warning":
        info_label.configure(foreground="red")
    else:
        info_label.configure(foreground="black")
    info_label.configure(text=message)
    global id
    if id:
        info_label.after_cancel(id)

    if delay:
        id = info_label.after(delay, lambda: info_label.configure(text=""))


def add_sim_config(
    sidebar_frame: ttk.Frame,
    info_label: ttk.Label,
    config_list: ttk.Treeview,
    selected_config: str,
):
    if not selected_config:
        return

    if config_list.exists(selected_config):
        timed_info_label(
            sidebar_frame,
            info_label,
            f"Config {selected_config} already exists in the list.",
            "warning",
        )
        return

    config_list.insert("", "end", iid=selected_config, text=selected_config)


def remove_sim_config(config_list: ttk.Treeview):
    if not config_list.selection():
        return
    results.pop(config_list.selection()[0], None)
    config_list.delete(config_list.selection()[0])


def exe_selector(sidebar_frame: ttk.Frame, info_label: ttk.Label, entry: ttk.Entry):
    exefile = filedialog.askopenfilename(
        title="Select GCSim Executable",
        filetypes=[("GCSim Executable", ["*.exe"])],
    )
    if not os.path.isfile(exefile):
        timed_info_label(
            sidebar_frame,
            info_label,
            "This file does not exist. Please select a valid GCSim executable.",
            "warning",
            None,
        )
        return
    else:
        timed_info_label(
            sidebar_frame,
            info_label,
            "",
            "success",
        )
    entry.configure(state="normal")
    entry.delete(0, "end")
    entry.insert(0, exefile)
    entry.configure(state="disabled")


def refresh_output_log(item: str, log_output: ScrolledText):
    log_output.configure(state="normal")
    log_output.delete("1.0", "end")

    if item in results:
        log_output.insert(
            "1.0",
            results[item]["output"],
        )

    log_output.insert("1.0", "")
    log_output.configure(state="disabled")


def refresh_textbox(
    config_list: ttk.Treeview,
    log_output: ScrolledText,
    display_config: ScrolledText,
    selected_config: str,
):
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

    refresh_output_log(selected_config, log_output)


def launch_handler(
    config_list: ttk.Treeview,
    log_output: ScrolledText,
    exe_path: str,
    sidebar_frame: ttk.Frame,
    info_label: ttk.Label,
    single: bool = False,
    browser: bool = False,
    options: str = "",
):
    global results

    maindir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )

    if not os.path.isfile(exe_path):
        timed_info_label(
            sidebar_frame,
            info_label,
            "GCSim executable not found. Please select a valid path.",
            "warning",
            None,
        )
        return

    os.makedirs(os.path.join(maindir, "out"), exist_ok=True)

    if single and not config_list.selection():
        timed_info_label(
            sidebar_frame,
            info_label,
            "No config selected to run.",
            "warning",
        )
        return

    if not single:
        results = {}

    with sqlite3.connect("configs.db") as con:
        cursor = con.cursor()

        for item in config_list.get_children(""):
            if single:
                if item != config_list.selection()[0]:
                    continue
                results.pop(item, None)

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
                timed_info_label(
                    sidebar_frame,
                    info_label,
                    f"Config {selected_config} not found.",
                    "warning",
                )
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
                timed_info_label(
                    sidebar_frame,
                    info_label,
                    f"Config rotation not found.",
                    "warning",
                )
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
                if options:
                    arglist.extend(options.split(" "))

                timed_info_label(
                    sidebar_frame,
                    info_label,
                    f"Running simulation for {selected_config}...",
                    "success",
                    delay=None,
                )
                sim = subprocess.run(
                    args=arglist, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                )

                timed_info_label(
                    sidebar_frame,
                    info_label,
                    f"",
                    "info",
                )
                results[selected_config] = {
                    "returncode": sim.returncode,
                    "output": sim.stdout.decode("utf-8"),
                }
                if config_list.selection():
                    refresh_output_log(config_list.selection()[0], log_output)
                else:
                    refresh_output_log(None, log_output)

                if sim.stderr and sim.returncode != 0:
                    timed_info_label(
                        sidebar_frame,
                        info_label,
                        sim.stderr.decode("utf-8"),
                        "info",
                    )

    if not config_list.selection():
        config_list.selection_set(config_list.get_children("")[-1])


def set_default_substat_options(
    liquid_substats: ttk.Spinbox, liquid_cap: ttk.Spinbox, fixed_substats: ttk.Spinbox
):
    liquid_substats.set(20)
    liquid_cap.set(10)
    fixed_substats.set(2)


def disable_substat_optimizer_options(
    fine_tune_button: ttk.Checkbutton,
    set_default_button: ttk.Button,
    liquid_substats: ttk.Spinbox,
    liquid_cap: ttk.Spinbox,
    fixed_substats: ttk.Spinbox,
):
    fine_tune_button.configure(state="disabled")
    set_default_button.configure(state="disabled")
    liquid_substats.configure(state="disabled")
    liquid_cap.configure(state="disabled")
    fixed_substats.configure(state="disabled")


def enable_substat_optimizer_options(
    fine_tune_button: ttk.Checkbutton,
    set_default_button: ttk.Button,
    liquid_substats: ttk.Spinbox,
    liquid_cap: ttk.Spinbox,
    fixed_substats: ttk.Spinbox,
):
    fine_tune_button.configure(state="normal")
    set_default_button.configure(state="normal")
    liquid_substats.configure(state="normal")
    liquid_cap.configure(state="normal")
    fixed_substats.configure(state="normal")


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

    info_label = ttk.Label(
        right_sidebar_frame,
        text="",
        font=("TkDefaultFont", 12),
    )

    # Left Sidebar
    config_list = ttk.Treeview(config_list_sidebar_frame)
    config_list.configure(selectmode="browse", show="tree")
    config_list.grid(column=0, row=0, columnspan=4, sticky=(N, S, E, W))

    # Middle
    main_sim_manager_frame.grid_columnconfigure(0, weight=1)
    main_sim_manager_frame.grid_rowconfigure(0, weight=1)

    preview_frame = ttk.Frame(main_sim_manager_frame)
    preview_frame.grid(column=0, row=0, sticky=(N, S, E, W))
    preview_frame.grid_columnconfigure(0, weight=1)
    preview_frame.grid_rowconfigure(1, weight=1)

    ttk.Label(preview_frame, text="Config").grid(column=0, row=0)
    preview = ScrolledText(preview_frame)
    preview.configure(state="disabled")
    preview.grid(column=0, row=1, sticky=(N, S, E, W), padx=10, pady=(0, 10))

    log_frame = ttk.Frame(main_sim_manager_frame)
    log_frame.grid(column=0, row=1, sticky=(N, S, E, W))
    log_frame.grid_columnconfigure(0, weight=1)
    log_frame.grid_rowconfigure(1, weight=1)

    ttk.Label(log_frame, text="Simulation Output").grid(column=0, row=0)
    log_output = ScrolledText(log_frame, height=15)
    log_output.configure(state="disabled")
    log_output.grid(column=0, row=1, sticky=(S, E, W), padx=10, pady=(0, 10))

    config_list.bind(
        "<<TreeviewSelect>>",
        lambda e: config_list.selection()
        and refresh_textbox(
            config_list, log_output, preview, config_list.selection()[0]
        ),
    )

    # Right Sidebar
    ttk.Button(
        right_sidebar_frame,
        text="Remove Selected Config",
        command=lambda: remove_sim_config(config_list)
        or refresh_output_log(None, log_output),
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
        or refresh_textbox(config_list, log_output, preview, listbox.get()),
    )

    ttk.Button(
        right_sidebar_frame,
        text="Add Config",
        command=lambda: add_sim_config(
            right_sidebar_frame, info_label, config_list, listbox.get()
        ),
    ).grid(column=3, row=1, sticky=(E, W))

    ttk.Separator(right_sidebar_frame, orient=HORIZONTAL).grid(
        column=0, row=2, columnspan=4, sticky=(E, W), pady=5
    )

    exepath = ttk.Entry(right_sidebar_frame, width=30)
    exepath.grid(column=0, row=3, columnspan=3, sticky=(E, W))
    exepath.configure(state="disabled")
    ttk.Button(
        right_sidebar_frame,
        text="Select GCSim EXE",
        command=lambda: exe_selector(right_sidebar_frame, info_label, exepath),
    ).grid(column=3, row=3, sticky=(E, W))

    # Options
    substat_optimizer = BooleanVar(value=True)
    substat_optimizer_button = ttk.Checkbutton(
        right_sidebar_frame,
        text="Substat Optimizer",
        variable=substat_optimizer,
    )
    substat_optimizer_button.grid(column=0, row=4, columnspan=2, sticky=(E, W))

    fine_tune = BooleanVar(value=True)
    fine_tune_button = ttk.Checkbutton(
        right_sidebar_frame,
        text="Fine tune",
        variable=fine_tune,
    )
    fine_tune_button.grid(column=2, row=4, columnspan=2, sticky=(E, W))

    default_button = ttk.Button(
        right_sidebar_frame,
        text="Set Defaults",
    )
    default_button.grid(column=0, row=5, columnspan=4, sticky=(E, W))

    ttk.Label(right_sidebar_frame, text="Total Liquid Substats", anchor="center").grid(
        column=0, row=6, sticky=(W, E)
    )
    liquid_substats_box = ttk.Spinbox(
        right_sidebar_frame,
        from_=0,
        to=100,
        width=5,
        state="disabled",
    )
    liquid_substats_box.grid(column=1, row=6, columnspan=3, sticky=(E, W))

    ttk.Label(right_sidebar_frame, text="Individual Liquid Cap", anchor="center").grid(
        column=0, row=7, sticky=(W, E)
    )
    liquid_cap_box = ttk.Spinbox(right_sidebar_frame, from_=0, to=100, width=5)
    liquid_cap_box.grid(column=1, row=7, columnspan=3, sticky=(E, W))

    ttk.Label(right_sidebar_frame, text="Fixed Substats Count", anchor="center").grid(
        column=0, row=8, sticky=(W, E)
    )
    fixed_substats_box = ttk.Spinbox(right_sidebar_frame, from_=0, to=100, width=5)
    fixed_substats_box.grid(column=1, row=8, columnspan=3, sticky=(E, W))

    substat_optimizer_button.configure(
        command=lambda: (
            disable_substat_optimizer_options(
                fine_tune_button,
                default_button,
                liquid_substats_box,
                liquid_cap_box,
                fixed_substats_box,
            )
            if not substat_optimizer.get()
            else enable_substat_optimizer_options(
                fine_tune_button,
                default_button,
                liquid_substats_box,
                liquid_cap_box,
                fixed_substats_box,
            )
        )
    )

    default_button.configure(
        command=lambda: set_default_substat_options(
            liquid_substats_box, liquid_cap_box, fixed_substats_box
        ),
    )
    set_default_substat_options(liquid_substats_box, liquid_cap_box, fixed_substats_box)
    substat_optimizer_button.invoke()

    def generate_options_string() -> str:
        if not substat_optimizer.get():
            return ""
        options = '-substatOptimFull -options="'
        # fine_tune={1 if fine_tune else 0};'
        if (
            liquid_substats_box.get()
            or liquid_cap_box.get()
            or fixed_substats_box.get()
        ):
            if liquid_substats_box.get():
                options += f"total_liquid_substats={liquid_substats_box.get()};"
            if liquid_cap_box.get():
                options += f"indiv_liquid_cap={liquid_cap_box.get()};"
            if fixed_substats_box.get():
                options += f"fixed_substats_count={fixed_substats_box.get()};"
        options += f'fine_tune={1 if fine_tune.get() else 0};"'
        return options

    ttk.Button(
        right_sidebar_frame,
        text="Run all in browser",
        command=lambda: launch_handler(
            config_list,
            log_output,
            exepath.get(),
            right_sidebar_frame,
            info_label,
            browser=True,
            options=generate_options_string(),
        ),
    ).grid(column=0, row=9, columnspan=2, sticky=(E, W))
    ttk.Button(
        right_sidebar_frame,
        text="Run all in CLI",
        command=lambda: launch_handler(
            config_list,
            log_output,
            exepath.get(),
            right_sidebar_frame,
            info_label,
            options=generate_options_string(),
        ),
    ).grid(column=2, row=9, columnspan=2, sticky=(E, W))

    ttk.Button(
        right_sidebar_frame,
        text="Run config in browser",
        command=lambda: launch_handler(
            config_list,
            log_output,
            exepath.get(),
            right_sidebar_frame,
            info_label,
            single=True,
            browser=True,
            options=generate_options_string(),
        ),
    ).grid(column=0, row=10, columnspan=2, sticky=(E, W))
    ttk.Button(
        right_sidebar_frame,
        text="Run config in CLI",
        command=lambda: launch_handler(
            config_list,
            log_output,
            exepath.get(),
            right_sidebar_frame,
            info_label,
            single=True,
            options=generate_options_string(),
        ),
    ).grid(column=2, row=10, columnspan=2, sticky=(E, W))

    ttk.Separator(right_sidebar_frame, orient=HORIZONTAL).grid(
        column=0, row=11, columnspan=4, sticky=(E, W), pady=5
    )

    info_label.grid(column=0, row=12, columnspan=4, sticky=(E, W))

    return sim_manager_frame
