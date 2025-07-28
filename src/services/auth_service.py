import os
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
# --- ALTERAÇÃO AQUI ---
from google.oauth2 import service_account
# --- FIM DA ALTERAÇÃO ---

# Scopes para o login do UTILIZADOR (OAuth 2.0)
SCOPES_USER = ["openid", "https://www.googleapis.com/auth/userinfo.email",
               "https://www.googleapis.com/auth/drive"]
# Scopes para as operações do ROBÔ (Conta de Serviço)
SCOPES_SERVICE_ACCOUNT = [
    "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..'))
    return os.path.join(base_path, relative_path)


# Ficheiro para o login do UTILIZADOR
CLIENT_SECRET_FILE = resource_path("client_secrets.json")
TOKEN_FILE = resource_path("token.json")
# --- ALTERAÇÃO AQUI: Ficheiro para o ROBÔ ---
SERVICE_ACCOUNT_FILE = resource_path("service_account.json")
# --- FIM DA ALTERAÇÃO ---

# ==============================================================================
# --- FUNÇÕES PARA O LOGIN DO UTILIZADOR (OAuth 2.0) ---
# (Estas funções permanecem para identificar quem está a usar a aplicação)
# ==============================================================================


def load_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(
                TOKEN_FILE, SCOPES_USER)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                save_credentials(creds)
            if creds and creds.valid:
                return creds
        except RefreshError:
            logout()
            return None
    return None


def save_credentials(credentials):
    with open(TOKEN_FILE, 'w') as token:
        token.write(credentials.to_json())


def run_login_flow():
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE, SCOPES_USER)
        return flow.run_local_server(port=0)
    except Exception as e:
        print(f"Erro no fluxo de login do utilizador: {e}")
        return None


def logout():
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)


def get_user_email(credentials):
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        return user_info.get("email", "Erro: e-mail não encontrado")
    except Exception:
        return "Erro ao obter e-mail"


def get_drive_service(credentials):
    """Constrói um serviço do Drive usando as credenciais do UTILIZADOR."""
    try:
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        print(f"Erro ao construir o serviço do Drive: {e}")
        return None

# ==============================================================================
# --- FUNÇÃO PARA A AUTENTICAÇÃO DO ROBÔ (Conta de Serviço) ---
# ==============================================================================


def get_service_account_credentials():
    """
    Carrega as credenciais da Conta de Serviço a partir do ficheiro JSON.
    Estas credenciais são usadas para todas as operações na planilha.
    """
    try:
        return service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES_SERVICE_ACCOUNT
        )
    except FileNotFoundError:
        print(
            f"ERRO CRÍTICO: O ficheiro da conta de serviço '{SERVICE_ACCOUNT_FILE}' não foi encontrado.")
        return None
    except Exception as e:
        print(
            f"ERRO CRÍTICO: Falha ao carregar as credenciais da conta de serviço: {e}")
        return None
