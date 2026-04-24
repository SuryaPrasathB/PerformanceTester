import sys
import os
import subprocess
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def sync_ui():
    """Automatically re-compiles all .ui files in the project."""
    import glob
    ui_files = glob.glob(os.path.join("**", "*.ui"), recursive=True)
    
    for ui_path in ui_files:
        # Determine output path: same dir as .ui, but named ui_*.py
        base_dir = os.path.dirname(ui_path)
        filename = os.path.basename(ui_path)
        py_filename = f"ui_{filename.replace('.ui', '.py')}"
        py_path = os.path.join(base_dir.replace("resources" + os.sep, ""), py_filename)
        
        if os.path.exists(ui_path):
            if not os.path.exists(py_path) or os.path.getmtime(ui_path) > os.path.getmtime(py_path):
                try:
                    subprocess.run(["pyside6-uic", ui_path, "-o", py_path], check=True)
                except Exception as e:
                    print(f"Failed to sync {filename}: {e}")
sync_ui()

from app.launcher import Launcher

def main():
    """Entry point for the application."""
    try:
        launcher = Launcher()
        sys.exit(launcher.run())
    except Exception as e:
        import traceback
        print("\n" + "="*50)
        print("CRITICAL STARTUP ERROR:")
        print("="*50)
        traceback.print_exc()
        print("="*50 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
