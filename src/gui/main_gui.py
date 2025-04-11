from tkinter import *
from tkinter import ttk

from .character_manager import setup_character_manager_frame
from .import_manager import setup_import_manager_frame
from .rotation_manager import setup_rotation_manager_frame
from .config_manager import setup_config_manager_frame


# setup
def main():
    root = Tk()
    root.title("GCSim Config Creator")
    root.state("zoomed")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    notebook = ttk.Notebook(root)
    notebook.grid(column=0, row=0, sticky=(N, W, E, S))

    character_manager_frame = setup_character_manager_frame(root, notebook)
    import_manager_frame = setup_import_manager_frame(root, notebook)
    rotation_manager_frame = setup_rotation_manager_frame(root, notebook)
    config_manager_frame = setup_config_manager_frame(root, notebook)

    notebook.add(character_manager_frame, text="Character Manager")
    notebook.add(import_manager_frame, text="Import Manager")
    notebook.add(rotation_manager_frame, text="Rotation Manager")
    notebook.add(config_manager_frame, text="Config Manager")

    root.mainloop()
