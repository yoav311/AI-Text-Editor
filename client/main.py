import tkinter as tk
from tkinter import ttk
import os
import json
import sys

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

# Import your page classes here
from pages.adjust_text_page import AdjustTextPage
from pages.review_text_page import DisplayTextPage

class TextEditorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Text Editor and Adjuster")
        self.geometry("1000x700")

        self.pages = {}
        self.current_page = None

        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.show_page("TextPage")

    def show_page(self, page_name, **kwargs):
        if self.current_page is not None:
            self.current_page.grid_forget()
        
        if page_name not in self.pages:
            if page_name == "TextPage":
                self.pages[page_name] = AdjustTextPage(self)
            elif page_name == "DisplayPage":
                # Pass additional kwargs to DisplayPage
                self.pages[page_name] = DisplayTextPage(self, **kwargs)
            else:
                raise ValueError(f"Unknown page name: {page_name}")
        
        self.current_page = self.pages[page_name]
        self.current_page.grid(row=0, column=0, sticky="nsew")

if __name__ == "__main__":
    app = TextEditorApp()
    app.mainloop()