import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import time
import os
import json
from pathlib import Path
import subprocess
import sys
import shutil

import backend.backend # main backend python script


# Global Variables
selected_path = None
cmd = None
root = None
terminal_output = None
windowed_output = None
config_data = None
cmd_terminal = None
codeEditor = None
key_option = None
key_values = None
currentproject = None

selected_dir = None # path to current selected project root path

lang_options = ["Python(don't add ext)", "Java(don't add ext)" , "Custom(add ext)"]

# user created program variables
user_project_name = "No Project Selected" # project Name
project_open = False # weather a project is open or not

# Paths
current_path = Path.cwd()
script_dir = Path(__file__).parent
config = script_dir / "configuration" / "config.json"  # Config file path
backendMain_path = script_dir / "backend" / "backendMain.cpp"  # Backend path

originalProjectPath = None
projectpath = "" 
previousDirectory = ""  #

# initialize cmd running dir

def restart_prog(): # uses batch file to restart the program
    pid = os.getpid()  # Get current process ID
    script_path = os.path.abspath("restartProg.bat")
    subprocess.run([script_path, str(pid)], shell=True)
    sys.exit()  # Closes the current Python process

# Read config file
def read_config_file():
    with open(config, "r") as file:
        global config_data, project_open, projectpath
        config_data = json.load(file)  # Load JSON data into the global variable

        # sets project_open variable
        if config_data["user_program_properties"]["opened_directory"] != "":
            project_open = True
            projectpath = Path(config_data["user_program_properties"]["opened_directory"])

            with open(config, "w") as file:
                config_data["user_program_properties"]["project_opened"] = "True"
                json.dump(config_data, file, indent=4)
        if config_data["user_program_properties"]["project_opened"] == "False":
            projectpath = ""
            project_open = False
            with open(config, "w") as file:
                config_data["user_program_properties"]["project_opened"] = "False"
                json.dump(config_data, file, indent=4)

read_config_file()  # Initializes config_data variable with config data.

originalProjectPath = projectpath  # Store the original project path

def setup_terminals(option=None):
    if option != "pop":
        terminal_output.config(bg=config_data["terminal_output_settings"]["background_color"])
        terminal_output.config(fg=config_data["terminal_output_settings"]["text_color"])
        cmd_terminal.config(bg=config_data["terminal_input_settings"]["background_color"])
        cmd_terminal.config(fg=config_data["terminal_input_settings"]["text_color"])
    else:
        if windowed_output is not None and windowed_output.winfo_exists():
            windowed_output.config(bg=config_data["terminal_output_settings"]["background_color"])
            windowed_output.config(fg=config_data["terminal_output_settings"]["text_color"])
        
    
def write_to_terminal_output(text, option=None):
    # Get colors from config
    error_color = config_data['terminal_output_settings']['error_color']
    warning_color = config_data['terminal_output_settings']['warning_color']
    success_color = config_data["terminal_output_settings"]["success_color"]
    info_color = config_data["terminal_output_settings"]["info_color"]

    text = str(text)

    # Map option to actual color value
    color_map = {
        "E": error_color,
        "W": warning_color,
        "S": success_color,
        "I": info_color
    }

    # Use option as tag name and get corresponding color
    tag_name = option
    color = color_map.get(option, None)

    # Insert text safely into a widget
    def insert_text(widget, tag_name=None, fg_color=None):
        if widget is not None and widget.winfo_exists():
            widget.config(state=tk.NORMAL)
            if tag_name and fg_color:
                widget.tag_configure(tag_name, foreground=fg_color)
                widget.insert(tk.END, text + '\n', tag_name)
            else:
                widget.insert(tk.END, text + '\n')
            widget.config(state=tk.DISABLED)
            widget.see(tk.END)

    # Output to both terminals
    insert_text(terminal_output, tag_name, color)
    insert_text(windowed_output, tag_name, color)



