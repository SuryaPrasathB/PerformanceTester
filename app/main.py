import sys
import os

# Add project root to path for absolute imports to work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.launcher import Launcher

def main():
    """Entry point for the application."""
    launcher = Launcher()
    sys.exit(launcher.run())

if __name__ == "__main__":
    main()
