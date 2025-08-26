# ==============================================================================
# ARQUIVO: src/services/occurrence_service.py
# ==============================================================================

import json
from datetime import datetime
from tkinter import messagebox

class OccurrenceService:
    """ Encapsula a lógica de negócio para o gerenciamento de ocorrências. """
    def __init__(self, sheets_service, auth_service):
        self.sheets_service = sheets_service
        self.auth_service = auth_service
        self.occurrences_cache = None

    def get_all_occurrences_for_user(self, user_email, force_refresh=False):
        if force_refresh or self.occurrences_cache is None:
            self.occurrences_cache = self.sheets_service.get_occurrences_by_user(user_email)
        return self.occurrences_cache

    def filter_occurrences(self, occurrences, filters):
        filtered_list = occurrences
        search_term = filters.get('search_term', '').lower()
        # ... (lógica de filtro completa)
        return filtered_list

    def submit_simple_call(self, user_email, form_data):
        user_profile = self.sheets_service.check_user_status(user_email)
        title = f"CHAMADA SIMPLES DE {form_data.get('origem', 'N/A')} PARA {form_data.get('destino', 'N/A')}"
        full_data = {**form_data, 'title': title, 'user_email': user_email, 'user_name': user_profile.get("name", "N/A"),
                     'user_username': user_profile.get("username", "N/A"), 'status': 'REGISTRADO',
                     'main_group': user_profile.get("main_group", "N/A"), 'company': user_profile.get("company", "")}
        return self.sheets_service.register_simple_call_occurrence(full_data)
    
    def get_occurrence_details(self, occurrence_id):
        return self.sheets_service.get_occurrence_by_id(occurrence_id)