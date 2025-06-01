import json
import os

def read_nested_json_key(json_data, keys):
    current = json_data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def get_file_data(project_path):
    project_path = str(project_path).replace("\\", "/")
    file = open(project_path, "r")
    data = file.read()
    file.close()
    return data

def list_files_and_folders(directory):
    try:
        items = []
        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)
            if os.path.isdir(full_path):
                items.append(f"{entry} (folder)")
            else:
                items.append(f"{entry} (file)")
        return items
    except Exception as e:
        return [f"Error: {str(e)}"]