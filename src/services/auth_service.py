# ==============================================================================
# ARQUIVO: src/services/auth_service.py
# DESCRIÇÃO: Lida com a autenticação e o armazenamento seguro da sessão.
# ==============================================================================

import os
import sys
from tkinter import messagebox
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from google.oauth2 import service_account

class AuthService:
    """ Gerencia a autenticação e a sessão do usuário. """
    def __init__(self):
        self.SCOPES_USER = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
        self.SCOPES_SERVICE_ACCOUNT = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        self.CLIENT_SECRET_FILE = self._resource_path("client_secrets.json")
        self.SERVICE_ACCOUNT_FILE = self._resource_path("service_account.json")

        if sys.platform.startswith('win'):
            base_dir = os.path.join(os.environ.get('APPDATA', ''), "REGTEL")
        else:
            base_dir = os.path.join(os.path.expanduser("~"), ".config", "regtel")

        self.auth_file = os.path.join(base_dir, "session.auth")
        os.makedirs(os.path.dirname(self.auth_file), exist_ok=True)
        self.encryption_key = self._generate_encryption_key()

    def _resource_path(self, relative_path):
        """ Obtém o caminho absoluto para os recursos. """
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS # pyright: ignore[reportAttributeAccessIssue]
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        return os.path.join(base_path, relative_path)

    def _generate_encryption_key(self):
        """ Gera uma chave de criptografia consistente. """
        system_id = os.environ.get('USERNAME', 'default_user_id')
        if hasattr(os, 'getuid'):
            system_id = str(os.getuid()) # pyright: ignore[reportAttributeAccessIssue]
        salt = system_id.encode('utf-8')
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        return base64.urlsafe_b64encode(kdf.derive(salt))

    def _save_session(self, user_data):
        """ Salva a sessão do usuário de forma criptografada. """
        try:
            cipher = Fernet(self.encryption_key)
            encrypted_data = cipher.encrypt(json.dumps(user_data).encode('utf-8'))
            with open(self.auth_file, 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            print(f"Erro ao salvar a sessão: {e}")

    def _load_session(self):
        """ Carrega a sessão do usuário. """
        if not os.path.exists(self.auth_file):
            return None
        try:
            with open(self.auth_file, 'rb') as f:
                encrypted_data = f.read()
            cipher = Fernet(self.encryption_key)
            return json.loads(cipher.decrypt(encrypted_data).decode('utf-8'))
        except Exception:
            self.clear_session()
            return None

    def clear_session(self):
        """ Limpa a sessão salva. """
        if os.path.exists(self.auth_file):
            os.remove(self.auth_file)

    def load_user_credentials(self):
        """ Carrega e atualiza as credenciais do usuário. """
        session_data = self._load_session()
        if session_data:
            try:
                creds = Credentials.from_authorized_user_info(session_data, self.SCOPES_USER)
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    self.save_user_credentials(creds)
                return creds
            except RefreshError:
                self.logout()
        return None

    def save_user_credentials(self, credentials):
        """ Salva as credenciais do usuário na sessão. """
        creds_data = {
            'token': credentials.token, 'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri, 'client_id': credentials.client_id,
            'client_secret': credentials.client_secret, 'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
            'id_token': credentials.id_token
        }
        self._save_session(creds_data)

    def run_login_flow(self):
        """ Inicia o fluxo de login OAuth2. """
        try:
            flow = InstalledAppFlow.from_client_secrets_file(self.CLIENT_SECRET_FILE, self.SCOPES_USER)
            creds = flow.run_local_server(port=0)
            self.save_user_credentials(creds)
            return creds
        except Exception as e:
            messagebox.showerror("Erro de Login", f"Não foi possível iniciar o login.\n\nDetalhes: {e}")
            return None

    def logout(self):
        """ Realiza o logout do usuário. """
        self.clear_session()

    def get_user_email(self, credentials):
        """ Obtém o e-mail do usuário autenticado. """
        try:
            service = build('oauth2', 'v2', credentials=credentials)
            return service.userinfo().get().execute().get("email")
        except Exception:
            return "Erro ao obter e-mail"

    def get_drive_service(self, credentials):
        """ Cria um serviço para interagir com o Google Drive. """
        try:
            return build('drive', 'v3', credentials=credentials)
        except Exception as e:
            print(f"Erro ao construir o serviço do Drive: {e}")
            return None

    def get_service_account_credentials(self):
        """ Carrega as credenciais da conta de serviço. """
        try:
            return service_account.Credentials.from_service_account_file(
                self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES_SERVICE_ACCOUNT
            )
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Falha ao carregar credenciais da conta de serviço: {e}")
            return None