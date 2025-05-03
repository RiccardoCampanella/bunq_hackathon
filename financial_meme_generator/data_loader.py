# financial_meme_generator/data_loader.py
import json
import os

def load_json_data(base_path, json_files):
    """
    Load JSON data from multiple files.
    
    Args:
        base_path (str): Base path to JSON files
        json_files (list): List of JSON filenames
        
    Returns:
        dict: Dictionary of loaded JSON data
    """
    json_data = {}
    for json_file in json_files:
        with open(os.path.join(base_path, json_file), 'r', encoding='utf-8') as f:
            json_data[json_file] = json.load(f)
    return json_data

def inspect_json(json_data):
    """
    Inspect and print structure of JSON data.
    
    Args:
        json_data (dict): Dictionary of loaded JSON data
    """
    for key, value in json_data.items():
        print(f'{key}:')
        if isinstance(value, list):
            print(f'  Number of items: {len(value)}')
            if len(value) > 0:
                print(f'  First item keys: {list(value[0].keys())}')
                for k, v in value[0].items():
                    if isinstance(v, dict):
                        print(f'    {k}: {list(v.keys())}')
                    elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                        print(f'    {k} (list): {list(v[0].keys())}')
        elif isinstance(value, dict):
            print(f'  Number of keys: {len(value)}')
            if len(value) > 0:
                print(f'  Keys: {list(value.keys())}')
        else:
            print(f'  Type: {type(value)}')
        print()