def reset_terminals():
    terminal_output.config(state=tk.NORMAL)
    terminal_output.delete(1.0, tk.END)
    terminal_output.config(state=tk.DISABLED)

    output_default_text = config_data["terminal_output_settings"]["defualt_text"]
    write_to_terminal_output(output_default_text)

    if config_data["user_program_properties"]["project_opened"] == "False":
        write_to_terminal_output("\nNo Project Opened Create or Open a Project.", "W")
        write_to_terminal_output(f"\nType Command 'openterm' To Open Terminal In Bigger Window!", "I")
    else:
        write_to_terminal_output(f"\nCurrent Directory: {projectpath}", "I")
        write_to_terminal_output(f"\nType Command 'openterm' To Open Terminal In Bigger Window!", "I")

    cmd_terminal.delete(1.0, tk.END)

def initializeProject(projName, language, projDirectory):
    # Creates and loads project files     
    global project_open, user_project_name
    user_project_name = f"Current Project: {projName}"
    
    # Extract file extension from language option
    file_extension = ""
    if language == "Python(don't add ext)":
        file_extension = "py"
    elif language == "Java(don't add ext)":
        file_extension = "java"
    else:  # Custom - extension should be included in the project name
        file_extension = ""  # Let the user specify the extension in the project name
    
    # Get placeholder code if available
    placeholder_code = ""
    if file_extension in config_data["default_code_placeholders"]:
        placeholder_code = config_data["default_code_placeholders"][file_extension]
    
    # Create project file with appropriate extension
    file_name = f"{projName}.{file_extension}" if file_extension else projName
    project_file_path = Path(projDirectory) / file_name
    
    try:
        with open(project_file_path, "w") as file:
            if placeholder_code:
                file.write(placeholder_code)
            else:
                file.write("")
        populate_file_explorer()  # Refresh the file explorer with the new project file
        write_to_terminal_output(f"Created File: {file_name}", "S")
    except Exception as e:
        write_to_terminal_output(f"Error creating File: {str(e)}", "E")

def create_project():
    # Creates a new project
    global selected_dir
    
    # Initialize selected_dir if it's None
    if selected_dir is None:
        selected_dir = os.path.expanduser("~")  # Default to home directory
    
    window = tk.Toplevel(root)
    window.title("Create New File")
    window.geometry("325x370")
    window.resizable(False, False)
    window.attributes('-topmost', 'true')
    
    window_title = tk.Label(window, text="Create New File", font=("Arial", 12))
    window_title.pack()
    
    label_frame1 = tk.LabelFrame(window, text="File Name")
    label_frame1.pack(fill=tk.X, padx=5, pady=5)
    
    project_name = tk.Text(label_frame1, height=1)
    project_name.pack(fill=tk.X, padx=5, pady=5)
    
    label_frame2 = tk.LabelFrame(window, text="File Language")
    label_frame2.pack(fill=tk.X, padx=5, pady=5)
    
    option_menu = ttk.Combobox(label_frame2, values=lang_options, state="readonly")
    option_menu.set(lang_options[0])
    option_menu.pack()
    
    label_frame3 = tk.LabelFrame(window, text="Select Directory To Store File")
    label_frame3.pack(fill=tk.X, padx=5, pady=5)
    
    global dir_
    dir_ = tk.Label(label_frame3, text=f"Dir: {selected_dir}")
    dir_.pack()
    
    def select_dir_for_project():
        global selected_dir
        directory = filedialog.askdirectory(title="Select Directory")
        if directory:
            selected_dir = directory
            dir_.config(text=f"Dir: {selected_dir}")
    
    directory_btn = tk.Button(label_frame3, text="Select Directory", command=select_dir_for_project)
    directory_btn.pack(fill=tk.X, pady=5, padx=5)
    
    label_frame4 = tk.LabelFrame(window, text="Info")
    label_frame4.pack(fill=tk.X, padx=5, pady=5)
    
    subtext1 = tk.Label(label_frame4, text="Python and Java Files's will have default code\ncustom Files's will be blank")
    subtext1.pack()
    
    subtext2 = tk.Label(label_frame4, text="(will create folder with file name in specified directory)")
    subtext2.pack()
    
    info_lbl = tk.Label(label_frame4, text="You Can Modify Default Code Structure In Settings\n(For Select Langs)")
    info_lbl.pack()
    
    def on_create_button_click():
        try:
            proj_name = project_name.get("1.0", tk.END).strip()
            if not proj_name:
                messagebox.showerror("Error", "File name cannot be empty")
                return
            
            if selected_dir is None or not os.path.exists(selected_dir):
                messagebox.showerror("Error", "Please select a valid directory")
                return
                
            project_file = initializeProject(proj_name, option_menu.get(), selected_dir)
            if project_file:
                window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create file: {str(e)}")
    
    create_project_btn = tk.Button(
        label_frame4, 
        text="Create Project",
        command=on_create_button_click,
        background="Green",
        foreground="Black"
    )
    create_project_btn.pack(fill=tk.X, padx=5, pady=5)

