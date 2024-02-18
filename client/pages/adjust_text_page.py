import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import json
import sys
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from api.controllers.get_text_scores import get_ai_estimated_targets
from api.controllers.get_text_scores import get_classic_estimated_targets


def get_scene_from_text(text, scene_num):
    """
    Splits the input text into paragraphs and returns a list of paragraphs.
    
    Args:
    - text (str): The input text to be split into paragraphs.
    
    Returns:
    - list: A list where each item is a paragraph from the input text.
    """
    scene_num = scene_num -1

    # Split the text by newline characters to get paragraphs
    paragraphs = text.split('\n')
    
    # Filter out any empty paragraphs that may occur from multiple newlines
    paragraphs = [para.strip() for para in paragraphs if para.strip()]
    
    return paragraphs[scene_num]

class AdjustTextPage(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.json_template = self.load_json_template('text-adjuster-pbb.json')

        # Text Viewer
        self.text_viewer_frame = tk.Frame(self)
        self.text_viewer = tk.Text(self.text_viewer_frame, wrap="word")
        self.scrollbar_viewer = tk.Scrollbar(self.text_viewer_frame, command=self.text_viewer.yview)
        self.text_viewer.config(yscrollcommand=self.scrollbar_viewer.set)

        self.text_viewer_frame.grid(row=0, column=0, sticky="nsew")
        self.text_viewer.pack(side="left", fill="both", expand=True)
        self.scrollbar_viewer.pack(side="right", fill="y")

        # Text Editor

        # Create an outer frame for the right side that will fill the entire right column
        self.right_side_frame = tk.Frame(self)
        self.right_side_frame.grid(row=0, column=1, sticky="nsew")

        # Center the text editor frame within the right_side_frame
        self.text_editor_frame = tk.LabelFrame(self.right_side_frame, text="Text Editor", padx=10, pady=10, font=("Arial", 10, "bold"))
        self.text_editor_frame.pack(pady=(100, 0), fill="both", expand=True)  # Adjust pady for vertical centering
        self.text_editor_frame.configure(borderwidth=2, relief="groove") 
        
        self.adjust_text_button_var = tk.BooleanVar(value=False)
        self.adjust_text_button = tk.Checkbutton(self.text_editor_frame, text="Adjust Entire Text", variable=self.adjust_text_button_var, command=self.toggle_scene_number_entry)
        self.adjust_text_button.grid(row=0, column=0, sticky="nw", pady=2)

        self.scene_number_label = tk.Label(self.text_editor_frame, text="Scene Number:")
        self.scene_number_label.grid(row=1, column=0, sticky="e", padx=(10, 2))

        self.var1 = tk.StringVar()
        self.scene_number_entry = tk.Entry(self.text_editor_frame, text="Scene Number:", textvariable=self.var1)
        self.scene_number_entry.grid(row=1, column=1, sticky="w", padx=(2, 10))
        self.var1.trace_add("write", self.on_scene_number_entered)

        # Initially hidden
        self.generate_old_image_button_var = tk.BooleanVar(value=False)
        self.generate_old_image_button = tk.Checkbutton(self.text_editor_frame, text="Generate Image of Old Scene", variable=self.generate_old_image_button_var)
        self.generate_old_image_button.grid(row=2, column=0, sticky="nsew", pady=2)

        self.generate_new_image_button_var = tk.BooleanVar(value=False)
        self.generate_new_image_button = tk.Checkbutton(self.text_editor_frame, text="Generate Image of New Scene", variable=self.generate_new_image_button_var)
        self.generate_new_image_button.grid(row=3, column=0, sticky="nsew", pady=2)
        
        self.parameter_widgets_frame = tk.Frame(self.text_editor_frame)
        self.parameter_widgets_frame.grid(row=4, column=0, sticky="nsew")
        self.parameter_widgets = []

        self.add_parameter_button = tk.Button(self.text_editor_frame, text="Add Another Parameter", command=self.add_parameter_widget)
        self.add_parameter_button.grid(row=5, column=0, sticky="nsew", pady=2)

        self.submit_button = tk.Button(self.text_editor_frame, text="Submit", command=self.submit)
        self.submit_button.grid(row=6, column=0, sticky="nsew", pady=2)

        # Initially add one parameter widget
        self.add_parameter_widget()

    def on_scene_number_entered(self, name, index, mode):
        # This function is called when the user presses Enter after entering a scene number
        scene_number = self.scene_number_entry.get()
        if scene_number.isdigit():
            scene_number = int(scene_number)
            current_text = self.text_viewer.get("1.0", tk.END)
            try:
                paragraph = get_scene_from_text(current_text, scene_number)
                # Process the paragraph in a separate thread to avoid freezing the UI
                threading.Thread(target=self.process_paragraph, args=(scene_number-1, paragraph,)).start()
            except IndexError:
                messagebox.showerror("Error", "Scene number out of range")
        else:
            messagebox.showerror("Error", "Invalid scene number")

    def process_paragraph(self, para_idx, paragraph):

        # Execute the processing logic in a thread-safe manner
        try:
            ai_estimated_targets = get_ai_estimated_targets(self.json_template, paragraph)
            classic_estimated_targets = get_classic_estimated_targets(self.json_template, paragraph)

            combined_estimated_targets = classic_estimated_targets['estimated_targets'] + ai_estimated_targets['estimated_targets']
            
            self.json_template["prompt_parameters"]["estimated_targets_old_text"] = combined_estimated_targets

        except Exception as exc:
            print(f"Error processing paragraph {para_idx}: {exc}")
    
    def load_json_template(self, json_file_name):
        # Get the directory of the current script
        dir_path = os.path.dirname(__file__)
        
        # Construct the path to the JSON file relative to the current script's directory
        json_path = os.path.join(dir_path, '..', 'configs', json_file_name)
        
        # Normalize the path to resolve any '..'
        json_path = os.path.normpath(json_path)
        
        # Read the JSON file
        with open(json_path, 'r') as file:
            return json.load(file)
    
    def toggle_scene_number_entry(self):
        if self.adjust_text_button_var.get():
            self.scene_number_entry.grid_forget()
        else:
            self.scene_number_entry.grid(row=1, column=0, sticky="nsew", pady=2)

    def add_parameter_widget(self):
        frame = tk.LabelFrame(self.parameter_widgets_frame, text="Parameter Settings", padx=5, pady=5)
        frame.configure(borderwidth=2, relief="groove") 
        
        parameter_label = tk.Label(frame, text="Parameter:")
        parameter_types = [param['type'] for param in self.json_template['adjustment_parameters']]
        parameter = ttk.Combobox(frame, values=parameter_types, state="readonly")
        
        parameter_target_label = tk.Label(frame, text="Target:")
        parameter_target = ttk.Combobox(frame, state="readonly")
        estimated_target_label = tk.Label(frame, text="")
        
        # Function to update targets based on selected parameter type
        def on_parameter_selected(event):
            selected_type = parameter.get()
            
            for param in self.json_template['adjustment_parameters']:
                if param['type'] == selected_type:
                    parameter_target['values'] = param['targets']
                    parameter_target.current(0)  # Set the first target as the default selection
                    break

            # Iterate through estimated_targets_old_text to find the estimated target value
            for target_info in self.json_template["prompt_parameters"]["estimated_targets_old_text"]:
                if target_info['type'] == selected_type:
                    estimated_target_value = target_info['estimated_target']
                    estimated_target_label.config(text=f"Estimated {target_info['type']}: {estimated_target_value}")
                    break
        
        # Bind the parameter combobox selection event to the update_targets function
        parameter.bind('<<ComboboxSelected>>', on_parameter_selected)
        
        parameter_label.grid(row=0, column=0, sticky="w")
        parameter.grid(row=0, column=1)
        parameter_target_label.grid(row=1, column=0, sticky="w")
        parameter_target.grid(row=1, column=1)
        estimated_target_label.grid(row=2, column=0, columnspan=2)  # Span across both columns
        
        frame.pack(pady=5)
        self.parameter_widgets.append((parameter, parameter_target, estimated_target_label))

    def submit(self):

        gen_new_txt_image = True if self.generate_new_image_button_var.get() else False
        gen_old_txt_image = True if self.generate_old_image_button_var.get() else False

        adjust_entire_text = self.adjust_text_button_var.get()
        entire_text = str(self.text_viewer.get("1.0", "end-1c"))
        text_to_adjust = ""
        
        if not adjust_entire_text:
            scene_number = self.scene_number_entry.get()
            if scene_number.isdigit():
                scene_number = int(scene_number)
                text_to_adjust = get_scene_from_text(entire_text, scene_num=scene_number)
            else:
                messagebox.showerror("Error", "Please insert a scene number or choose all scenes")  # Fixed function call
                return  # Exit the function to prevent further execution
        else:
            scene_number = "None"
            text_to_adjust = entire_text

        # Construct the adjustments list
        adjustments = [{
            "type": param[0].get(), 
            "target": param[1].get()
        } for param in self.parameter_widgets if param[0].get() and param[1].get()]
        
        prompt_parameters = self.json_template["prompt_parameters"]
        prompt_parameters["entire_text"] = entire_text
        prompt_parameters["text_to_adjust"] = text_to_adjust
        prompt_parameters["user_adjustments"] = adjustments
        prompt_parameters["additional_instructions"] = "Maintain the core narrative and themes of the original text."

        self.json_template["prompt_parameters"] = prompt_parameters
        
         # Transition to DisplayPage with the updated json_template
        self.master.show_page("DisplayPage", json_template=self.json_template, gen_old_txt_image=gen_old_txt_image, gen_new_txt_image=gen_new_txt_image)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Text Viewer and Editor")
    main_frame = AdjustTextPage(root)
    main_frame.pack(fill="both", expand=True)
    root.geometry("800x600")
    root.mainloop()
