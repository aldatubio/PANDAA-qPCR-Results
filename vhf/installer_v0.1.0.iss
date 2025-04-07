; Script generated by the Inno Script Studio Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "EpiFocus Assistant"
#define MyAppNameNoSpaces "EpiFocusAssistant"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Aldatu Biosciences, Inc."
#define MyAppURL "http://www.aldatubio.com"
#define MyAppExeName "EpiFocusAssistant_v0.1.0.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{386A7145-AB0A-4EDB-B2E4-43169961A7EB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
LicenseFile=C:\Users\lucy\OneDrive - Aldatu Biosciences\Desktop\PANDAA qPCR Results\vhf\eula.txt
InfoBeforeFile=C:\Users\lucy\OneDrive - Aldatu Biosciences\Desktop\PANDAA qPCR Results\vhf\readme.txt
InfoAfterFile=C:\Users\lucy\OneDrive - Aldatu Biosciences\Desktop\PANDAA qPCR Results\vhf\readme.txt
OutputBaseFilename={#MyAppNameNoSpaces}_Installer_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 0,6.1

[Files]
Source: "C:\Users\lucy\OneDrive - Aldatu Biosciences\Desktop\PANDAA qPCR Results\vhf\dist\EpiFocusAssistant_v0.1.0.exe"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon
