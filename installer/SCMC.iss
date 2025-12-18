; SCMC (Star Citizen Merit Calculator) Installer Script
; Inno Setup 6 Script

#ifndef AppName
#define AppName "SCMC"
#endif
#ifndef AppNameLong
#define AppNameLong "SCMC (Star Citizen Merit Calculator)"
#endif
#ifndef AppVersion
  #define AppVersion "1.0.7"
#endif
#ifndef AppPublisher
#define AppPublisher "PINKgeekPDX"
#endif
#ifndef AppURL
  #define AppURL "http://www.scmc.space"
#endif
#ifndef AppRepoURL
  #define AppRepoURL "https://github.com/PINKgeekPDX/SCMeritsCalc"
#endif
#ifndef AppSupportURL
  #define AppSupportURL "https://github.com/PINKgeekPDX/SCMeritsCalc/issues"
#endif
#ifndef AppUpdatesURL
  #define AppUpdatesURL "https://github.com/PINKgeekPDX/SCMeritsCalc/releases"
#endif
#ifndef AppExeName
#define AppExeName "SCMC.exe"
#endif
#ifndef OutputBaseFilename
#define OutputBaseFilename "SCMC_Installer"
#endif

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppNameLong}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppSupportURL}
AppUpdatesURL={#AppUpdatesURL}
VersionInfoVersion={#AppVersion}.0
VersionInfoProductVersion={#AppVersion}.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppNameLong} Installer
VersionInfoProductName={#AppNameLong}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=
OutputDir=..\dist
OutputBaseFilename={#OutputBaseFilename}
SetupIconFile=..\assets\app-logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\SCMC.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\app-logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\assets\app-logo.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppNameLong}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\app-logo.ico"
Name: "{group}\{cm:UninstallProgram,{#AppNameLong}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; IconFilename: "{app}\app-logo.ico"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppNameLong}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
