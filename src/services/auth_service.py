# ==============================================================================
# ARQUIVO: src/services/auth_service.py
# DESCRIÇÃO: (VERSÃO REATORADA E CORRIGIDA) Lida com todo o fluxo de autenticação,
#            incluindo o armazenamento seguro da sessão do usuário.
# ==============================================================================

import os
import sys
from tkinter import messagebox
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# --- Dependências Google ---
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from google.oauth2 import service_account

# O AuthManager foi removido, a sua lógica agora está nesta classe.

class AuthService:
    """
    Lida com a autenticação de usuários (OAuth), da conta de serviço e com o
    armazenamento seguro e persistente da sessão do usuário.
    """
    def __init__(self):
        # Escopos de permissão para as APIs do Google
        self.SCOPES_USER = ["openid", "https://www.googleapis.com/auth/userinfo.email", 
                            "https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
        self.SCOPES_SERVICE_ACCOUNT = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Caminhos para os arquivos de credenciais
        self.CLIENT_SECRET_FILE = self._resource_path("client_secrets.json")
        self.SERVICE_ACCOUNT_FILE = self._resource_path("service_account.json")

        # --- Lógica do antigo AuthManager integrada aqui ---
        if sys.platform.startswith('win'):
            app_data_path = os.environ.get('APPDATA', os.path.join(os.path.expanduser("~"), "AppData", "Roaming"))
            base_dir = os.path.join(app_data_path, "REGTEL")
        else:
            base_dir = os.path.join(os.path.expanduser("~"), ".config", "regtel")

        self.auth_file = os.path.join(base_dir, "session.auth")
        os.makedirs(os.path.dirname(self.auth_file), exist_ok=True)
        self.encryption_key = self._generate_encryption_key()

    def _resource_path(self, relative_path):
        """ 
        Obtém o caminho absoluto para os recursos, funciona para desenvolvimento e para o executável do PyInstaller.
        """
        # O atributo _MEIPASS é adicionado pelo PyInstaller em tempo de execução.
        # Usamos hasattr para verificar sua existência de forma segura e evitar alertas de análise estática.
        if hasattr(sys, '_MEIPASS'):
            # Se estiver executando como um pacote do PyInstaller
            # A diretiva abaixo ignora o alerta do Pylance, que não reconhece o atributo em tempo de análise.
            base_path = sys._MEIPASS # pyright: ignore[reportAttributeAccessIssue]
        else:
            # Se estiver executando em um ambiente de desenvolvimento normal
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        
        return os.path.join(base_path, relative_path)

    # ==============================================================================
    # --- MÉTODOS DE GERENCIAMENTO DE SESSÃO (DO ANTIGO AUTH_MANAGER) ---
    # ==============================================================================

    def _generate_encryption_key(self):
        """
        Gera uma chave de criptografia consistente baseada em um identificador do sistema.
        """
        system_id = os.environ.get('USERNAME', 'default_user_id')
        # A função getuid só existe em sistemas Unix-like (Linux, macOS).
        # O Pylance pode alertar sobre isso em um ambiente Windows, então ignoramos o alerta.
        if hasattr(os, 'getuid'):
            system_id = str(os.getuid()) # pyright: ignore[reportAttributeAccessIssue]

        salt = system_id.encode('utf-8')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(system_id.encode('utf-8')))
        return key

    def _save_session(self, user_data):
        """Salva os dados da sessão criptografados no arquivo."""
        try:
            cipher = Fernet(self.encryption_key)
            encrypted_data = cipher.encrypt(json.dumps(user_data).encode('utf-8'))
            with open(self.auth_file, 'wb') as f:
                f.write(encrypted_data)
            if not sys.platform.startswith('win'):
                os.chmod(self.auth_file, 0o600)
            return True
        except Exception as e:
            print(f"Erro ao salvar a sessão: {e}")
            return False

    def _load_session(self):
        """Carrega e descriptografa os dados da sessão do arquivo."""
        if not os.path.exists(self.auth_file):
            return None
        try:
            with open(self.auth_file, 'rb') as f:
                encrypted_data = f.read()
            cipher = Fernet(self.encryption_key)
            decrypted_data = cipher.decrypt(encrypted_data).decode('utf-8')
            return json.loads(decrypted_data)
        except Exception as e:
            print(f"Erro ao carregar/descriptografar sessão: {e}")
            self.clear_session()
            return None

    def clear_session(self):
        """Remove a sessão salva do disco."""
        if os.path.exists(self.auth_file):
            try:
                os.remove(self.auth_file)
            except Exception as e:
                print(f"Erro ao limpar a sessão: {e}")

    # ==============================================================================
    # --- MÉTODOS DE AUTENTICAÇÃO (OAUTH E SERVIÇO) ---
    # ==============================================================================

    def load_user_credentials(self):
        """
        Carrega as credenciais do usuário a partir do armazenamento seguro.
        """
        creds = None
        session_data = self._load_session()
        
        if session_data:
            try:
                creds = Credentials.from_authorized_user_info(session_data, self.SCOPES_USER)
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    self.save_user_credentials(creds)
                if creds and creds.valid:
                    return creds
            except RefreshError as e:
                messagebox.showwarning("Sessão Expirada", "Sua sessão expirou ou as permissões mudaram. Por favor, faça o login novamente.")
                self.logout()
                return None
            except Exception as e:
                messagebox.showerror("Erro de Credenciais", f"Ocorreu um erro ao carregar as credenciais: {e}")
                self.logout()
                return None
        return None

    def save_user_credentials(self, credentials):
        """
        Converte o objeto Credentials para um dicionário e salva a sessão.
        """
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
            'id_token': credentials.id_token
        }
        self._save_session(creds_data)

    def run_login_flow(self):
        """Inicia o fluxo de login OAuth2 para o usuário."""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(self.CLIENT_SECRET_FILE, self.SCOPES_USER)
            creds = flow.run_local_server(port=0)
            self.save_user_credentials(creds)
            return creds
        except Exception as e:
            messagebox.showerror("Erro de Login", f"Não foi possível iniciar o login. Verifique o arquivo 'client_secrets.json' e sua conexão.\n\nDetalhes: {e}")
            return None

    def logout(self):
        """Limpa a sessão do usuário."""
        self.clear_session()

    def get_user_email(self, credentials):
        """Obtém o e-mail do usuário autenticado."""
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info.get("email", "Erro: e-mail não encontrado")
        except Exception:
            return "Erro ao obter e-mail"

    def get_drive_service(self, credentials):
        """Cria um serviço para interagir com o Google Drive do usuário."""
        try:
            return build('drive', 'v3', credentials=credentials)
        except Exception as e:
            print(f"Erro ao construir o serviço do Drive: {e}")
            return None

    def get_service_account_credentials(self):
        """Carrega as credenciais da conta de serviço."""
        try:
            return service_account.Credentials.from_service_account_file(
                self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES_SERVICE_ACCOUNT
            )
        except FileNotFoundError:
            messagebox.showerror("Erro Crítico", f"Arquivo não encontrado: {self.SERVICE_ACCOUNT_FILE}")
            return None
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Falha ao carregar credenciais da conta de serviço: {e}")
            return None
