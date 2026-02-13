import logging
import json
import yaml

def setup_logging(config_path: str = "config.yaml"):
    """
    Sets up logging configuration.
    """
    # TODO: Load config and setup logging
    pass

def load_config(config_path: str = "config.yaml") -> dict:
    """
    Loads configuration from a YAML file.
    
    Args:
        config_path (str): Path to the YAML configuration file.
        
    Returns:
        dict: The configuration dictionary.
    """
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def save_json(data: dict, filepath: str):
    """
    Saves a dictionary to a JSON file.
    
    Args:
        data (dict): The data to save.
        filepath (str): The output file path.
    """
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
