# ==============================================================================
# ARQUIVO: src/services/auth_manager.py
# DESCRIÇÃO: Gerencia o armazenamento seguro das credenciais de sessão do usuário,
#            incluindo criptografia.
# DATA DA ATUALIZAÇÃO: 28/08/2025
# NOTAS: Este arquivo foi refatorado para incluir criptografia de sessão.
# ==============================================================================

import os
import json
import base64
import sys
from cryptography.fernet import Fernet, InvalidToken
from tkinter import messagebox

class AuthManager:
    """
    Gerencia o armazenamento seguro e a criptografia das credenciais de sessão do usuário.
    """
    def __init__(self):
        self.SESSION_FILE = self._resource_path("session.json")
        self.ENCRYPTION_KEY_FILE = self._resource_path("encryption.key")
        self._fernet = self._load_or_generate_key()

    def _resource_path(self, relative_path):
        """
        Obtém o caminho absoluto para os recursos, funciona para dev e para executável.
        """
        try:
            # PyInstaller cria um atributo _MEIPASS para o caminho temporário
            base_path = sys._MEIPASS # type: ignore
        except Exception:
            # Caminho relativo para o diretório raiz do projeto a partir de src/services
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        return os.path.join(base_path, relative_path)

    def _load_or_generate_key(self):
        """
        Carrega a chave de criptografia de um arquivo ou a gera se não existir.
        """
        if os.path.exists(self.ENCRYPTION_KEY_FILE):
            try:
                with open(self.ENCRYPTION_KEY_FILE, 'rb') as key_file:
                    key = key_file.read()
                    return Fernet(key)
            except Exception as e:
                messagebox.showerror("Erro de Criptografia", f"Não foi possível carregar a chave de criptografia. Detalhes: {e}")
                return None
        else:
            try:
                key = Fernet.generate_key()
                with open(self.ENCRYPTION_KEY_FILE, 'wb') as key_file:
                    key_file.write(key)
                return Fernet(key)
            except Exception as e:
                messagebox.showerror("Erro de Criptografia", f"Não foi possível gerar e salvar a chave de criptografia. Detalhes: {e}")
                return None

    def save_session(self, session_data):
        """
        Salva os dados da sessão do usuário de forma criptografada.
        """
        if not self._fernet:
            messagebox.showerror("Erro de Criptografia", "Chave de criptografia não disponível. Não foi possível salvar a sessão.")
            return

        try:
            # Converte o dicionário para string JSON e depois para bytes
            json_data = json.dumps(session_data).encode('utf-8')
            encrypted_data = self._fernet.encrypt(json_data)
            
            with open(self.SESSION_FILE, 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            messagebox.showerror("Erro ao Salvar Sessão", f"Não foi possível salvar os dados da sessão. Detalhes: {e}")

    def load_session(self):
        """
        Carrega e descriptografa os dados da sessão do usuário.
        """
        if not self._fernet:
            messagebox.showerror("Erro de Criptografia", "Chave de criptografia não disponível. Não foi possível carregar a sessão.")
            return None

        if not os.path.exists(self.SESSION_FILE):
            return None

        try:
            with open(self.SESSION_FILE, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self._fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except InvalidToken:
            messagebox.showwarning("Sessão Inválida", "A sessão armazenada está corrompida ou foi alterada. Por favor, faça login novamente.")
            self.clear_session() # Limpa a sessão inválida
            return None
        except Exception as e:
            messagebox.showerror("Erro ao Carregar Sessão", f"Não foi possível carregar os dados da sessão. Detalhes: {e}")
            return None

    def clear_session(self):
        """
        Remove o arquivo de sessão, efetivamente fazendo logout.
        """
        if os.path.exists(self.SESSION_FILE):
            try:
                os.remove(self.SESSION_FILE)
            except Exception as e:
                messagebox.showerror("Erro ao Limpar Sessão", f"Não foi possível remover o arquivo de sessão. Detalhes: {e}")