def select_dir_explorer():
    global selected_dir, projectpath
    directory = filedialog.askdirectory(title="Select Directory")
    if directory:
        selected_dir = Path(directory)
        write_to_terminal_output(f"Selected Directory: {selected_dir}", "S")

        with open(config, "w") as file:
            config_data["user_program_properties"]["opened_directory"] = str(selected_dir).replace("\\", "/")
            json.dump(config_data, file, indent=4)
        write_to_terminal_output(f"Saved Directory: {selected_dir}", "S")
        projectpath = selected_dir  # Update the project path to the selected folder.
        populate_file_explorer()  # Refresh the file explorer with the folder's contents
        cmd_clear() # clears the terminal output
        write_to_terminal_output(f"Selected Directory: {selected_dir}", "S")

def first_open():  # runs on user first open
    messagebox.showinfo("Welcome To SolarIDE!", "This is a light weight IDE made in Python\nThis was made as a personal project but can be used to make any kind of project if you're willing.")

# Command implementations
def cmd_help(): # prints all commands in CMD
    write_to_terminal_output("Commands:")
    for command, description in config_data.get("cmd_commands", {}).items():
        write_to_terminal_output(f"{command} - {description}", "I")

def cmd_clear(): # clears the terminal to the default text
    reset_terminals()

def cmd_exit(): # exits the IDE
    if messagebox.askyesno("Exit SolarIDE", "Are you sure you want to exit? Make sure your work is saved."):
        os._exit(0)
    else:
        write_to_terminal_output("Exit Operation Cancelled.", "W")

def cmd_createproject(): # opens window to create new project
    create_project()

def last_dir():  # Goes back to the previous directory
    global projectpath, previousDirectory
    if previousDirectory and Path(previousDirectory).exists():
        projectpath = Path(previousDirectory)
        previousDirectory = str(projectpath.parent)  # Update previousDirectory to the parent of the current path
        populate_file_explorer()
        write_to_terminal_output(f"Moved back to: {projectpath}", "S")
    elif projectpath != originalProjectPath and originalProjectPath.exists():
        previousDirectory = str(projectpath)  # Save the current path as the previous directory
        projectpath = originalProjectPath  # Reset to the original project path
        populate_file_explorer()
        write_to_terminal_output(f"Moved back to original project path: {projectpath}", "S")
    else:
        write_to_terminal_output("No previous directory to go back to.", "W")

def openProject(event):
    global file_explorer_listbox, project_open, user_project_name, currentproject, projectpath, previousDirectory, selected_path

    selected_item = file_explorer_listbox.get(file_explorer_listbox.curselection())
    selected_path = projectpath / selected_item.split(" (")[0]  # Remove "(file)" or "(folder)" from the label

    if selected_path.is_file():  # If the selected path is a file
        write_to_terminal_output(f"Opening File: {selected_item}", "S")
        currentproject.config(text=f"Current Project: {selected_item}")
        # Specify encoding when reading the file
        with open(selected_path, "r", encoding="latin-1") as file:
            file_contents = file.read()
        codeEditor.delete(1.0, tk.END)  # Clear the code editor
        codeEditor.insert(tk.END, file_contents)  # Insert file contents into the code editor
        project_open = True
        user_project_name = f"Current Project File: {selected_item}"
    elif selected_path.is_dir():  # If the selected path is a folder
        write_to_terminal_output(f"Opening Folder: {selected_item}", "S")
        previousDirectory = str(projectpath)
        projectpath = selected_path  # Update the project path to the selected folder.
        populate_file_explorer()  # Refresh the file explorer with the folder's contents
    else:
        write_to_terminal_output(f"Error: {selected_item} is not a valid file or folder!", "E")

