; Inno Setup Script for Pro-Perf application
; Defines parameters for the Windows Installer

[Setup]
AppId={{5D8B8497-2DF0-4FA9-A1B9-724FE35FCE99}}
AppName=Pro-Perf
AppVersion=1.0.0
AppPublisher=L S Control Systems
DefaultDirName={autopf}\Pro-Perf
DefaultGroupName=Pro-Perf
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=Pro-Perf-Setup
SetupIconFile=ui\resources\icons\app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\Pro-Perf\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "configs\*"; DestDir: "{app}\configs"; Flags: ignoreversion recursesubdirs createallsubdirs onlyifdoesntexist

[Icons]
Name: "{group}\Pro-Perf"; Filename: "{app}\Pro-Perf.exe"
Name: "{autodesktop}\Pro-Perf"; Filename: "{app}\Pro-Perf.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Pro-Perf.exe"; Description: "{cm:LaunchProgram,Pro-Perf}"; Flags: nowait postinstall skipifsilent
