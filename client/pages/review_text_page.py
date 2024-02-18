import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
import threading
import os, sys

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

import api.controllers.get_generated_text as generate_text
import api.controllers.get_generated_image as generate_image
from api.controllers.get_text_scores import get_readability_score

class DisplayTextPage(tk.Frame):
    def __init__(self, parent, json_template, gen_old_txt_image, gen_new_txt_image):
        tk.Frame.__init__(self, parent)
        self.json_template = json_template
        
        self.input_text = self.json_template["prompt_parameters"]["text_to_adjust"]
        self.output_text = None
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        # Adjusting grid configurations for dynamic spacing
        self.grid_rowconfigure(1, weight=1)  # Lesser weight to text displays
        self.grid_rowconfigure(4, weight=3)  # More weight to image display area

        # Return to TextEditor page
        self.return_button = tk.Button(self, text="Back to Editing", command=self.go_to_editing_page)
        self.return_button.grid(row=0, column=2, sticky='ne', padx=(10, 10))

        # Input Text Display
        self.input_text_frame = tk.Frame(self, borderwidth=2, relief="groove")
        self.input_text_display = tk.Text(self.input_text_frame, wrap="word")
        self.input_scrollbar = tk.Scrollbar(self.input_text_frame, command=self.input_text_display.yview)
        self.input_text_display.config(yscrollcommand=self.input_scrollbar.set)
        self.input_text_display.insert('1.0', self.input_text)
        self.input_text_display.config(state='disabled')  # Make the text display only

        self.input_text_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.input_text_display.pack(side="left", fill="both", expand=True)
        self.input_scrollbar.pack(side="right", fill="y")
        self.input_text_display.config(height=3)
        self.input_text_frame.grid_propagate(False)


        self.input_headline_label  = tk.Label(self, text="Input Text", font=("Arial", 10, "bold"))
        self.input_headline_label.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        # Get the readability score for the Input text
        scores_dict = get_readability_score(self.input_text)
        readability_score = '\n'.join('- {}: {}'.format(score_key, scores_dict[f"{score_key}"]) for score_key in scores_dict)
        self.input_score_label = tk.Label(self, text=f"Readability: \n{readability_score}")
        self.input_score_label.grid(row=2, column=0, sticky="nsew", padx=(10, 0))

        # Output Text Display
        self.output_text_frame = tk.Frame(self, borderwidth=2, relief="groove")
        self.output_text_display = tk.Text(self.output_text_frame, wrap="word")
        self.output_scrollbar = tk.Scrollbar(self.output_text_frame, command=self.output_text_display.yview)
        self.output_text_display.config(yscrollcommand=self.output_scrollbar.set)

        self.output_headline_label  = tk.Label(self, text="Output Text", font=("Arial", 10, "bold"))
        self.output_headline_label.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self.output_text_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        self.output_text_display.pack(side="left", fill="both", expand=True)
        self.output_scrollbar.pack(side="right", fill="y")
        self.output_text_display.config(height=3)
        self.output_text_frame.grid_propagate(False)

        # Progress Bar
        self.progress = ttk.Progressbar(self, orient="horizontal", length=200, mode="indeterminate")
        self.progress.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(150, 150))

        self.generate_image_for_old_text = gen_old_txt_image
        self.generate_image_for_new_text = gen_new_txt_image

        # Image Frame Setup
        self.image_frame = tk.Frame(self)
        self.image_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=10)
        self.old_image_label = tk.Label(self.image_frame)
        self.new_image_label = tk.Label(self.image_frame)
        # Adjust the layout according to your design. For example:
        self.old_image_label.pack(side="left", padx=10, fill="both", expand=True)
        self.new_image_label.pack(side="right", padx=10, fill="both", expand=True)

        self.save_old_image_button = tk.Button(self.image_frame, text="Save Old Image", command=self.save_old_image)
        self.save_new_image_button = tk.Button(self.image_frame, text="Save New Image", command=self.save_new_image)

        self.start_text_and_image_generation()

    def start_text_and_image_generation(self):

        self.progress.start()

        threading.Thread(target=self.generate_output_text).start()

        if self.generate_image_for_old_text:
            threading.Thread(target=self.generate_output_image, args=("Old",)).start()
        
    def generate_output_text(self):
        # Call the generate function
        output_text = generate_text.get_generated_text(self.json_template)  # Adjust this line as needed
        self.output_text = output_text

        self.json_template["prompt_parameters"]["adjusted_text"] = self.output_text

        # Get the readability score for the output text
        scores_dict = get_readability_score(self.output_text)
        readability_score = '\n'.join('- {}: {}'.format(score_key, scores_dict[f"{score_key}"]) for score_key in scores_dict)
        self.output_score_label = tk.Label(self, text=f"Readability: \n{readability_score}")
        self.output_score_label.grid(row=2, column=1, sticky="nsew", padx=(10, 0))

        self.progress.stop()

        if self.generate_image_for_new_text:
            threading.Thread(target=self.generate_output_image, args=("New",)).start()

        # Safe update of the Tkinter UI from another thread
        self.after(0, self.display_output_text, output_text)

    def generate_output_image(self, text_version):
        
        # Call the generate function
        self.progress.start()
        output_image = generate_image.get_generated_image(self.json_template, text_version)  # Adjust this line as needed
        self.progress.stop()

        # Decide where to display the image
        if text_version == "Old":
            self.original_old_image = output_image
            self.after(0, self.display_image, output_image, self.old_image_label, text_version)
        elif text_version == "New":
            self.original_new_image = output_image
            self.after(0, self.display_image, output_image, self.new_image_label, text_version)

    def display_output_text(self, output_text):

        self.output_text_display.config(state='normal')
        self.output_text_display.delete('1.0', tk.END)
        self.output_text_display.insert('1.0', output_text)
        self.output_text_display.config(state='disabled')

    def display_image(self, output_image, image_label, image_version):
        
        # Dynamically calculate the desired height
        total_height = self.winfo_height()
        text_widgets_height = total_height * 0.4  # Assuming text widgets use 40% of the height
        desired_height = (total_height - text_widgets_height) * 0.8  # 80% of the remaining height for the image
        
        # Resize the image to fit the calculated height while maintaining aspect ratio
        output_image.thumbnail((self.winfo_width() // 2, desired_height), Image.ANTIALIAS)
        
        # Convert PIL image to a format Tkinter can handle
        tk_image = ImageTk.PhotoImage(output_image)
        
        # Display the image in the appropriate label
        image_label.configure(image=tk_image)
        image_label.image = tk_image  # Keep a reference to avoid garbage collection
        
        # Show the corresponding save button
        if image_version == "Old":
            self.save_old_image_button.pack(side="bottom", pady=10)
        else:
            self.save_new_image_button.pack(side="bottom", pady=10)

    def save_old_image(self):
        if hasattr(self, 'original_old_image'):
            filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
            if filepath:
                self.original_old_image.save(filepath)

    def save_new_image(self):
        if hasattr(self, 'original_new_image'):
            filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
            if filepath:
                self.original_new_image.save(filepath)
    
    def go_to_editing_page(self):
        self.master.show_page("TextPage")