def populate_file_explorer():  # Populates file explorer with all files and folders in the current project directory.
    global file_explorer_listbox, projectpath

    file_explorer_listbox.delete(0, tk.END)  # Clear the listbox before populating

    if projectpath == "":
        write_to_terminal_output("No Project Opened Or No Project Directory Opened!", "E")
        return

    try:
        # Use the backend function to list files and folders with labels
        items = backend.backend.list_files_and_folders(str(projectpath))
        for item in items:
            file_explorer_listbox.insert(tk.END, item)
        file_explorer_listbox.bind("<Double-1>", openProject)  # Bind double-click to openProject
    except Exception as e:
        write_to_terminal_output(f"Error populating file explorer: {str(e)}", "E")

def setup_fileExploror(): # set's up file explorer.
    global file_explorer, file_explorer_listbox, projectpath, project_open

    file_explorer = tk.Frame(root, bg="grey", width=250, height=600)
    file_explorer.pack(side=tk.LEFT)
    file_explorer.pack_propagate(False)

    options_frame = tk.Frame(file_explorer, bg="lightgrey", width=225, height=45)
    options_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

    goBackBTN = tk.Button(options_frame, text="Go Back", command=last_dir, foreground="Red")
    goBackBTN.pack(padx=23)
    goBackBTN.config(width=15)

    select_dir_create_btn = tk.Button(options_frame, text="Select Directory", command=select_dir_explorer)
    select_dir_create_btn.pack(padx=23)

    # File Explorer Title (Regular Label)
    file_explorer_title = tk.Label(file_explorer, text="File Explorer",
                                   bg="lightgrey", fg="black",
                                   borderwidth=2, relief=tk.RIDGE,
                                   height=2)
    file_explorer_title.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # File explorer scrollbar
    file_explorer_scrollbar = ttk.Scrollbar(file_explorer, orient=tk.VERTICAL)
    file_explorer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # File Explorer Listbox
    file_explorer_listbox = tk.Listbox(file_explorer, yscrollcommand=file_explorer_scrollbar.set)
    file_explorer_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    file_explorer_scrollbar.config(command=file_explorer_listbox.yview)

    # add content to file explorer listbox
    populate_file_explorer()

def cmd_list(): # lists all files in project
    try:
        directory = str(config_data["user_program_properties"]["opened_directory"])
        if not os.path.exists(directory):
            write_to_terminal_output("Error: Directory does not exist.", "E")
            return

        items = backend.backend.list_files_and_folders(directory)
        for item in items:
            write_to_terminal_output(item, "I")
    except PermissionError:
        write_to_terminal_output("Error: Permission denied.", "E")
    except Exception as e:
        write_to_terminal_output(f"Error: {str(e)}", "E")

def reset_editor(): # initializes the code editor
    global codeEditor, project_open
    background_color = config_data["editorSettings"]["background_color"]
    text_color = config_data["editorSettings"]["text_color"]
    default_text = config_data["editorSettings"]["editor_default_text"]

    codeEditor.delete(1.0, tk.END)
    codeEditor.config(background=background_color, foreground=text_color, borderwidth=5)
    if not project_open: # if true then display code
        codeEditor.insert(tk.END, f"{default_text}")

    write_to_terminal_output("Cleared Text Editor", "S")

def populate_key_options():
    try:
        with open(config, "r") as file:
            data = json.load(file)  # Load JSON data
            key_option["values"] = list(data.keys())  # Set combobox values
            key_option.set("Select A Key")  # Default selection
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load config file: {str(e)}")

def grab_key(event=None):
    selected_key = key_option.get()
    
    if selected_key == "Select A Key":
        return
        
    try:
        # Update label to show which key is selected
        key_values.config(text=f"Displaying Values From Key: {selected_key}")
        
        # Get the current value from config file
        with open(config, "r") as file:
            data = json.load(file)
            
        # Check if key exists
        if selected_key in data:
            current_value = data[selected_key]
            
            # Clear the text widget
            text_widget.delete(1.0, tk.END)
            
            # Format dictionaries and lists as proper JSON
            if isinstance(current_value, (dict, list)):
                formatted_value = json.dumps(current_value, indent=4)
                text_widget.insert(tk.END, formatted_value)
            else:
                # Insert current value into text widget
                text_widget.insert(tk.END, str(current_value))
        else:
            messagebox.showwarning("Warning", f"Key '{selected_key}' not found in config")
    except Exception as e:
        messagebox.showerror("Error", f"Error retrieving value: {str(e)}")

