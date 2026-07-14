Step 1 (Build the executable): Run pyinstaller pro_perf.spec in your terminal. This compiles the Python code and gathers the assets (including your new icon) into the dist\Pro-Perf\ directory.
Step 2 (Build the installer): Compile pro_perf_installer.iss using Inno Setup (ISCC). This packages everything in the dist\Pro-Perf\ directory into a single Pro-Perf-Setup.exe installer.
