[Setup]
AppName=MissAV Downloader
AppVersion=4.0
DefaultDirName={autopf}\MissAV Downloader
DefaultGroupName=MissAV Downloader
UninstallDisplayIcon={app}\MissAV_Downloader.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=MissAV_Downloader_Setup
; SetupIconFile=locales\logo.ico

[Files]
Source: "dist\MissAV_Downloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\MissAV Downloader"; Filename: "{app}\MissAV_Downloader.exe"
Name: "{commondesktop}\MissAV Downloader"; Filename: "{app}\MissAV_Downloader.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\MissAV_Downloader.exe"; Description: "Launch MissAV Downloader"; Flags: nowait postinstall skipifsilent