def saveChanges():
    selected_key = key_option.get()
    
    if selected_key == "Select A Key" or not selected_key:
        messagebox.showinfo("Info", "Please select a key first")
        return
        
    try:
        # Get the new value from text widget
        new_value_text = text_widget.get(1.0, tk.END).strip()
        
        # Load current config
        with open(config, "r") as file:
            data = json.load(file)
        
        # Navigate to the original value
        parts = selected_key.split(".")
        target = data
        for part in parts[:-1]:
            if part not in target:
                messagebox.showerror("Error", f"Key '{selected_key}' not found in config.")
                return
            target = target[part]
        
        key_to_update = parts[-1]
        if key_to_update not in target:
            messagebox.showerror("Error", f"Key '{selected_key}' not found in config.")
            return
        
        original_value = target[key_to_update]
        
        # Type conversion based on original value
        if isinstance(original_value, bool):
            new_value = new_value_text.lower() in ('true', 'yes', '1', 'y')
        elif isinstance(original_value, int):
            try:
                new_value = int(new_value_text)
            except ValueError:
                messagebox.showerror("Error", "Invalid integer format. Please enter a valid number.")
                return
        elif isinstance(original_value, float):
            try:
                new_value = float(new_value_text)
            except ValueError:
                messagebox.showerror("Error", "Invalid float format. Please enter a valid number.")
                return
        elif isinstance(original_value, dict):
            try:
                new_value = json.loads(new_value_text)
                if not isinstance(new_value, dict):
                    messagebox.showerror("Error", "Value must be a dictionary. Please check your input.")
                    return
            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Invalid JSON format: {str(e)}")
                return
        elif isinstance(original_value, list):
            try:
                new_value = json.loads(new_value_text)
                if not isinstance(new_value, list):
                    new_value = [new_value]
            except json.JSONDecodeError:
                new_value = [item.strip() for item in new_value_text.split(',')]
        else:
            new_value = new_value_text
        
        # Update the value in the data
        target[key_to_update] = new_value
        
        # Save the updated config
        with open(config, "w") as file:
            json.dump(data, file, indent=4)
            
        messagebox.showinfo("Success", f"Value for '{selected_key}' has been updated")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save changes: {str(e)}")

