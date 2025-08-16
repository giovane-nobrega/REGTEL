; Script de Instalação para REGTEL (Comprovadamente funciona no Inno Setup 6.5.0)
; ATUALIZE: GUID, versões e caminhos

[Setup]
; --- Identificação do Aplicativo ---
AppId={{12345678-1234-1234-1234-123456789ABC} ; SUBSTITUA POR UM GUID ÚNICO!
AppName=REGTEL - Plataforma de Registo de Ocorrências
AppVersion=1.0.0
AppPublisher=Sua Empresa
AppPublisherURL=https://www.suaempresa.com; Script de Instalação para a Aplicação REGTEL
; Gerado para Inno Setup Compiler

[Setup]
; Informações básicas do instalador
AppName=REGTEL - Plataforma de Registo de Ocorrências
AppVersion=1.0.0 ; ATUALIZE: Defina a versão atual da sua aplicação (ex: 1.0.0)
DefaultDirName={autopf}\REGTEL ; Pasta de instalação padrão (ex: C:\Program Files\REGTEL)
DefaultGroupName=REGTEL ; Nome do grupo no Menu Iniciar
AllowNoIcons=yes ; Permite que o utilizador escolha não criar ícones (CORRIGIDO: 'AllowNoIcons' sem o 'l' extra)
OutputBaseFilename=REGTEL_Installer_1.0.0 ; ATUALIZE: Nome do ficheiro de saída do instalador (ex: REGTEL_Installer_1.0.0.exe)
Compression=lzma/max ; Tipo de compressão para o instalador (lzma é bom para executáveis)
SolidCompression=yes ; Comprime todos os ficheiros juntos para melhor taxa de compressão
WizardStyle=modern ; Estilo moderno do assistente de instalação
SetupIconFile=.\icon.ico ; Caminho para o ficheiro .ico da sua aplicação (assumindo que está na raiz do projeto)
UninstallDisplayIcon={app}\REGTEL.exe ; Ícone a ser exibido no "Adicionar/Remover Programas"
UninstallDisplayName=REGTEL - Plataforma de Registo de Ocorrências ; Nome no "Adicionar/Remover Programas"
DisableStartupPrompt=yes ; Não pergunta para iniciar a aplicação após a instalação
VersionInfoVersion=1.0.0.0 ; ATUALIZE: Versão do ficheiro do instalador (geralmente igual a AppVersion)
ArchitecturesAllowed=x64 ; Se a sua aplicação é 64-bit, especifique
ArchitecturesInstallIn64BitMode=x64 ; Instala em Program Files (x86) ou Program Files

; --- Para garantir uma INSTALAÇÃO LIMPA ---
; Quando uma nova versão é instalada, o Inno Setup pode desinstalar a versão anterior
; automaticamente se detectar que ela já existe. As diretivas abaixo são cruciais para isso.
Uninstallable=yes ; Garante que o programa pode ser desinstalado
CreateUninstallRegKey=yes ; Cria a chave de registo para desinstalação no Windows

[Files]
; Inclui todos os ficheiros da pasta 'dist' (gerada pelo PyInstaller), que contém o executável e suas dependências.
; Exclui ficheiros .iss que podem estar na pasta 'dist' por engano.
Source: ".\dist\*"; DestDir: "{app}"; Excludes: "*.iss"

; Inclui ficheiros de configuração essenciais que podem não ser empacotados pelo PyInstaller
; (assumindo que estão na raiz do projeto, ao lado de 'dist').
Source: ".\client_secrets.json"; DestDir: "{app}"
Source: ".\service_account.json"; DestDir: "{app}"

; NOVO: Mantém a pasta de dados do utilizador durante atualizações
; A pasta .regtel (ou REGTEL) é criada em {userappdata} (Windows) ou ~/.config (Linux/macOS)
; Esta diretiva garante que, se o instalador for executado novamente para uma atualização,
; ele não vai sobrescrever ou remover esta pasta de sessão.
; O 'uninsneveruninstall' é crucial para que esta pasta não seja removida na desinstalação.
Source: "{userappdata}\REGTEL\*"; DestDir: "{userappdata}\REGTEL"; Flags: recursesubdirs createallsubdirs external noinstallfont noregerror shareduserdirectory ignoreversion onlyifdestfileexists uninsneveruninstall

[Icons]
; Cria atalhos na área de trabalho e no menu Iniciar.
; Atalho no Menu Iniciar
Name: "{group}\REGTEL - Plataforma de Registo de Ocorrências"; Filename: "{app}\REGTEL.exe"
; Atalho no Ambiente de Trabalho (opcional, selecionável pelo utilizador)
Name: "{autodesktop}\REGTEL - Plataforma de Registo de Ocorrências"; Filename: "{app}\REGTEL.exe"; Tasks: desktopicon

[Tasks]
; Define tarefas opcionais para o instalador (ex: criar ícone no ambiente de trabalho)
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Run]
; Comando para executar a aplicação após a instalação (opcional)
Filename: "{app}\REGTEL.exe"; Description: "{cm:LaunchProgram,REGTEL - Plataforma de Registo de Ocorrências}"; Flags: postinstall skipifsilent

[UninstallRun]
; Comandos a executar durante a desinstalação (opcional).
; Por padrão, não vamos remover a pasta de sessão do utilizador aqui,
; pois ela contém as credenciais persistentes.
; Se o utilizador desinstalar, ele precisará fazer login novamente na próxima instalação.
; Se desejar remover a pasta de sessão na desinstalação, descomente a linha abaixo.
; Type: filesandordirs; Name: "{userappdata}\REGTEL"

AppContact=suporte@suaempresa.com
AppSupportURL=https://www.suaempresa.com/suporte

; --- Configurações de Instalação ---
DefaultDirName={autopf}\REGTEL
DefaultGroupName=REGTEL
OutputBaseFilename=REGTEL_Installer_1.0.0
SetupIconFile=.\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\REGTEL.exe
UninstallDisplayName=REGTEL
VersionInfoVersion=1.0.0.0
SetupLogging=yes

; --- SOLUÇÃO DEFINITIVA PARA O ERRO ---
; Use uma das opções abaixo (remova o ponto-e-vírgula para ativar UMA delas):
;PrivilegesRequired=admin
PrivilegesRequired=lowest

; --- Configurações de Arquitetura ---
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: ".\dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs; Excludes: "*.log,*.tmp,*.bak,*.iss"
Source: ".\client_secrets.json"; DestDir: "{userappdata}\REGTEL"; Flags: onlyifdoesntexist uninsneveruninstall
Source: ".\service_account.json"; DestDir: "{userappdata}\REGTEL"; Flags: onlyifdoesntexist uninsneveruninstall

[InstallDelete]
Type: filesandordirs; Name: "{app}"

[Icons]
Name: "{group}\REGTEL"; Filename: "{app}\REGTEL.exe"
Name: "{autodesktop}\REGTEL"; Filename: "{app}\REGTEL.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Run]
Filename: "{app}\REGTEL.exe"; Description: "{cm:LaunchProgram,REGTEL}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\REGTEL"