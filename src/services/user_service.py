# ==============================================================================
# ARQUIVO: src/services/user_service.py
# DESCRIÇÃO: Novo módulo de serviço para gerenciar a lógica de negócio
#            relacionada a usuários.
# ==============================================================================

class UserService:
    """
    Este serviço encapsula toda a lógica de negócio para o gerenciamento de usuários,
    incluindo solicitações de acesso e atualização de perfis.
    """
    def __init__(self, sheets_service):
        """
        Inicializa o UserService.

        :param sheets_service: Uma instância de SheetsService para interagir com a planilha.
        """
        self.sheets_service = sheets_service
        self.users_cache = None

    def get_user_status(self, email):
        """Verifica o status e o perfil de um usuário."""
        return self.sheets_service.check_user_status(email)

    def get_all_users(self, force_refresh=False):
        """
        Busca todos os usuários do sistema, utilizando cache para otimização.

        :param force_refresh: Se True, força o recarregamento dos dados da planilha.
        :return: Uma lista de dicionários de usuários.
        """
        if force_refresh or self.users_cache is None:
            self.users_cache = self.sheets_service.get_all_users()
        return self.users_cache

    def get_pending_requests(self):
        """Busca todas as solicitações de acesso pendentes."""
        return self.sheets_service.get_pending_requests()

    def submit_access_request(self, email, full_name, username, main_group, sub_group, company_name=None):
        """
        Processa e envia uma nova solicitação de acesso.

        :return: Tupla (success, message).
        """
        return self.sheets_service.request_access(email, full_name, username, main_group, sub_group, company_name)

    def update_user_access(self, email, new_status):
        """
        Aprova ou rejeita uma solicitação de acesso.

        :param email: O e-mail do usuário.
        :param new_status: O novo status ('approved' ou 'rejected').
        :return: Tupla (success, message).
        """
        success, message = self.sheets_service.update_user_status(email, new_status)
        if success:
            self.users_cache = None # Invalida o cache de usuários
        return success, message

    def update_user_profiles_batch(self, changes):
        """
        Salva um lote de alterações de perfis de usuário.

        :param changes: Dicionário com as alterações a serem aplicadas.
        :return: Tupla (success, message).
        """
        success, message = self.sheets_service.batch_update_user_profiles(changes)
        if success:
            self.users_cache = None # Invalida o cache
        return success, message
