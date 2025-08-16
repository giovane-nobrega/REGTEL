; Script de Instalação para a Aplicação REGTEL
; Compatível com Inno Setup 6.5.0+

[Setup]
AppId={{ba8811e7-e373-4b67-8cba-5a257d22b851}}
AppName=REGTEL - Plataforma de Registo de Ocorrências
AppVersion=1.0.0
AppPublisher=Sua Empresa
AppPublisherURL=https://www.suaempresa.com
AppContact=suporte@suaempresa.com
AppSupportURL=https://www.suaempresa.com/suporte
DefaultDirName={autopf}\REGTEL
DefaultGroupName=REGTEL
OutputBaseFilename=REGTEL_Installer_1.0.0
SetupIconFile=.\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes
PrivilegesRequired=admin
VersionInfoVersion=1.0.0.0
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\REGTEL.exe
UninstallDisplayName=REGTEL - Plataforma de Registo de Ocorrências
Uninstallable=yes
CreateUninstallRegKey=yes
AllowNoIcons=yes
DisableStartupPrompt=yes

[Files]
; --- App principal ---
Source: ".\dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs; Excludes: "*.log;*.tmp;*.bak;*.iss"

; --- Config do usuário (vai direto para AppData do usuário) ---
Source: ".\client_secrets.json"; DestDir: "{userappdata}\REGTEL"
Source: ".\service_account.json"; DestDir: "{userappdata}\REGTEL"

[InstallDelete]
Type: filesandordirs; Name: "{app}"

[Icons]
Name: "{group}\REGTEL"; Filename: "{app}\REGTEL.exe"
Name: "{autodesktop}\REGTEL"; Filename: "{app}\REGTEL.exe"; Tasks: desktopicon

[Tasks]
; Deixe marcado por padrão (sem Flags) ou use Flags: unchecked se quiser desmarcado por padrão
Name: "desktopicon"; Description: "Criar ícone no Ambiente de Trabalho"; GroupDescription: "Atalhos:"

[Run]
Filename: "{app}\REGTEL.exe"; Description: "Iniciar REGTEL"; Flags: nowait postinstall skipifsilent
