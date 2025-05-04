[Setup]
AppName=MKV to MP4 Converter
AppVersion=1.0.1
AppId={{F3A17DA5-6B1E-4F3C-A3D9-C5F4E3718E1F}}
DefaultDirName={autopf}\MKV to MP4 Converter
DefaultGroupName=MKV to MP4 Converter
OutputDir=installer
OutputBaseFilename=MKVtoMP4Converter_Setup
Compression=lzma2/ultra64
SolidCompression=yes
InternalCompressLevel=ultra64
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4
LZMABlockSize=65536
LZMAAlgorithm=1
DiskSpanning=no
WizardStyle=modern
PrivilegesRequired=admin
MinVersion=10.0
SetupLogging=yes
UninstallDisplayIcon={app}\mkvtomp4.exe
AppPublisher=Yonatan Setbon
AppPublisherURL=https://sourceforge.net/projects/mkv-to-mp4-converter/
AppContact=Yonatan Setbon
AppCopyright=Copyright (C) 2025 Yonatan Setbon
VersionInfoCompany=Yonatan Setbon
VersionInfoCopyright=Copyright (C) 2025 Yonatan Setbon
VersionInfoVersion=1.0.1.0
AppSupportURL=https://sourceforge.net/projects/mkv-to-mp4-converter/
DisableProgramGroupPage=yes
DisableWelcomePage=yes
DisableFinishedPage=yes
AllowNoIcons=yes
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x86 x64
DisableDirPage=no
AllowCancelDuringInstall=yes
RestartIfNeededByRun=yes
AlwaysRestart=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
DiskSpaceMBLabel=At least 62 MB of free disk space is required.

[Files]
; Updated paths for onefile PyInstaller build
Source: "dist\mkvtomp4.exe"; DestDir: "{app}"; DestName: "mkvtomp4.exe"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}"; Permissions: users-full

[Icons]
Name: "{group}\MKV to MP4 Converter"; Filename: "{app}\mkvtomp4.exe"; IconFilename: "{app}\icon.ico"
Name: "{commondesktop}\MKV to MP4 Converter"; Filename: "{app}\mkvtomp4.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{group}\Uninstall MKV to MP4 Converter"; Filename: "{uninstallexe}"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\mkvtomp4.exe"; Description: "Launch MKV to MP4 Converter"; Flags: postinstall nowait skipifsilent unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: dirifempty; Name: "{app}"
Type: filesandordirs; Name: "{group}"
Type: dirifempty; Name: "{group}"

[Code]
var
  WelcomePage: TWizardPage;
  WelcomeLabel: TLabel;

procedure InitializeWizard();
begin
  WelcomePage := CreateCustomPage(wpWelcome, 'Welcome', 'Welcome to the MKV to MP4 Converter Setup Wizard');

  WelcomeLabel := TLabel.Create(WelcomePage);
  WelcomeLabel.Parent := WelcomePage.Surface;
  WelcomeLabel.Left := 10;
  WelcomeLabel.Top := 10;
  WelcomeLabel.Width := WelcomePage.SurfaceWidth - 20;
  WelcomeLabel.Height := WelcomePage.SurfaceHeight - 20;
  WelcomeLabel.AutoSize := False;
  WelcomeLabel.WordWrap := True;
  WelcomeLabel.Caption := 'This installer will guide you through the process of installing MKV to MP4 Converter on your computer.' + #13#10#13#10 +
                         'Publisher: Yonatan Setbon' + #13#10 +
                         'Contact: https://www.youtube.com/@YonatanSetbon' + #13#10 +
                         'Copyright: Copyright (C) May 4 2025 Yonatan Setbon' + #13#10#13#10 +
                         'Click "Next" to continue with the installation.';
end;

function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

function InitializeSetup(): Boolean;
var
  FreeDiskSpace: Cardinal;
  RequiredSpace: Cardinal;
begin
  Result := True;
  
  RequiredSpace := 406 * 1024 * 1024; // 406 MB in bytes

  
  
  // Existing logging
  Log('Starting installation...');
  if Is64BitInstallMode then
    Log('64-bit installation')
  else
    Log('32-bit installation');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    try
      Exec(ExpandConstant('{sys}\ie4uinit.exe'), '-show', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
    except
      Log('Failed to refresh icon cache');
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Clean up files only if they exist
    if DirExists(ExpandConstant('{app}')) then
      DelTree(ExpandConstant('{app}'), True, True, True);
      
    if DirExists(ExpandConstant('{group}')) then
      DelTree(ExpandConstant('{group}'), True, True, True);
    
    // Clean up user settings if needed
    if DirExists(ExpandConstant('{localappdata}\MKV to MP4 Converter')) then
      DelTree(ExpandConstant('{localappdata}\MKV to MP4 Converter'), True, True, True);
  end;
end;