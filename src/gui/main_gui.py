from tkinter import *
from tkinter import ttk

from .character_manager import setup_character_manager_frame


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

    notebook.add(character_manager_frame, text="Character Manager")

    root.mainloop()
