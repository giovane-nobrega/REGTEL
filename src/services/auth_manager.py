# ==============================================================================
# FICHEIRO: src/services/auth_manager.py
# DESCRIÇÃO: Lida com o armazenamento seguro e persistente de dados de sessão.
# ==============================================================================

import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import sys # Importado para identificar o SO

class AuthManager:
    """
    Gerencia o armazenamento seguro e persistente de dados de sessão
    (como credenciais OAuth) no sistema do utilizador.
    """
    def __init__(self):
        # Define o caminho para o ficheiro de autenticação dentro da pasta .regtel
        # Usa %APPDATA% no Windows e ~/.config ou ~/.local/share no Linux/macOS
        if sys.platform.startswith('win'):
            app_data_path = os.environ.get('APPDATA')
            if not app_data_path: # Fallback se APPDATA não estiver definido
                app_data_path = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
            base_dir = os.path.join(app_data_path, "REGTEL")
        else: # Linux, macOS, etc.
            base_dir = os.path.join(os.path.expanduser("~"), ".config", "regtel") # Ou ~/.local/share/regtel

        self.auth_file = os.path.join(base_dir, "session.auth")
        
        # Cria o diretório se ele não existir
        os.makedirs(os.path.dirname(self.auth_file), exist_ok=True)
        
        # Chave de criptografia fixa para este sistema (gerada uma vez)
        self.encryption_key = self._generate_encryption_key()

    def _generate_encryption_key(self):
        """
        Gera uma chave de criptografia consistente baseada num identificador
        único do sistema ou utilizador.
        """
        # Usa o SID do utilizador no Windows ou UID no Linux/Mac para gerar o salt
        # Para Windows, USERNAME é mais comum e acessível que o SID para este propósito.
        system_id = os.environ.get('USERNAME', 'default_user_id') # Para Windows e outros
        if hasattr(os, 'getuid'): # Para sistemas Unix-like (Linux, macOS)
            system_id = str(os.getuid())

        salt = system_id.encode('utf-8') # O salt deve ser único por utilizador/sistema
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000 # Um número alto de iterações para segurança
        )
        # Deriva a chave e a codifica em base64 URL-safe para uso com Fernet
        key = base64.urlsafe_b64encode(kdf.derive(system_id.encode('utf-8')))
        return key

    def save_session(self, user_data):
        """
        Salva os dados da sessão criptografados no ficheiro.
        user_data deve ser um dicionário serializável em JSON.
        """
        try:
            cipher = Fernet(self.encryption_key)
            # Converte os dados para JSON e depois para bytes antes de criptografar
            encrypted_data = cipher.encrypt(json.dumps(user_data).encode('utf-8'))
            
            with open(self.auth_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Define permissões restritas para o ficheiro (apenas o proprietário pode ler/escrever)
            # Note: os.chmod pode não ser totalmente eficaz em sistemas de ficheiros Windows não-NTFS
            # ou se o Python não tiver privilégios suficientes.
            if sys.platform.startswith('win'):
                # Em Windows, permissões são mais complexas. Uma abordagem simples é tentar
                # garantir que apenas o utilizador atual tenha acesso.
                # No entanto, para Fernet, a chave derivada do USERNAME já oferece isolamento.
                pass 
            else: # Unix-like
                os.chmod(self.auth_file, 0o600) # r/w para o proprietário, nada para outros
            return True
        except Exception as e:
            print(f"Erro ao salvar a sessão: {e}")
            return False

    def load_session(self):
        """
        Carrega e descriptografa os dados da sessão do ficheiro.
        Retorna os dados da sessão (dicionário) ou None se falhar.
        """
        if not os.path.exists(self.auth_file):
            return None
            
        try:
            with open(self.auth_file, 'rb') as f:
                encrypted_data = f.read()
                
            cipher = Fernet(self.encryption_key)
            # Descriptografa e decodifica para string, depois carrega como JSON
            decrypted_data = cipher.decrypt(encrypted_data).decode('utf-8')
            return json.loads(decrypted_data)
        except Exception as e:
            # Captura erros de descriptografia (chave errada, ficheiro corrompido)
            # ou erros de JSON. Neste caso, a sessão é inválida.
            print(f"Erro ao carregar/descriptografar sessão: {e}")
            self.clear_session() # Limpa o ficheiro inválido
            return None

    def clear_session(self):
        """Remove a sessão salva do disco."""
        if os.path.exists(self.auth_file):
            try:
                os.remove(self.auth_file)
                return True
            except Exception as e:
                print(f"Erro ao limpar a sessão: {e}")
                return False
        return True # Já não existe, então está "limpo"
