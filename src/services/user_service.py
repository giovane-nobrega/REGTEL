# ==============================================================================
# ARQUIVO: src/services/user_service.py
# ==============================================================================

class UserService:
    """ Encapsula a lógica de negócio para o gerenciamento de usuários. """
    def __init__(self, sheets_service):
        self.sheets_service = sheets_service
        self.users_cache = None

    def get_user_status(self, email):
        return self.sheets_service.check_user_status(email)

    def get_all_users(self, force_refresh=False):
        if force_refresh or self.users_cache is None:
            self.users_cache = self.sheets_service.get_all_users()
        return self.users_cache

    def get_pending_requests(self):
        return self.sheets_service.get_pending_requests()

    def submit_access_request(self, email, full_name, username, main_group, sub_group, company_name=None):
        return self.sheets_service.request_access(email, full_name, username, main_group, sub_group, company_name)

    def update_user_access(self, email, new_status):
        success, message = self.sheets_service.update_user_status(email, new_status)
        if success:
            self.users_cache = None
        return success, message

    def update_user_profiles_batch(self, changes):
        success, message = self.sheets_service.batch_update_user_profiles(changes)
        if success:
            self.users_cache = None
        return success, message
