import sys
import os
import subprocess
import time

# Add project root to path (handle frozen PyInstaller environment vs normal script execution)
if getattr(sys, 'frozen', False):
    # In PyInstaller, main.py is placed at the root of the temporary bundle folder
    project_root = os.path.dirname(__file__)
else:
    # During development, main.py is in the 'app/' directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

def sync_ui():
    """Automatically re-compiles all .ui files in the project."""
    import glob
    ui_files = [f for f in glob.glob(os.path.join("**", "*.ui"), recursive=True)
                if not f.startswith("dist" + os.sep) and not f.startswith("build" + os.sep)]
    
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
if not getattr(sys, 'frozen', False):
    sync_ui()

try:
    from app.launcher import Launcher
except ModuleNotFoundError:
    try:
        from launcher import Launcher
    except ModuleNotFoundError:
        # Fallback to absolute path lookup if needed
        sys.path.insert(0, os.path.dirname(__file__))
        from launcher import Launcher

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
