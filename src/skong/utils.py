from .core import valid_dir
from pathlib import Path

def read_configurations(file_path: Path, configurations: list) -> None:
    """
    Reads all the configurations recursively from the given path and stores them in the provided list.
    Args:
        file_path (Path): The path to the directory containing the skong projects.
        configurations (list): A list to store the configurations.
    
    Returns:
        None: The function modifies the configurations list in place.
    """
    for item in file_path.iterdir():
        if item.is_file():
            continue
        elif item.is_dir():
            if valid_dir(item):
                configurations.append(item.absolute())
            else:
                read_configurations(item, configurations)