def settings():
    global key_option, key_values, text_widget
    
    # Create settings window
    window = tk.Toplevel(root)
    window.title("Config Settings Editor GUI")
    window.geometry("600x370")
    window.resizable(False, False)
    window.attributes('-topmost', 'true')
    
    # Top frame - keeping similar to original
    topframe = tk.Frame(window, background="grey", height=75)
    topframe.pack(fill=tk.X, padx=3, pady=3)
    
    text1 = tk.Label(topframe, text="Config Settings Editor GUI", font=("Arial", 20, "bold"), background="grey")
    text1.pack(fill=tk.X)
    
    # Main content frame - keeping grey color from original
    frame1 = tk.Frame(window, background="gray58", width=600, height=325)
    frame1.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
    
    # Label frame for key selection - keeping similar to original
    label_frame1 = tk.LabelFrame(frame1, text="Select Key To Modify", background="white")
    label_frame1.pack(fill=tk.X, pady=5, padx=5)
    
    # Combo box - with slight improvements
    key_option = ttk.Combobox(label_frame1, state="readonly", width=50)
    key_option.pack(padx=5, pady=5, fill=tk.X)
    key_option.bind("<<ComboboxSelected>>", grab_key)
    
    # Label frame for displaying selected key
    label_frame2 = tk.LabelFrame(frame1, text="Selected Key Info", background="white")
    label_frame2.pack(fill=tk.X, padx=5, pady=5)
    
    # Display selected key - using your original approach
    key_values = tk.Label(label_frame2, text="No Key Selected", background="white", anchor="w")
    key_values.pack(padx=5, pady=5, fill=tk.X)
    
    # Label frame for editing values
    label_frame3 = tk.LabelFrame(frame1, text="Edit Values Box", background="white")
    label_frame3.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Frame for text widget and scrollbar
    text_frame = tk.Frame(label_frame3, background="white")
    text_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Text widget
    text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, wrap="word", height=8)
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Attach scrollbar
    scrollbar.config(command=text_widget.yview)
    
    # Button frame for save functionality
    button_frame = tk.Frame(frame1, background="gray58")
    button_frame.pack(fill=tk.X, pady=5, padx=5)
    
    # Save button
    save_button = tk.Button(
        button_frame,
        text="Save Changes",
        background="#4CAF50",
        foreground="white",
        font=("Arial", 10, "bold"),
        padx=10,
        pady=3,
        command=saveChanges
    )
    save_button.pack(side=tk.RIGHT, padx=5)
    
    # Exit Button
    exit_button = tk.Button(
        button_frame,
        text="Close",
        background="#F44336",
        foreground="white",
        font=("Arial", 10, "bold"),
        padx=10,
        pady=3,
        command=window.destroy
    )
    exit_button.pack(side=tk.RIGHT, padx=5)

    restartBTN = tk.Button(
        button_frame,
        text="Restart Prog",
        background="#2196F3",
        foreground="white",
        font=("Arial", 10, "bold"),
        padx=10,
        pady=3,
        command=restart_prog
    )
    restartBTN.pack(side=tk.RIGHT, padx=5)

    # Text
    text = tk.Label(button_frame, text="RESTART AFTER MAKING CHANGES!", font=("Arial", 8, "bold"))
    text.pack(side=tk.LEFT, padx=5)
    text.config(foreground="black", background="gray58")
    
    # Populate the combobox with keys from the config file
    populate_key_options()    

def openTerm():
    global windowed_output

    term_window = tk.Toplevel(root)
    term_window.title("Terminal")
    term_window.geometry("800x600")
    term_window.configure(bg="black")

    windowed_output = tk.Text(
        term_window, height=30, width=100, bg="black", fg="white",
        borderwidth=2, insertbackground="white", padx=5, pady=5
    )
    windowed_output.pack(side="top", fill="both", expand=True)

    setup_terminals("pop")

    def on_close():
        global windowed_output
        windowed_output = None
        term_window.destroy()

    term_window.protocol("WM_DELETE_WINDOW", on_close)
    term_window.attributes('-topmost', True)
    cmd_clear()

