import os
import subprocess

def add_to_path(new_path):
    # Extract the directory from the executable path
    new_path = os.path.dirname(new_path)

    # Get the current PATH environment variable
    current_path = os.environ.get("PATH", "")

    # Check if the new path is already in the PATH
    if new_path in current_path:
        print(f"The path '{new_path}' is already in the PATH.")
    else:
        # Add the new path to the system PATH using setx
        try:
            command = f'setx PATH "%PATH%;{new_path}"'
            subprocess.run(command, shell=True, check=True)
            print(f"Successfully added '{new_path}' to the PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to add path. Error: {e}")

# Path to your SQLite executable
sqlite_path = r"C:\Users\parla\OneDrive\Masaüstü\sqlite-tools-win-x64-3470000"

# Add it to the PATH
add_to_path(sqlite_path)
