# ==============================================================================
# FICHEIRO: src/services/auth_service.py
# DESCRIÇÃO: Lida com a autenticação de utilizadores (OAuth) e da conta de serviço.
# ==============================================================================

import os
import sys
from tkinter import messagebox

# --- Dependências Google ---
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from google.oauth2 import service_account

class AuthService:
    """Lida com a autenticação de utilizadores (OAuth) e da conta de serviço."""
    def __init__(self):
        self.SCOPES_USER = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/drive"]
        self.SCOPES_SERVICE_ACCOUNT = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # Caminhos para os ficheiros de credenciais
        self.CLIENT_SECRET_FILE = self._resource_path("client_secrets.json")
        self.TOKEN_FILE = self._resource_path("token.json")
        self.SERVICE_ACCOUNT_FILE = self._resource_path("service_account.json")

    def _resource_path(self, relative_path):
        """ Obtém o caminho absoluto para os recursos, funciona para dev e para executável. """
        try:
            # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            # Se não estiver num executável, usa o caminho do ficheiro
            # (Assumindo que os ficheiros de credenciais estão na raiz do projeto)
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        return os.path.join(base_path, relative_path)

    def load_user_credentials(self):
        """Carrega as credenciais do utilizador a partir do ficheiro token.json."""
        creds = None
        if os.path.exists(self.TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(self.TOKEN_FILE, self.SCOPES_USER)
                # Se as credenciais expiraram, tenta atualizá-las
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    self.save_user_credentials(creds)
                if creds and creds.valid:
                    return creds
            except RefreshError:
                # Se o token de atualização for inválido, faz logout
                self.logout()
                return None
        return None

    def save_user_credentials(self, credentials):
        """Salva as credenciais do utilizador no ficheiro token.json."""
        with open(self.TOKEN_FILE, 'w') as token:
            token.write(credentials.to_json())

    def run_login_flow(self):
        """Inicia o fluxo de login OAuth2 para o utilizador."""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(self.CLIENT_SECRET_FILE, self.SCOPES_USER)
            # Abre o navegador para o utilizador autorizar a aplicação
            return flow.run_local_server(port=0)
        except Exception as e:
            print(f"Erro no fluxo de login do utilizador: {e}")
            messagebox.showerror("Erro de Login", f"Não foi possível iniciar o login. Verifique o ficheiro 'client_secrets.json'.\n\nDetalhes: {e}")
            return None

    def logout(self):
        """Remove o ficheiro de token, efetivamente fazendo logout."""
        if os.path.exists(self.TOKEN_FILE):
            os.remove(self.TOKEN_FILE)

    def get_user_email(self, credentials):
        """Obtém o e-mail do utilizador autenticado."""
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info.get("email", "Erro: e-mail não encontrado")
        except Exception:
            return "Erro ao obter e-mail"

    def get_drive_service(self, credentials):
        """Cria um serviço para interagir com o Google Drive do utilizador."""
        try:
            return build('drive', 'v3', credentials=credentials)
        except Exception as e:
            print(f"Erro ao construir o serviço do Drive: {e}")
            return None

    def get_service_account_credentials(self):
        """Carrega as credenciais da conta de serviço (robô)."""
        try:
            return service_account.Credentials.from_service_account_file(
                self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES_SERVICE_ACCOUNT
            )
        except FileNotFoundError:
            messagebox.showerror("Erro Crítico", f"Ficheiro não encontrado: {self.SERVICE_ACCOUNT_FILE}\n\nA aplicação não pode funcionar sem este ficheiro.")
            return None
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Falha ao carregar credenciais da conta de serviço: {e}")
            return None