def rmproject():
    global project_open, user_project_name, projectpath, currentproject
    window = tk.Toplevel(root)
    window.title("Remove Project")
    window.geometry("325x350")
    window.resizable(False, False)
    window.attributes('-topmost', 'true')
    
    t = tk.Label(window, text="Remove File", font=("Arial", 12, "bold"))
    t.pack()

    frame1 = tk.LabelFrame(window, text="File To Remove")
    frame1.pack(fill=tk.X, padx=5, pady=5)

    frame1Text = tk.Label(frame1, text="Select File To Remove")
    frame1Text.pack(fill=tk.X, padx=5, pady=5)

    frame1directory = tk.Label(frame1, text="No File Selected")
    frame1directory.pack(fill=tk.X, padx=5, pady=5)

    selected_file = [None]

    def delete_file(file_path, window):
        if file_path and file_path.exists():
            try:
                if file_path.is_file():
                    file_path.unlink()  # Delete the file
                    write_to_terminal_output(f"File '{file_path.name}' deleted successfully.", "S")
                elif file_path.is_dir():
                    shutil.rmtree(file_path)  # Delete the directory and its contents
                    write_to_terminal_output(f"Directory '{file_path.name}' deleted successfully.", "S")
                else:
                    write_to_terminal_output(f"'{file_path.name}' is neither a file nor a directory.", "E")
            except Exception as e:
                write_to_terminal_output(f"Error deleting '{file_path.name}': {str(e)}", "E")
        else:
            write_to_terminal_output("No valid file or directory selected for deletion.", "W")
        
        window.destroy()
        populate_file_explorer()

    def update_info():
        if selected_file[0] and selected_file[0].exists():
            frame2Text.config(text=f"File Information\nFull Path: {selected_file[0]}\n" \
                                   f"File Name: {selected_file[0].name}\n" \
                                   f"File Size: {selected_file[0].stat().st_size} bytes\n" \
                                   f"File Type: {selected_file[0].suffix}")

    def sel_directory():
        file = filedialog.askopenfilename(title="Select File To Remove")
        if file:
            selected_file[0] = Path(file)
            frame1directory.config(text=f"Selected File: {selected_file[0].name}")
            update_info()
        else:
            selected_file[0] = None
            frame1directory.config(text="No File Selected")

    frame1Button = tk.Button(frame1, text="Select File", command=sel_directory)
    frame1Button.pack(fill=tk.X, padx=5, pady=5)

    frame2 = tk.LabelFrame(window, text="Info")
    frame2.pack(fill=tk.X, padx=5, pady=5)
    frame2Text = tk.Label(frame2, 
                          text=f"File Information\nFull Path: {selected_file[0] if selected_file[0] else 'None'}" \
                          f"\nFile Name: {selected_file[0].name if selected_file[0] else 'None'}" \
                          f"\nFile Size: {selected_file[0].stat().st_size if selected_file[0] else 'None'} bytes" \
                          f"\nFile Type: {selected_file[0].suffix if selected_file[0] else 'None'}")
    frame2Text.pack(fill=tk.X, padx=5, pady=5)

    delete_button = tk.Button(window, text="Delete File!", command=lambda: delete_file(selected_file[0], window), foreground="black", background="green", borderwidth=2)
    delete_button.pack(fill=tk.X, padx=5, pady=5)


# Command registry
command_registry = {
    "help": cmd_help,
    "openterm": openTerm,
    "list": cmd_list,
    "clear": cmd_clear,
    "exit": cmd_exit,
    "openconfig": settings,
    "createfile": create_project,
    "rmfile": rmproject,
    "reset": reset_terminals,
    "cleareditor": reset_editor
}

def execute_powershell_command(command):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "backend", "PowershellCommand.ps1")

    # Optional: Check if file exists
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"PowerShell script not found at: {script_path}")

    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path, "-Command", command],
        capture_output=True,
        text=True
    )
    return result

def execute_commands(command):
    if not command:
        write_to_terminal_output("Syntax Error: No Command Entered.", "W")
        return
        
    write_to_terminal_output(f"Executing Command: {command}")
    
    # Look up and execute the command if found
    if command in command_registry:
        command_registry[command]()
        write_to_terminal_output(f"Command '{command}' executed successfully.", "S")
    elif command not in config_data["cmd_commands"]: # checks if command is a system command if not return error
        write_to_terminal_output(f"\nCommand Not Recognized By Program Attempting To Run System Command.", "S")

        result = execute_powershell_command(command)

        if result.returncode != 0:
            write_to_terminal_output(f"\nPowershell Error: {result.stderr}", "E")
            write_to_terminal_output(f"If You Need Help Please Use Command 'help'.")
        else:
            write_to_terminal_output(f"Powershell Response: \n{result.stdout}", "S")

        

def process_command(event):
    command = cmd_terminal.get("1.0", tk.END).strip()
    cmd_terminal.delete("1.0", tk.END)
    
    execute_commands(command)
    return "break"  # Prevents Tkinter from adding a newline on Enter

def save_code():
    global codeEditor, project_open, user_project_name, selected_path
    write_to_terminal_output(f"\nSaving Code To File {selected_path}...", "I")

    with open(selected_path, "w") as file:
        code_content = codeEditor.get("1.0", tk.END).strip()
        file.write(code_content)
    write_to_terminal_output(f"\nCode Saved To File: {selected_path}", "S")
    
