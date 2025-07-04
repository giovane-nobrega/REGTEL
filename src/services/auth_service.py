import os
import sys
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build

SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.join(base_path, relative_path)

CLIENT_SECRET_FILE = resource_path("client_secrets.json")
TOKEN_FILE = resource_path("token.json")

def load_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
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
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        return flow.run_local_server(port=0)
    except Exception:
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