import os
import sys
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIGURAÇÕES DE AUTENTICAÇÃO ---
# Escopos definem as permissões que a aplicação solicitará ao usuário.
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def resource_path(relative_path):
    """ Obtém o caminho absoluto para o recurso, funciona para dev e para PyInstaller. """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Define os caminhos para os arquivos de segredos e de token
CLIENT_SECRET_FILE = resource_path("client_secrets.json")
TOKEN_FILE = resource_path("token.json")

def load_credentials():
    """
    Carrega as credenciais do arquivo de token. Se não forem válidas ou estiverem
    expiradas, tenta atualizá-las. Retorna None se não houver token.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"[auth] Erro ao carregar o arquivo de token: {e}")
            return None

    # Se as credenciais existem, verifica se são válidas
    if creds and creds.valid:
        return creds
    
    # Se expiraram e possuem um refresh token, tenta atualizar
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(creds) # Salva as novas credenciais atualizadas
            return creds
        except RefreshError as e:
            print(f"[auth] O token não pôde ser atualizado. O usuário precisará fazer login novamente. Erro: {e}")
            logout() # Força o logout para limpar o token inválido
            return None
        except Exception as e:
            print(f"[auth] Erro inesperado ao atualizar o token: {e}")
            return None
            
    return None

def save_credentials(credentials):
    """Salva o token de acesso no disco em formato JSON."""
    try:
        with open(TOKEN_FILE, 'w') as token:
            token.write(credentials.to_json())
    except Exception as e:
        print(f"[auth] Erro ao salvar credenciais: {e}")

def run_login_flow():
    """
    Executa o fluxo de login OAuth 2.0 interativo.
    Primeiro tenta abrir um servidor local. Se falhar, usa o console.
    """
    flow = None
    try:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    except FileNotFoundError:
        print("[auth] ERRO CRÍTICO: O arquivo 'client_secrets.json' não foi encontrado.")
        return None
    except Exception as e:
        print(f"[auth] Erro ao carregar o arquivo de segredos do cliente: {e}")
        return None

    creds = None
    try:
        # O método recomendado para apps de desktop
        creds = flow.run_local_server(port=0)
    except OSError:
        # Fallback para ambientes sem GUI ou se o navegador não puder ser aberto
        print("[auth] Não foi possível iniciar o servidor local. Tentando via console.")
        try:
            creds = flow.run_console()
        except Exception as e:
            print(f"[auth] Falha no fluxo de login via console: {e}")
    except Exception as e:
        print(f"[auth] Falha no fluxo de login: {e}")
        
    return creds

def logout():
    """Remove o arquivo de token do disco para forçar um novo login."""
    try:
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            print("[auth] Logout bem-sucedido.")
    except Exception as e:
        print(f"[auth] Erro durante o logout: {e}")

def get_user_email(credentials):
    """
    Obtém o e-mail do usuário autenticado usando a API do OAuth2.
    Esta é a abordagem moderna usando o google-api-python-client.
    """
    try:
        # Constrói um objeto de serviço para a API do OAuth2
        service = build('oauth2', 'v2', credentials=credentials)
        # Executa a requisição para obter as informações do usuário
        user_info = service.userinfo().get().execute()
        return user_info.get("email", "E-mail não encontrado")
    except HttpError as e:
        print(f"[auth] Erro HTTP ao obter e-mail: {e.resp.status} - {e.content}")
        return "Erro ao obter e-mail (HTTP)"
    except Exception as e:
        print(f"[auth] Erro inesperado ao obter e-mail: {e}")
        return "Erro ao obter e-mail"

