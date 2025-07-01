import os
import json
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# --- CONFIGURAÇÕES ---
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CLIENT_SECRET_FILE = os.path.join(os.path.dirname(__file__), "client_secrets.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

def load_credentials():
    """Carrega credenciais salvas em token.json, se válidas."""
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            if creds and creds.valid:
                return creds
            elif creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                save_credentials(creds)
                return creds
        except Exception as e:
            print(f"Erro ao carregar credenciais: {e}")
    return None

def save_credentials(credentials):
    """Salva as credenciais atualizadas no disco."""
    with open(TOKEN_FILE, 'w') as token:
        token.write(credentials.to_json())

def run_login_flow():
    """Executa o fluxo de login interativo com o Google."""
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    return creds

def get_user_email(credentials):
    """Obtém o e-mail do usuário autenticado usando o token."""
    headers = {"Authorization": f"Bearer {credentials.token}"}
    response = requests.get("https://www.googleapis.com/oauth2/v3/userinfo", headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Erro ao buscar informações do usuário: {response.status_code}")
    
    user_info = response.json()
    return user_info.get("email", "Não identificado")
