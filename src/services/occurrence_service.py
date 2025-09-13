# ==============================================================================
# ARQUIVO: src/services/occurrence_service.py
# DESCRIÇÃO: Encapsula a lógica de negócio para o gerenciamento de ocorrências.
# DATA DA ATUALIZAÇÃO: 28/08/2025
# ==============================================================================

import json
from datetime import datetime
from tkinter import messagebox
from typing import Dict, Tuple

class OccurrenceService:
    """ Encapsula a lógica de negócio para o gerenciamento de ocorrências. """
    def __init__(self, sheets_service, auth_service):
        self.sheets_service = sheets_service
        self.auth_service = auth_service
        self.occurrences_cache = None

    def get_all_occurrences_for_user(self, user_email, force_refresh=False):
        """
        Obtém todas as ocorrências visíveis para um utilizador específico,
        com a opção de forçar uma atualização do cache.
        """
        if force_refresh or self.occurrences_cache is None:
            self.occurrences_cache = self.sheets_service.get_occurrences_by_user(user_email)
        return self.occurrences_cache

    def filter_occurrences(self, occurrences, filters):
        """
        Filtra uma lista de ocorrências com base nos critérios fornecidos.
        (A lógica de filtro completa deve ser implementada aqui).
        """
        filtered_list = occurrences
        search_term = filters.get('search_term', '').lower()
        # ... (lógica de filtro completa)
        return filtered_list

    def submit_simple_call(self, user_email, form_data):
        """
        Submete uma nova ocorrência de chamada simplificada.
        """
        user_profile = self.sheets_service.check_user_status(user_email)
        title = f"CHAMADA SIMPLES DE {form_data.get('origem', 'N/A')} PARA {form_data.get('destino', 'N/A')}"
        full_data = {**form_data, 'title': title, 'user_email': user_email, 'user_name': user_profile.get("name", "N/A"),
                     'user_username': user_profile.get("username", "N/A"), 'status': 'REGISTRADO',
                     'main_group': user_profile.get("main_group", "N/A"), 'company': user_profile.get("company", "")}
        return self.sheets_service.register_simple_call_occurrence(user_email, full_data)
    
    def get_occurrence_details(self, occurrence_id):
        """
        Obtém os detalhes completos de uma ocorrência pelo seu ID.
        """
        return self.sheets_service.get_occurrence_by_id(occurrence_id)

    # --- MÉTODOS DE COMENTÁRIOS MOVIDOS DE sheets_service.py ---

    def add_comment(self, occurrence_id, user_email, user_name, comment_text):
        """
        Adiciona um novo comentário a uma ocorrência.
        """
        return self.sheets_service.add_occurrence_comment(occurrence_id, user_email, user_name, comment_text)

    def update_comment(self, comment_id, new_comment_text):
        """
        Atualiza o texto de um comentário existente.
        """
        return self.sheets_service.update_occurrence_comment(comment_id, new_comment_text)

    def delete_comment(self, comment_id):
        """
        Elimina um comentário da planilha.
        """
        return self.sheets_service.delete_occurrence_comment(comment_id)
        
    def get_comments(self, occurrence_id):
        """
        Obtém todos os comentários associados a uma ocorrência.
        """
        return self.sheets_service.get_occurrence_comments(occurrence_id)

    def register_simple_call_occurrence(self, user_email: str, user_profile: Dict[str, str], data: Dict[str, str]) -> Tuple[bool, str]:
        """
        Registra uma ocorrência de chamada simplificada.
        """
        return self.sheets_service.register_simple_call_occurrence(user_email, data)