def main():
    global root, terminal_output, cmd_terminal, codeEditor_frameBK, currentproject

    # Check if it's the first time running the app before initializing the main window
    if config_data["settings"]["first_open"] == "True":
        first_open()  # Open the first-time setup window

    root = tk.Tk()
    root.title("SolarIDE")
    root.geometry("1250x800")
    root.configure(bg="white")
    root.resizable(False, False)

    # Terminal and Output Frame Container
    bottom_frame = tk.Frame(root)
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

    # CMD Frame
    cmd_frame = tk.LabelFrame(bottom_frame, text="Terminal Input", padx=5, pady=5)
    cmd_terminal = tk.Text(cmd_frame, height=10, width=80, bg="black", fg="white", # terminal input text box
                           borderwidth=2, insertbackground="white", padx=5, pady=5)
    cmd_terminal.pack()
    cmd_frame.pack(side=tk.LEFT, padx=5, pady=5)

    # Terminal Output Frame
    terminal_output_frame = tk.LabelFrame(bottom_frame, text="Terminal Output", padx=5, pady=5)
    terminal_output = tk.Text(terminal_output_frame, height=10, width=80, bg="black", fg="white",
                              borderwidth=2, insertbackground="white", padx=5, pady=5)
    terminal_output.pack()
    terminal_output_frame.pack(side=tk.LEFT, padx=5, pady=5)
    terminal_output.config(state=tk.DISABLED)

    # Call setup_terminals() here after terminal_output is initialized
    setup_terminals()

    # QuickMenu Frame
    quick_frame = tk.LabelFrame(root, text="QuickMenu", padx=2, pady=2, height=55)
    quick_frame.pack_propagate(False)  # Prevent resizing to fit children

    new_project_btn = tk.Button(quick_frame, text="New File",
                                command=create_project)
    run_code_btn = tk.Button(quick_frame, text="Save Code",
                            command=save_code)
    open_config_file = tk.Button(quick_frame, text="Open Settings",
                                command=settings)
    currentproject = tk.Label(quick_frame, text=f"Current Project: {user_project_name}",
                            bg="black", fg="white")
    remove_project_btn = tk.Button(quick_frame, text="Remove File",
                                   command=rmproject)

    # Arrange buttons and label with exactly 5px horizontal spacing
    new_project_btn.grid(row=0, column=0, padx=5, pady=0)
    remove_project_btn.grid(row=0, column=1, padx=5, pady=0)
    run_code_btn.grid(row=0, column=2, padx=5, pady=0)
    open_config_file.grid(row=0, column=3, padx=5, pady=0)
    currentproject.grid(row=0, column=4, padx=5, pady=0)

    quick_frame.pack(side=tk.TOP, padx=3, pady=3, fill=tk.X)
    quick_frame.grid_columnconfigure(0, weight=1)
    quick_frame.grid_columnconfigure(1, weight=1)
    quick_frame.grid_columnconfigure(2, weight=1)
    quick_frame.grid_columnconfigure(3, weight=1)
    quick_frame.grid_columnconfigure(4, weight=1)

    # File Explorer Setup
    setup_fileExploror()

    # Frame And Sidebar
    white_side = tk.Frame(root, height=200, width=54, background="white")
    white_side.pack(side=tk.RIGHT, fill=tk.Y)

    # Scrollbar for Text Widget
    scrollbar = ttk.Scrollbar(white_side, orient="vertical")
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Initialize Code Editor (Inside a Frame for Proper Layout)
    text_frame = tk.Frame(root)
    text_frame.pack(fill=tk.BOTH, expand=True)

    global codeEditor
    codeEditor = tk.Text(text_frame, height=40, width=200, yscrollcommand=scrollbar.set)
    
    # Link Scrollbar to Text Widget
    scrollbar.config(command=codeEditor.yview)
    # Sets up the code editor
    reset_editor()
    codeEditor.pack(padx=1, pady=1, fill=tk.BOTH, expand=True)

    # Actual Code
    reset_terminals()  # Initializes terminal output

    # Show welcome message (only if it's the first open)
    if config_data["settings"]["first_open"] == "True":
        
        config_data["settings"]["first_open"] = "False"  # Mark that first open has been completed
        # Save updated config data back to the file
        with open(config, 'w') as file:
            json.dump(config_data, file, indent=4)

    # Force focus back to main window after messagebox
    root.lift()
    root.focus_force()

    root.update_idletasks()  # Force focus update

    # Capture enter key to process commands entered in the input terminal
    cmd_terminal.bind("<Return>", process_command)

    root.mainloop()

if __name__ == "__main__":
    main()