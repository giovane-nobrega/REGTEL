# ==============================================================================
# ARQUIVO: src/services/occurrence_service.py
# DESCRIÇÃO: Novo módulo de serviço para gerenciar a lógica de negócio
#            relacionada a ocorrências.
# ==============================================================================

import json
from datetime import datetime

class OccurrenceService:
    """
    Este serviço encapsula toda a lógica de negócio para o gerenciamento de ocorrências.
    Ele atua como uma camada intermediária entre o controlador (app.py) e o
    serviço de acesso a dados (sheets_service.py).
    """
    def __init__(self, sheets_service, auth_service):
        """
        Inicializa o OccurrenceService.

        :param sheets_service: Uma instância de SheetsService para interagir com a planilha.
        :param auth_service: Uma instância de AuthService para obter credenciais de usuário.
        """
        self.sheets_service = sheets_service
        self.auth_service = auth_service
        self.occurrences_cache = None

    def get_all_occurrences_for_user(self, user_email, force_refresh=False):
        """
        Obtém todas as ocorrências visíveis para um usuário específico, aplicando
        as regras de negócio de filtragem baseadas no perfil do usuário.

        :param user_email: O e-mail do usuário para filtrar as ocorrências.
        :param force_refresh: Se True, força o recarregamento dos dados da planilha.
        :return: Uma lista de dicionários, cada um representando uma ocorrência.
        """
        if force_refresh or self.occurrences_cache is None:
            all_occurrences = self.sheets_service.get_all_occurrences()
            user_profile = self.sheets_service.check_user_status(user_email)
            self.occurrences_cache = self._filter_occurrences_by_profile(all_occurrences, user_profile)
        return self.occurrences_cache

    def _filter_occurrences_by_profile(self, all_occurrences, user_profile):
        """
        Lógica de negócio para filtrar ocorrências com base no perfil do usuário.

        :param all_occurrences: A lista completa de todas as ocorrências.
        :param user_profile: O dicionário de perfil do usuário.
        :return: Uma lista de ocorrências filtrada.
        """
        if not user_profile or user_profile.get('status') != 'approved':
            return []

        main_group = user_profile.get("main_group", "").strip().upper()
        user_company = user_profile.get("company", "").strip().upper()

        if main_group == '67_TELECOM':
            return all_occurrences

        filtered_list = []
        if main_group == 'PARTNER':
            if not user_company:
                return []
            for occ in all_occurrences:
                occurrence_id = occ.get('id', '').strip().upper()
                occ_registrador_company = occ.get('registradorcompany', '').strip().upper()
                if 'CALL' in occurrence_id and occ_registrador_company == user_company:
                    filtered_list.append(occ)
            return filtered_list

        if main_group == 'PREFEITURA':
            for occ in all_occurrences:
                occ_group = (str(occ.get("registradormaingroup") or "")).upper()
                occ_id = occ.get("id", "")
                if (occ_group == "PREFEITURA" or
                    (occ_id.startswith("EQUIP") and occ_group == "67_TELECOM") or
                    (occ_id.startswith("SCALL") and occ_group == "67_TELECOM")):
                    filtered_list.append(occ)
            return filtered_list

        return []

    def submit_simple_call(self, user_email, form_data):
        """
        Prepara e envia os dados de uma nova ocorrência de chamada simples.

        :param user_email: O e-mail do usuário registrando a ocorrência.
        :param form_data: Dicionário com os dados do formulário.
        :return: Tupla (success, message).
        """
        user_profile = self.sheets_service.check_user_status(user_email)
        origem = form_data.get('origem', 'N/A')
        destino = form_data.get('destino', 'N/A')
        title = f"CHAMADA SIMPLES DE {origem} PARA {destino}"
        
        full_data = {
            'title': title,
            'user_email': user_email,
            'user_name': user_profile.get("name", "N/A"),
            'user_username': user_profile.get("username", "N/A"),
            'status': 'REGISTRADO',
            'origem': origem,
            'destino': destino,
            'descricao': form_data.get('descricao'),
            'main_group': user_profile.get("main_group", "N/A"),
            'company': user_profile.get("company", "")
        }
        return self.sheets_service.register_simple_call_occurrence(full_data)

    def submit_equipment_occurrence(self, user_credentials, user_email, data, attachment_paths):
        """
        Prepara e envia os dados de uma nova ocorrência de equipamento, incluindo o upload de anexos.

        :param user_credentials: Credenciais do usuário para o upload no Drive.
        :param user_email: E-mail do usuário.
        :param data: Dicionário com os dados do formulário.
        :param attachment_paths: Lista de caminhos dos arquivos a serem anexados.
        :return: Tupla (success, message).
        """
        upload_success, result = self.sheets_service.upload_files_to_drive(user_credentials, attachment_paths)
        if not upload_success:
            return False, result

        user_profile = self.sheets_service.check_user_status(user_email)
        full_data = {
            'user_email': user_email,
            'user_name': user_profile.get("name", "N/A"),
            'user_username': user_profile.get("username", "N/A"),
            'status': 'REGISTRADO',
            'title': data.get('tipo', "EQUIPAMENTO"),
            'modelo': data.get('modelo'),
            'ramal': data.get('ramal'),
            'localizacao': data.get('localizacao'),
            'descricao': data.get('descricao'),
            'anexos_json': json.dumps(result),
            'main_group': user_profile.get("main_group", "N/A"),
            'company': user_profile.get("company", "")
        }
        return self.sheets_service.register_equipment_occurrence(full_data)

    def submit_full_occurrence(self, user_email, title, testes):
        """
        Prepara e envia os dados de uma nova ocorrência de chamada detalhada.

        :param user_email: E-mail do usuário.
        :param title: Título da ocorrência.
        :param testes: Lista de dicionários com os testes de ligação.
        :return: Tupla (success, message).
        """
        user_profile = self.sheets_service.check_user_status(user_email)
        op_a = testes[0]['op_a'] if testes else 'N/A'
        op_b = testes[0]['op_b'] if testes else 'N/A'
        description = testes[0]['obs'] if testes else ""
        
        full_data = {
            'title': title,
            'user_email': user_email,
            'user_name': user_profile.get("name", "N/A"),
            'user_username': user_profile.get("username", "N/A"),
            'status': 'REGISTRADO',
            'op_a': op_a,
            'op_b': op_b,
            'testes_json': json.dumps(testes),
            'description': description,
            'main_group': user_profile.get("main_group", "N/A"),
            'company': user_profile.get("company", "")
        }
        return self.sheets_service.register_full_occurrence(full_data)

    def get_occurrence_details(self, occurrence_id):
        """Busca os detalhes de uma única ocorrência por ID."""
        return self.sheets_service.get_occurrence_by_id(occurrence_id)

    def get_comments(self, occurrence_id):
        """Busca os comentários de uma ocorrência."""
        return self.sheets_service.get_occurrence_comments(occurrence_id)

    def add_comment(self, occurrence_id, user_email, user_name, comment_text):
        """Adiciona um novo comentário a uma ocorrência."""
        return self.sheets_service.add_occurrence_comment(occurrence_id, user_email, user_name, comment_text)

    def update_comment(self, comment_id, new_text):
        """Atualiza um comentário existente."""
        return self.sheets_service.update_occurrence_comment(comment_id, new_text)

    def delete_comment(self, comment_id):
        """Exclui um comentário."""
        return self.sheets_service.delete_occurrence_comment(comment_id)
        
    def update_status_from_history(self, occurrence_id, new_status):
        """Atualiza o status de uma ocorrência."""
        success, message = self.sheets_service.update_occurrence_status(occurrence_id, new_status)
        if success:
            self.occurrences_cache = None # Invalida o cache
        return success, message

    def save_batch_status_changes(self, changes):
        """Salva um lote de alterações de status de ocorrências."""
        success, message = self.sheets_service.batch_update_occurrence_statuses(changes)
        if success:
            self.occurrences_cache = None # Invalida o cache
        return success, message
