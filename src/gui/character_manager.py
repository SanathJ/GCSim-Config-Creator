import sqlite3
from tkinter import *
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import util


def refresh_textbox(display_config: ScrolledText, tree: ttk.Treeview):
    display_config.configure(state="normal")
    display_config.delete("1.0", "end")
    if tree.selection():
        display_config.insert("1.0", tree.item(tree.selection())["values"][-1])
    display_config.configure(state="disabled")


def refresh_treeview(tree: ttk.Treeview):
    with sqlite3.connect("configs.db") as con:
        con.row_factory = util.dict_factory

        cursor = con.cursor()

        rows = cursor.execute(
            """
            SELECT *
            FROM Character_Configs
            """
        ).fetchall()

        for item in tree.get_children(""):
            tree.delete(item)

        for row in rows:
            tree.insert(
                "",
                "end",
                text=row["config_name"],
                values=(
                    row["character"],
                    row["constellation"],
                    row["level"],
                    row["talent"],
                    row["weapon"],
                    row["refine"],
                    row["config"],
                ),
            )


g_tree = None


def refresh_character_manager_tree():
    refresh_treeview(g_tree)


def delete_char_config(display_config: ScrolledText, tree: ttk.Treeview):
    if not tree.selection():
        return

    answer = messagebox.askyesno(
        "Delete Character",
        f"Are you sure you want to delete {tree.item(tree.selection())["text"]}?",
    )

    if answer:
        with sqlite3.connect("configs.db") as con:
            cursor = con.cursor()
            cursor.execute(
                """
                DELETE FROM Character_Configs
                WHERE config_name = ?
                """,
                (tree.item(tree.selection())["text"],),
            )

            con.commit()

    refresh_textbox(display_config, tree)
    refresh_treeview(tree)


def rename_char_config(root: Tk, display_config: ScrolledText, tree: ttk.Treeview):
    if not tree.selection():
        return

    # Function to handle the renaming process
    def open_rename_dialog(item_id: tuple[str, ...]):
        # Create a new top-level window for the rename dialog
        rename_dialog = Toplevel(root)
        rename_dialog.title("Rename Item")

        # Create a label and entry field to input the new name
        label = ttk.Label(rename_dialog, text="Enter new name:")
        label.pack(padx=10, pady=10)

        # Get the current name of the selected item
        current_name = tree.item(item_id)["text"]
        entry = ttk.Entry(rename_dialog)
        entry.insert(0, current_name)  # Set the current name in the entry
        entry.pack(padx=10, pady=10)

        # Function to save the new name
        def save_new_name():
            new_name = entry.get()
            if new_name:  # Ensure the new name isn't empty
                with sqlite3.connect("configs.db") as con:
                    cursor = con.cursor()
                    cursor.execute(
                        """
                        UPDATE Character_Configs
                        SET config_name = ?
                        WHERE config_name = ?
                        """,
                        (new_name, tree.item(tree.selection())["text"]),
                    )

            con.commit()
            rename_dialog.destroy()  # Close the rename dialog

        # Function to cancel the rename operation
        def cancel_rename():
            rename_dialog.destroy()  # Just close the dialog without changes

        # Create buttons for "Rename" and "Cancel"
        save_button = ttk.Button(rename_dialog, text="Rename", command=save_new_name)
        save_button.pack(side=LEFT, padx=10, pady=10)

        cancel_button = ttk.Button(rename_dialog, text="Cancel", command=cancel_rename)
        cancel_button.pack(side=LEFT, padx=10, pady=10)

        def dismiss():
            rename_dialog.grab_release()
            rename_dialog.destroy()

        rename_dialog.protocol("WM_DELETE_WINDOW", dismiss)  # intercept close button
        rename_dialog.transient(root)  # dialog window is related to main
        rename_dialog.wait_visibility()  # can't grab until window appears, so we wait

        x = root.winfo_x() + root.winfo_width() // 2 - rename_dialog.winfo_width() // 2
        y = (
            root.winfo_y()
            + root.winfo_height() // 2
            - rename_dialog.winfo_height() // 2
        )
        rename_dialog.geometry(f"+{x}+{y}")

        rename_dialog.grab_set()  # ensure all input goes to our window
        rename_dialog.wait_window()

    open_rename_dialog(tree.selection())
    refresh_textbox(display_config, tree)
    refresh_treeview(tree)


def setup_character_manager_frame(root: Tk, notebook: ttk.Notebook) -> ttk.Frame:
    character_manager_frame = ttk.Frame(notebook)
    character_manager_frame.grid(column=0, row=0, sticky=(N, S, E, W))

    main_config_manager_frame = ttk.Frame(character_manager_frame)
    main_config_manager_frame.grid(column=0, row=0)

    # button sidebar
    sidebar_frame = ttk.Frame(character_manager_frame)
    sidebar_frame.grid(column=1, row=0)

    # main
    tree = ttk.Treeview(
        main_config_manager_frame,
        columns=(
            "character",
            "constellation",
            "level",
            "talent",
            "weapon",
            "refine",
            "config",
        ),
        displaycolumns=[x for x in range(0, 6)],
    )

    headings = [
        "#0",
        "character",
        "constellation",
        "level",
        "talent",
        "weapon",
        "refine",
        "config",
    ]

    column_widths = [400, 180, 80, 50, 65, 260, 50, 200]
    for x, width in zip(headings, column_widths):
        tree.column(x, anchor="center", width=width)
        tree.heading(x, text="Config Name" if x == "#0" else x.title())
    tree.grid(column=0, row=0)
    global g_tree
    g_tree = tree

    tree_s = ttk.Scrollbar(
        main_config_manager_frame, orient=VERTICAL, command=tree.yview
    )
    tree.configure(yscrollcommand=tree_s.set, selectmode="browse")
    tree_s.grid(column=1, row=0, sticky=(N, S))

    display_config = ScrolledText(main_config_manager_frame)
    display_config.grid(column=0, row=1, columnspan=2, sticky=(E, W, S))
    tree.bind("<<TreeviewSelect>>", lambda e: refresh_textbox(display_config, tree))

    # buttons
    ttk.Button(
        sidebar_frame,
        text="Delete",
        command=lambda: delete_char_config(display_config, tree),
    ).grid(column=0, row=0)
    ttk.Button(
        sidebar_frame,
        text="Rename",
        command=lambda: rename_char_config(root, display_config, tree),
    ).grid(column=0, row=1)

    display_config.configure(state="disabled")

    refresh_treeview(tree)
    return character_manager_frame
