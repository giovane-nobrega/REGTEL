# ==============================================================================
# FICHEIRO: src/services/auth_service.py
# DESCRIÇÃO: Lida com a autenticação de utilizadores (OAuth) e da conta de serviço.
#            (COM TRATAMENTO DE ERRO DE SCOPE E NOVO ESCOPO DE SHEETS)
#            CORRIGIDO: Tratamento de 'expiry' para evitar 'NoneType' object has no attribute 'replace'.
# ==============================================================================

import os
import sys
from tkinter import messagebox
import json
# import datetime # REMOVIDO: Não é mais necessário para a conversão de expiry aqui

# --- Dependências Google ---
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Importa o novo AuthManager e o date_utils
from services.auth_manager import AuthManager
from utils.date_utils import safe_fromisoformat # Importa a função utilitária (ainda pode ser útil para outros contextos)

class AuthService:
    """Lida com a autenticação de utilizadores (OAuth) e da conta de serviço."""
    def __init__(self):
        # Adicionado o escopo de Google Sheets para o utilizador, conforme a análise.
        self.SCOPES_USER = ["openid", "https://www.googleapis.com/auth/userinfo.email", 
                            "https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
        self.SCOPES_SERVICE_ACCOUNT = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        self.CLIENT_SECRET_FILE = self._resource_path("client_secrets.json")
        self.SERVICE_ACCOUNT_FILE = self._resource_path("service_account.json")

        self.auth_manager = AuthManager() # Instância do AuthManager

    def _resource_path(self, relative_path):
        """ Obtém o caminho absoluto para os recursos, funciona para dev e para executável. """
        try:
            base_path = sys._MEIPASS # pyright: ignore[reportAttributeAccessIssue]
        except Exception:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        return os.path.join(base_path, relative_path)

    def load_user_credentials(self):
        """
        Carrega as credenciais do utilizador a partir do armazenamento seguro.
        Tenta refrescar se expiradas.
        CORRIGIDO: O campo 'expiry' é passado como string ISO para Credentials.from_authorized_user_info.
        """
        creds = None
        session_data = self.auth_manager.load_session()
        
        if session_data:
            try:
                # CORREÇÃO: Passar o expiry como string ISO 8601 para Credentials.from_authorized_user_info.
                # A função Credentials.from_authorized_user_info já espera 'expiry' como string.
                # Se 'expiry' não estiver presente ou for None, o Google Auth lida com isso.
                creds = Credentials.from_authorized_user_info(session_data, self.SCOPES_USER)
                
                # Se as credenciais existirem, estiverem expiradas e tiverem um refresh_token, tenta refrescar
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    # Se o refresh for bem-sucedido, salva as credenciais atualizadas
                    self.save_user_credentials(creds)
                
                # Se as credenciais forem válidas após carregar ou refrescar
                if creds and creds.valid:
                    return creds
            except RefreshError as e:
                # Tratamento de erro quando o scope muda ou o token é inválido/revogado
                if 'Scope has changed' in str(e) or 'invalid_grant' in str(e):
                    messagebox.showwarning("Permissões Atualizadas", 
                                           "As permissões da aplicação foram atualizadas ou sua sessão expirou. Por favor, faça o login novamente.")
                    self.logout() # Apaga o token inválido
                else:
                    messagebox.showerror("Erro de Autenticação", f"Ocorreu um erro ao verificar sua sessão: {e}")
                return None
            except Exception as e:
                # Captura outros erros inesperados durante o carregamento/refresh
                messagebox.showerror("Erro de Credenciais", f"Ocorreu um erro ao carregar as credenciais: {e}")
                self.logout() # Força o logout para um novo início
                return None
        return None

    def save_user_credentials(self, credentials):
        """
        Salva as credenciais do utilizador de forma segura usando AuthManager.
        ATUALIZADO: Inclui expiry (como string ISO) e id_token.
        """
        # Converte o objeto Credentials para um dicionário serializável
        creds_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'universe_domain': credentials.universe_domain,
            # Salva expiry como string ISO 8601
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
            # Salva id_token
            'id_token': credentials.id_token
        }
        self.auth_manager.save_session(creds_data)

    def run_login_flow(self):
        """Inicia o fluxo de login OAuth2 para o utilizador."""
        try:
            # Garante que o fluxo OAuth utiliza os SCOPES_USER atualizados
            flow = InstalledAppFlow.from_client_secrets_file(self.CLIENT_SECRET_FILE, self.SCOPES_USER)
            creds = flow.run_local_server(port=0)
            self.save_user_credentials(creds) # Salva as credenciais recém-obtidas
            return creds
        except Exception as e:
            print(f"Erro no fluxo de login do utilizador: {e}")
            messagebox.showerror("Erro de Login", f"Não foi possível iniciar o login. Verifique o ficheiro 'client_secrets.json' e sua conexão com a internet.\n\nDetalhes: {e}")
            return None

    def logout(self):
        """Remove o ficheiro de token, efetivamente fazendo logout."""
        self.auth_manager.clear_session() # Limpa a sessão salva

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

