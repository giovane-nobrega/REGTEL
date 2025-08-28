# ==============================================================================
# ARQUIVO: src/services/user_service.py
# DESCRIÇÃO: Encapsula a lógica de negócio para o gerenciamento de usuários.
# DATA DA ATUALIZAÇÃO: 28/08/2025
# NOTAS: Nenhuma alteração de código foi necessária neste ficheiro.
# ==============================================================================

class UserService:
    """ Encapsula a lógica de negócio para o gerenciamento de usuários. """
    def __init__(self, sheets_service):
        self.sheets_service = sheets_service
        self.users_cache = None

    def get_user_status(self, email):
        """
        Verifica o status e o perfil de um utilizador.
        """
        return self.sheets_service.check_user_status(email)

    def get_all_users(self, force_refresh=False):
        """
        Obtém todos os utilizadores registados, com a opção de forçar uma atualização do cache.
        """
        if force_refresh or self.users_cache is None:
            self.users_cache = self.sheets_service.get_all_users()
        return self.users_cache

    def get_pending_requests(self):
        """
        Obtém todas as solicitações de acesso pendentes.
        """
        return self.sheets_service.get_pending_requests()

    def submit_access_request(self, email, full_name, username, main_group, sub_group, company_name=None):
        """
        Envia uma solicitação de acesso para um novo utilizador.
        """
        return self.sheets_service.request_access(email, full_name, username, main_group, sub_group, company_name)

    def update_user_access(self, email, new_status):
        """
        Atualiza o status de acesso de um utilizador específico (aprovado/rejeitado).
        Limpa o cache de usuários após a atualização.
        """
        success, message = self.sheets_service.update_user_status(email, new_status)
        if success:
            self.users_cache = None # Invalida o cache para forçar a recarga
        return success, message

    def update_user_profiles_batch(self, changes):
        """
        Atualiza múltiplos perfis de utilizador de uma só vez.
        Limpa o cache de usuários após a atualização.
        """
        success, message = self.sheets_service.batch_update_user_profiles(changes)
        if success:
            self.users_cache = None # Invalida o cache para forçar a recarga
        return success, message
