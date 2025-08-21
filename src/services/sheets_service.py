# ==============================================================================
# FICHEIRO: src/services/sheets_service.py
# DESCRIÇÃO: Lida com todas as operações de leitura e escrita na planilha
#            Google Sheets, otimizado com operações em lote.
#            Gere o acesso a diferentes abas (folhas) e tipos de ocorrências.
# ==============================================================================

import gspread  # Biblioteca Python para interagir com a Google Sheets API
# Usado para serializar/desserializar dados JSON (ex: testes, anexos)
import json
import csv  # Usado para exportação de dados CSV (se implementado)
from datetime import datetime  # Usado para timestamps
# Usado para upload de ficheiros para o Google Drive
from googleapiclient.http import MediaFileUpload
import os  # Usado para operações de sistema de ficheiros
from tkinter import messagebox  # Usado para exibir mensagens de erro/informação
# Usado para garantir segurança de thread ao aceder a recursos compartilhados (gspread)
import threading


class SheetsService:
    """
    Lida com todas as operações de leitura e escrita na planilha Google Sheets.
    Utiliza uma conta de serviço para acesso programático e otimiza operações
    com cache e processamento em lote.
    """

    def __init__(self, auth_service_instance):
        """
        Inicializa o SheetsService com uma instância de AuthService para autenticação.
        Define IDs da planilha e nomes das abas.
        :param auth_service_instance: Instância de AuthService para obter credenciais.
        """
        self.auth_service = auth_service_instance  # Referência ao serviço de autenticação

        # --- IDs e Nomes de Planilhas/Abas ---
        # ATUALIZE: SPREADSHEET_ID com o ID da sua planilha principal do Google Sheets.
        self.SPREADSHEET_ID = "1ymzB0QiZiuTnLk9h3qfFnZgcxkTKJUeT-3rn4bYqtQA"
        self.USERS_SHEET = "users"  # Aba para gerenciar utilizadores e seus status
        # Aba para ocorrências de chamada detalhadas
        self.CALLS_SHEET = "call_occurrences"
        # Aba para ocorrências de chamada simplificadas
        self.SIMPLE_CALLS_SHEET = "simple_call_occurrences"
        # Aba para ocorrências de equipamento
        self.EQUIPMENT_SHEET = "equipment_occurrences"
        # Nova aba para armazenar comentários de ocorrências
        self.OCCURRENCE_COMMENTS_SHEET = "occurrence_comments"

        # Um lock para garantir que as operações do gspread sejam thread-safe
        self.gspread_lock = threading.Lock()
        self._GC = None  # Cliente gspread (Google Client)
        self._SPREADSHEET = None  # Objeto da planilha aberta
        self.is_connected = False  # Flag para verificar o estado da conexão

    def _connect(self):
        """
        Conecta-se ao Google Sheets usando as credenciais da conta de serviço.
        A conexão é estabelecida apenas uma vez (singleton pattern) e é thread-safe.
        """
        if self.is_connected:
            return  # Já conectado, não faz nada

        with self.gspread_lock:  # Adquire o lock para garantir que apenas uma thread se conecta por vez
            if self.is_connected:
                return  # Dupla verificação dentro do lock

            # Obtém as credenciais da conta de serviço do AuthService.
            self._SERVICE_CREDENTIALS = self.auth_service.get_service_account_credentials()
            if not self._SERVICE_CREDENTIALS:
                return  # Não foi possível obter as credenciais, retorna

            try:
                # Autentica com o gspread usando o ficheiro de credenciais da conta de serviço.
                self._GC = gspread.service_account(
                    filename=self.auth_service.SERVICE_ACCOUNT_FILE)
                # Abre a planilha pelo seu ID.
                self._SPREADSHEET = self._GC.open_by_key(self.SPREADSHEET_ID)
                self.is_connected = True  # Marca a conexão como bem-sucedida
            except Exception as e:
                messagebox.showerror(
                    "Erro de Conexão", f"Não foi possível conectar ao Google Sheets: {e}")

    def _get_worksheet(self, sheet_name):
        """
        Obtém uma aba (worksheet) específica da planilha.
        :param sheet_name: O nome da aba (string).
        :return: O objeto da aba (Worksheet) ou None se não for encontrada ou houver erro.
        """
        self._connect()  # Garante que a conexão com o Google Sheets está estabelecida
        if not self._SPREADSHEET:
            return None  # Se a planilha não foi aberta, retorna None

        try:
            # Retorna a aba pelo nome
            return self._SPREADSHEET.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            print(
                f"ERRO: A aba '{sheet_name}' não foi encontrada na planilha.")
            return None
        except Exception as e:
            print(f"ERRO ao obter a aba '{sheet_name}': {e}")
            return None

    def _get_all_records_safe(self, worksheet):
        """
        Lê todos os registos de uma aba de forma segura (thread-safe).
        Normaliza as chaves dos dicionários de retorno para facilitar o acesso.
        :param worksheet: O objeto da aba (Worksheet) a ser lida.
        :return: Uma lista de dicionários, onde cada dicionário representa uma linha.
                 Cada dicionário contém chaves originais e normalizadas (minúsculas, sem espaços).
        """
        with self.gspread_lock:  # Adquire o lock para garantir acesso exclusivo à aba durante a leitura
            # Obtém todos os registos como uma lista de dicionários
            raw_records = worksheet.get_all_records()
            processed_records = []
            for rec in raw_records:
                processed_rec = {}
                for k, v in rec.items():
                    # Mantém a chave original (como está na planilha)
                    original_key = k
                    # Cria uma versão normalizada (minúsculas, sem espaços)
                    normalized_key = k.strip().lower()

                    # Armazena o valor com a chave original
                    processed_rec[original_key] = v
                    if original_key != normalized_key:  # Evita duplicação se a chave já for normalizada
                        # Armazena o valor com a chave normalizada
                        processed_rec[normalized_key] = v
                processed_records.append(processed_rec)
            return processed_records

    def _upload_files_to_drive(self, user_credentials, file_paths):
        """
        Faz o upload de ficheiros para o Google Drive do utilizador.
        Cria uma pasta "Craft Quest Anexos" se não existir e torna os ficheiros públicos.
        :param user_credentials: Credenciais OAuth do utilizador para acesso ao Google Drive.
        :param file_paths: Lista de caminhos locais dos ficheiros a serem carregados.
        :return: Tupla (True, lista_de_links) se sucesso, ou (False, mensagem_de_erro).
        """
        if not file_paths:
            return True, []  # Retorna sucesso se não houver ficheiros para upload

        drive_service = self.auth_service.get_drive_service(
            user_credentials)  # Obtém o serviço do Google Drive
        if not drive_service:
            return False, "Não foi possível obter o serviço do Google Drive."

        try:
            # Procura por uma pasta existente chamada "Craft Quest Anexos"
            q = "mimeType='application/vnd.google-apps.folder' and name='Craft Quest Anexos' and trashed=false"
            response = drive_service.files().list(
                q=q, spaces='drive', fields='files(id, name)').execute()

            folder_id = None
            if response.get('files'):
                folder_id = response.get('files')[0].get(
                    'id')  # Usa a primeira pasta encontrada
            else:
                # Se a pasta não existir, cria uma nova.
                folder_metadata = {'name': 'Craft Quest Anexos',
                                   'mimeType': 'application/vnd.google-apps.folder'}
                folder_id = drive_service.files().create(
                    body=folder_metadata, fields='id').execute().get('id')

            uploaded_file_links = []
            for file_path in file_paths:
                file_metadata = {'name': os.path.basename(
                    file_path), 'parents': [folder_id]}
                # Prepara o ficheiro para upload resumível
                media = MediaFileUpload(file_path, resumable=True)
                file = drive_service.files().create(body=file_metadata, media_body=media,
                                                    fields='id, webViewLink').execute()

                # Torna o ficheiro publicamente acessível (qualquer um pode ler)
                drive_service.permissions().create(fileId=file.get('id'), body={
                    'role': 'reader', 'type': 'anyone'}).execute()
                # Adiciona o link de visualização
                uploaded_file_links.append(file.get('webViewLink'))

            # Retorna True e a lista de links dos ficheiros carregados
            return True, uploaded_file_links
        except Exception as e:
            return False, f"Ocorreu um erro durante o upload para o Google Drive: {e}"

    # ==============================================================================
    # --- MÉTODOS DE ATUALIZAÇÃO EM LOTE (OTIMIZADOS) ---
    # ==============================================================================

    def batch_update_occurrence_statuses(self, changes: dict):
        """
        Atualiza múltiplos status de ocorrências de uma só vez usando operações em lote.
        Isso é mais eficiente do que atualizar cada ocorrência individualmente.
        :param changes: Dicionário onde a chave é o ID da ocorrência e o valor é o novo status.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect()  # Garante a conexão
        if not self._SPREADSHEET:
            return False, "Falha na conexão."

        updates_by_sheet = {
            self.CALLS_SHEET: [],
            self.SIMPLE_CALLS_SHEET: [],
            self.EQUIPMENT_SHEET: []
        }

        all_ids_map = {}
        # Mapeia todos os IDs de ocorrência para suas abas e linhas.
        for sheet_name in updates_by_sheet.keys():
            ws = self._get_worksheet(sheet_name)
            if ws:
                # Obtém todos os valores da primeira coluna (IDs)
                ids_in_sheet = ws.col_values(1)
                for i, cell_id in enumerate(ids_in_sheet):
                    if i == 0:
                        continue  # Ignora o cabeçalho
                    # Armazena a aba e a linha
                    all_ids_map[cell_id] = {'sheet': sheet_name, 'row': i + 1}

        # Prepara as células a serem atualizadas.
        for occ_id, new_status in changes.items():
            if occ_id in all_ids_map:
                info = all_ids_map[occ_id]
                sheet_name = info['sheet']
                # A coluna do status é diferente para ocorrências de equipamento (coluna 6) e outras (coluna 7).
                status_col = 6 if sheet_name == self.EQUIPMENT_SHEET else 7
                updates_by_sheet[sheet_name].append(gspread.Cell(
                    info['row'], status_col, value=new_status))

        try:
            with self.gspread_lock:  # Adquire o lock para operações em lote seguras
                for sheet_name, cells_to_update in updates_by_sheet.items():
                    if cells_to_update:
                        ws = self._get_worksheet(sheet_name)
                        if ws:
                            # Realiza a atualização em lote para cada aba
                            ws.update_cells(cells_to_update)
            return True, "Alterações salvas com sucesso."
        except Exception as e:
            return False, f"Erro na atualização em lote: {e}"

    def batch_update_user_profiles(self, changes: dict):
        """
        Atualiza múltiplos perfis de utilizador de uma só vez usando operações em lote.
        :param changes: Dicionário onde a chave é o e-mail do utilizador e o valor é um dicionário
                        com as mudanças de perfil (main_group, sub_group, company).
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect()  # Garante a conexão
        # Obtém a aba de utilizadores
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws:
            return False, "Falha na conexão com a aba de utilizadores."

        # Obtém todos os e-mails da primeira coluna
        emails_in_sheet = ws.col_values(1)
        # Mapeia e-mails normalizados para suas linhas na planilha.
        all_users_map = {emails_in_sheet[i].strip().lower(): {'row': i + 1}
                         for i in range(1, len(emails_in_sheet)) if emails_in_sheet[i].strip()}

        cells_to_update = []
        # Prepara as células a serem atualizadas.
        for email, profile_changes in changes.items():
            normalized_email = email.strip().lower()
            if normalized_email in all_users_map:
                row = all_users_map[normalized_email]['row']
                # Adiciona células para atualizar Grupo Principal (col 4), Subgrupo (col 5), Empresa (col 7)
                cells_to_update.append(gspread.Cell(
                    row, 4, value=profile_changes['main_group']))
                cells_to_update.append(gspread.Cell(
                    row, 5, value=profile_changes['sub_group']))
                cells_to_update.append(gspread.Cell(
                    row, 7, value=profile_changes['company']))

        try:
            with self.gspread_lock:  # Adquire o lock para operações em lote seguras
                if cells_to_update:
                    # Realiza a atualização em lote
                    ws.update_cells(cells_to_update)
            return True, "Perfis atualizados com sucesso."
        except Exception as e:
            return False, f"Erro na atualização de perfis em lote: {e}"

    # ==============================================================================
    # --- MÉTODOS DE LEITURA E ESCRITA DE OCORRÊNCIAS/UTILIZADORES ---
    # ==============================================================================

    def check_user_status(self, email):
        """
        Verifica o status e o perfil de um utilizador na planilha 'users'.
        :param email: E-mail do utilizador a ser verificado.
        :return: Dicionário com os dados do perfil do utilizador ou status de erro/não registado.
        """
        self._connect()  # Garante a conexão
        # Obtém a aba de utilizadores
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws:
            return {"status": "error"}
        try:
            # Obtém todos os registos com chaves normalizadas
            records = self._get_all_records_safe(ws)
            for user_rec in records:
                if user_rec.get("email") and user_rec["email"].strip().lower() == email.strip().lower():
                    return user_rec  # Retorna o dicionário completo do perfil
        except Exception as e:
            print(f"Erro ao ler a planilha de usuários: {e}")
            return {"status": "error"}
        # Retorna que o utilizador não está registado
        return {"status": "unregistered"}

    def get_all_occurrences(self):
        """
        Obtém todas as ocorrências de todas as abas (chamadas detalhadas, simples, equipamento).
        Normaliza os títulos das ocorrências para exibição consistente.
        :return: Lista de todas as ocorrências, ordenadas pela data de registo (mais recente primeiro).
        """
        self._connect()  # Garante a conexão
        calls_ws = self._get_worksheet(self.CALLS_SHEET)
        simple_calls_ws = self._get_worksheet(self.SIMPLE_CALLS_SHEET)
        equip_ws = self._get_worksheet(self.EQUIPMENT_SHEET)

        all_occurrences = []

        # Chaves preferenciais para determinar o título de uma ocorrência.
        possible_title_keys = ['título da ocorrência', 'título', 'title']

        def get_final_title(record, record_type):
            """
            Função auxiliar para determinar o título de uma ocorrência para exibição.
            Tenta usar o título fornecido pelo utilizador; caso contrário, gera um padrão.
            :param record: Dicionário com os dados da ocorrência.
            :param record_type: Tipo da ocorrência ('call', 'simple_call', 'equipment').
            :return: String com o título final da ocorrência.
            """
            for key in possible_title_keys:
                value = record.get(key)
                if value is not None and str(value).strip() != "":
                    return str(value).strip()

            # Se nenhum título do utilizador for encontrado, gera um padrão.
            record_id = record.get('id', 'N/A')
            if record_type == "call":
                return f"Chamada Detalhada {record_id}"
            elif record_type == "simple_call":
                return f"Chamada Simples de {record.get('origem', 'N/A')} para {record.get('destino', 'N/A')}"
            elif record_type == "equipment":
                return record.get('tipo de equipamento', f"Equipamento {record_id}")

            return f"Ocorrência {record_id}"  # Fallback final

        # Processa ocorrências de chamadas detalhadas.
        if calls_ws:
            calls_records = self._get_all_records_safe(calls_ws)
            for rec in calls_records:
                if rec.get('id'):
                    rec['Título da Ocorrência'] = get_final_title(rec, "call")
                    all_occurrences.append(rec)

        # Processa ocorrências de chamadas simplificadas.
        if simple_calls_ws:
            simple_calls_records = self._get_all_records_safe(simple_calls_ws)
            for rec in simple_calls_records:
                if rec.get('id'):
                    rec['Título da Ocorrência'] = get_final_title(
                        rec, "simple_call")
                    all_occurrences.append(rec)

        # Processa ocorrências de equipamento.
        if equip_ws:
            equip_records = self._get_all_records_safe(equip_ws)
            for rec in equip_records:
                if rec.get('id'):
                    rec['Título da Ocorrência'] = get_final_title(
                        rec, "equipment")
                    all_occurrences.append(rec)

        # Retorna os registos ordenados pela data de registo (mais recente primeiro).
        return sorted(all_occurrences, key=lambda x: x.get('Data de Registro', ''), reverse=True)

    def get_occurrences_by_user(self, user_email):
        """
        Obtém as ocorrências visíveis para um utilizador específico,
        filtrando com base no seu perfil e empresa/departamento.
        :param user_email: E-mail do utilizador.
        :return: Lista de ocorrências visíveis para o utilizador.
        """
        self._connect()  # Garante a conexão
        user_profile = self.check_user_status(
            user_email)  # Obtém o perfil do utilizador

        # --- DEBUG: Informações do Perfil do Utilizador ---
        print(f"\n--- DEBUG: get_occurrences_by_user para {user_email} ---")
        print(f"DEBUG: Perfil do Utilizador: {user_profile}")
        # ----------------------------------------------------

        if not user_profile or user_profile.get('status') != 'approved':
            print(
                "DEBUG: Utilizador não aprovado ou perfil não encontrado. Retornando lista vazia.")
            return []

        main_group = user_profile.get("main_group")
        # Normaliza a empresa do utilizador
        user_company = user_profile.get("company", "").strip().upper()
        # Pega o subgrupo do utilizador
        user_sub_group = user_profile.get("sub_group", "").strip().upper()

        all_occurrences = self.get_all_occurrences()  # Obtém TODAS as ocorrências

        print(
            f"DEBUG: Grupo Principal: {main_group}, Subgrupo do Utilizador: '{user_sub_group}', Empresa do Utilizador: '{user_company}'")
        print(
            f"DEBUG: Total de ocorrências carregadas (antes do filtro): {len(all_occurrences)}")

        # Lógica de filtragem baseada no grupo e subgrupo do utilizador.

        # 67 Telecom users (todos os subgrupos) veem todas as ocorrências.
        if main_group == '67_TELECOM':
            print("DEBUG: Grupo 67_TELECOM detectado. Retornando TODAS as ocorrências.")
            return all_occurrences

        # Parceiros veem apenas ocorrências da sua empresa específica.
        elif main_group == 'PARTNER':
            if not user_company:
                print(
                    f"AVISO: Utilizador {user_email} do grupo {main_group} não tem empresa definida. Retornando lista vazia.")
                return []

            filtered_list = []
            for occ in all_occurrences:
                occ_registrador_main_group = occ.get(
                    'Registrador Main Group', '').strip().upper()
                # Normaliza a empresa do registrador da ocorrência
                occ_registrador_company = occ.get(
                    'Registrador Company', '').strip().upper()

                # --- DEBUG: Detalhes da Ocorrência durante o Filtro (Partner) ---
                print(
                    f"DEBUG: Ocorrência ID: {occ.get('ID', 'N/A')}, Registrador Main Group: '{occ_registrador_main_group}', Registrador Company: '{occ_registrador_company}', User Company (Partner): '{user_company}'")
                # ----------------------------------------------------

                # Ocorrências de parceiros são filtradas estritamente pela sua empresa.
                # Apenas ocorrências cujo Registrador Main Group é 'PARTNER' e a empresa corresponde.
                if occ_registrador_main_group == 'PARTNER' and occ_registrador_company == user_company:
                    filtered_list.append(occ)
                else:
                    print(
                        f"DEBUG: Ocorrência ID: {occ.get('ID', 'N/A')} NÃO incluída para PARTNER (Registrador Main Group: '{occ_registrador_main_group}', Registrador Company: '{occ_registrador_company}' != User Company: '{user_company}')")

            print(
                f"DEBUG: Grupo '{main_group}' detectado. Filtrando por empresa '{user_company}'. Ocorrências filtradas: {len(filtered_list)}")
            return filtered_list

        # Prefeitura veem todas as ocorrências do grupo "PREFEITURA".
        elif main_group == 'PREFEITURA':
            filtered_list = []
            for occ in all_occurrences:
                occ_registrador_main_group = occ.get(
                    'Registrador Main Group', '').strip().upper()
                # Para a Prefeitura, basta que o main group da ocorrência seja 'PREFEITURA'.
                if occ_registrador_main_group == 'PREFEITURA':
                    filtered_list.append(occ)
                else:
                    print(
                        f"DEBUG: Ocorrência ID: {occ.get('ID', 'N/A')} NÃO incluída para PREFEITURA (Registrador Main Group: '{occ_registrador_main_group}')")

            print(
                f"DEBUG: Grupo '{main_group}' detectado. Retornando todas as ocorrências da Prefeitura. Ocorrências filtradas: {len(filtered_list)}")
            return filtered_list

        print(
            f"DEBUG: Perfil '{main_group}' não mapeado para regras de visualização. Retornando lista vazia.")
        return []  # Retorna vazio para perfis não mapeados ou sem permissão

    def get_active_occurrences_for_admin_dashboard(self):
        """
        Obtém todas as ocorrências e filtra aquelas com status 'RESOLVIDO' ou 'CANCELADO',
        destinadas à exibição no dashboard de gestão do administrador.
        :return: Lista de ocorrências ativas.
        """
        all_occurrences = self.get_all_occurrences()  # Obtém todas as ocorrências

        # Define os status que são considerados "ativos" para o dashboard.
        active_statuses = ["REGISTRADO", "EM ANÁLISE",
                           "AGUARDANDO TERCEIROS", "PARCIALMENTE RESOLVIDO"]

        # Filtra as ocorrências que não estão em status de finalização.
        filtered_occurrences = [
            occ for occ in all_occurrences
            if occ.get('Status', '').upper() in active_statuses
        ]
        return filtered_occurrences

    def get_all_users(self):
        """
        Obtém todos os utilizadores registados na planilha 'users'.
        :return: Lista de dicionários, cada um representando um utilizador.
        """
        self._connect()  # Garante a conexão
        # Obtém a aba de utilizadores
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws:
            return []
        # Retorna todos os utilizadores com e-mail
        return [rec for rec in self._get_all_records_safe(ws) if rec.get("email")]

    def get_all_operators(self):
        """
        Obtém uma lista de todas as operadoras de telefonia,
        incluindo uma base predefinida e operadoras encontradas nas ocorrências.
        :return: Lista ordenada de operadoras únicas.
        """
        self._connect()  # Garante a conexão
        # Conjunto de operadoras base predefinidas.
        base_operators = {"VIVO", "CLARO", "TIM", "OI", "ALGAR TELECOM", "SERCOMTEL", "NEXTEL",
                          "VULCANET", "CTBC TELECOM", "UNO INTERNET", "VIVO FIXO", "CLARO FIXO", "OI FIXO", "EMBRATEL"}

        # Obtém a aba de chamadas detalhadas
        ws = self._get_worksheet(self.CALLS_SHEET)
        if not ws:
            # Retorna apenas as base se a aba não for encontrada
            return sorted(list(base_operators))

        try:
            records = self._get_all_records_safe(
                ws)  # Obtém os registos de chamadas
            sheet_operators = set()
            for rec in records:
                # Obtém operadora A (chave normalizada)
                op_a = rec.get('operadora a')
                # Obtém operadora B (chave normalizada)
                op_b = rec.get('operadora b')
                if op_a and str(op_a).strip() != "":
                    sheet_operators.add(str(op_a).strip().upper())
                if op_b and str(op_b).strip() != "":
                    sheet_operators.add(str(op_b).strip().upper())
            # Adiciona operadoras encontradas às base
            base_operators.update(sheet_operators)
        except Exception as e:
            print(f"Erro ao ler operadoras da planilha: {e}")
        # Retorna a lista combinada e ordenada
        return sorted(list(base_operators))

    def request_access(self, email, full_name, username, main_group, sub_group, company_name=None):
        """
        Envia uma solicitação de acesso para um novo utilizador para a planilha 'users'.
        Verifica se o e-mail já existe antes de adicionar.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect()  # Garante a conexão
        # Obtém a aba de utilizadores
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws:
            return False, "Falha ao aceder à planilha."

        try:
            all_users_records = self._get_all_records_safe(
                ws)  # Obtém todos os utilizadores
            normalized_emails_in_sheet = [
                str(rec.get('email', '')).strip().lower() for rec in all_users_records]

            if email.strip().lower() in normalized_emails_in_sheet:
                return False, "Solicitação já existe para este e-mail."  # Evita duplicatas
        except Exception as e:
            return False, f"Erro ao verificar e-mail existente: {e}"

        # Prepara a nova linha com os dados da solicitação.
        new_row = [
            email,              # Coluna 1: Email
            full_name,          # Coluna 2: Nome Completo
            username,           # Coluna 3: Username
            main_group,         # Coluna 4: Grupo Principal
            sub_group,          # Coluna 5: Subgrupo
            "pending",          # Coluna 6: Status inicial como "pending"
            # Coluna 7: Empresa/Departamento (vazio se None)
            company_name or ""
        ]
        try:
            # Adiciona a nova linha
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Solicitação de acesso enviada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao enviar a solicitação: {e}"

    def get_pending_requests(self):
        """
        Obtém todas as solicitações de acesso de utilizadores com status 'pending'.
        :return: Lista de dicionários, cada um representando uma solicitação pendente.
        """
        self._connect()  # Garante a conexão
        # Obtém a aba de utilizadores
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws:
            return []
        all_users = self._get_all_records_safe(
            ws)  # Obtém todos os utilizadores
        return [user for user in all_users if user.get("status") and str(user.get("status")).strip().lower() == "pending"]

    def update_user_status(self, email, new_status):
        """
        Atualiza o status de um utilizador específico na planilha 'users'.
        :param email: E-mail do utilizador.
        :param new_status: Novo status (ex: 'approved', 'rejected').
        """
        self._connect()  # Garante a conexão
        # Obtém a aba de utilizadores
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws:
            return
        try:
            # Encontra a célula com o e-mail na coluna 1
            cell = ws.find(email, in_column=1)
            if cell:
                # Atualiza a célula na coluna 6 (Status)
                ws.update_cell(cell.row, 6, new_status)
        except gspread.exceptions.CellNotFound:
            print(f"Usuário {email} não encontrado.")
        except Exception as e:
            print(f"Erro ao atualizar status do usuário {email}: {e}")

    def get_occurrence_by_id(self, occurrence_id):
        """
        Obtém os detalhes de uma ocorrência pelo seu ID.
        :param occurrence_id: ID da ocorrência.
        :return: Dicionário com os detalhes da ocorrência ou None se não for encontrada.
        """
        self._connect()  # Garante a conexão
        # Reutiliza get_all_occurrences que já normaliza títulos e chaves.
        for occ in self.get_all_occurrences():
            if str(occ.get('id')).strip().lower() == str(occurrence_id).strip().lower():
                return occ  # Retorna a ocorrência completa
        return None

    def update_occurrence_status(self, occurrence_id, new_status):
        """
        Atualiza o status de uma ocorrência específica.
        :param occurrence_id: ID da ocorrência.
        :param new_status: Novo status da ocorrência.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect()  # Garante a conexão
        sheet_name, status_col = None, 7  # Coluna padrão para status

        # Determina a aba correta e a coluna do status com base no prefixo do ID da ocorrência.
        occ_id_lower = str(occurrence_id).strip().lower()
        if 'scall' in occ_id_lower:
            sheet_name = self.SIMPLE_CALLS_SHEET
        elif 'call' in occ_id_lower:
            sheet_name = self.CALLS_SHEET
        elif 'equip' in occ_id_lower:
            sheet_name = self.EQUIPMENT_SHEET
            status_col = 6  # Coluna do status é diferente para equipamentos
        if not sheet_name:
            return False, "Tipo de ocorrência desconhecido."

        ws = self._get_worksheet(sheet_name)  # Obtém a aba
        if not ws:
            return False, f"Falha ao aceder à planilha {sheet_name}."

        try:
            # Encontra a célula com o ID da ocorrência
            cell = ws.find(occurrence_id, in_column=1)
            if cell:
                # Atualiza o status
                ws.update_cell(cell.row, status_col, new_status)
                return True, "Status atualizado com sucesso."
            else:
                return False, f"Ocorrência {occurrence_id} não encontrada."
        except gspread.exceptions.CellNotFound:
            return False, f"Ocorrência {occurrence_id} não encontrada na planilha {sheet_name}."
        except Exception as e:
            return False, f"Erro ao atualizar status da ocorrência {occurrence_id}: {e}"

    def register_simple_call_occurrence(self, user_email, data):
        """
        Regista uma nova ocorrência de chamada simplificada.
        :param user_email: E-mail do utilizador que está a registar.
        :param data: Dicionário com os dados do formulário da ocorrência.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect()  # Garante a conexão
        ws = self._get_worksheet(self.SIMPLE_CALLS_SHEET)  # Obtém a aba
        if not ws:
            return False, "Falha ao aceder à planilha."

        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Timestamp atual
            current_records = self._get_all_records_safe(ws)
            # Gera um novo ID único para a ocorrência.
            new_id = f"SCALL-{len([rec for rec in current_records if rec.get('id')]) + 1:04d}"

            user_profile = self.check_user_status(
                user_email)  # Obtém o perfil do utilizador
            # Define um título padrão para a ocorrência.
            title_to_register = f"CHAMADA SIMPLES DE {data.get('origem', 'N/A')} PARA {data.get('destino', 'N/A')}"

            # Prepara a nova linha com todos os dados.
            new_row = [
                new_id, now, title_to_register,
                user_email, user_profile.get(
                    "name", "N/A"), user_profile.get("username", "N/A"),
                'REGISTRADO', data.get('origem'), data.get(
                    'destino'), data.get('descricao'),
                user_profile.get(
                    "main_group", "N/A"), user_profile.get("company", "")
            ]
            # Adiciona a linha
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Ocorrência registrada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao registrar: {e}"

    def register_equipment_occurrence(self, user_credentials, user_email, data, attachment_paths):
        """
        Regista uma nova ocorrência de suporte a equipamento.
        Faz upload de anexos para o Google Drive.
        :param user_credentials: Credenciais OAuth do utilizador para upload no Drive.
        :param user_email: E-mail do utilizador.
        :param data: Dicionário com os dados do formulário.
        :param attachment_paths: Lista de caminhos locais para os ficheiros anexados.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect()  # Garante a conexão
        ws = self._get_worksheet(self.EQUIPMENT_SHEET)  # Obtém a aba
        if not ws:
            return False, "Falha ao aceder à planilha de equipamentos."

        # Tenta fazer o upload dos ficheiros para o Google Drive.
        upload_success, result = self._upload_files_to_drive(
            user_credentials, attachment_paths)
        if not upload_success:
            return False, result  # Retorna erro se o upload falhar

        # Converte a lista de links para JSON string
        attachment_links_json = json.dumps(result)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        current_records = self._get_all_records_safe(ws)
        new_id = f"EQUIP-{len([rec for rec in current_records if rec.get('id')]) + 1:04d}"

        user_profile = self.check_user_status(user_email)

        # Título baseado no tipo de equipamento
        title_to_register = data.get('tipo', f"EQUIPAMENTO {new_id}")
        new_row = [
            new_id, now, user_email, user_profile.get(
                "name", "N/A"), user_profile.get("username", "N/A"),
            'REGISTRADO', title_to_register, data.get(
                'modelo'), data.get('ramal'),
            data.get('localizacao'), data.get(
                'descricao'), attachment_links_json,
            user_profile.get(
                "main_group", "N/A"), user_profile.get("company", "")
        ]
        try:
            # Adiciona a linha
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Ocorrência de equipamento registrada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao registrar a ocorrência de equipamento: {e}"

    def register_full_occurrence(self, user_email, title, testes):
        """
        Regista uma nova ocorrência de chamada detalhada.
        :param user_email: E-mail do utilizador.
        :param title: Título da ocorrência.
        :param testes: Lista de dicionários com os dados dos testes de ligação.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect()  # Garante a conexão
        ws = self._get_worksheet(self.CALLS_SHEET)  # Obtém a aba
        if not ws:
            return False, "Falha ao aceder à planilha de chamadas."

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        current_records = self._get_all_records_safe(ws)
        new_id = f"CALL-{len([rec for rec in current_records if rec.get('id')]) + 1:04d}"

        user_profile = self.check_user_status(user_email)

        # Extrai informações dos testes para as colunas principais (Operadora A, Operadora B, Descrição)
        # O restante dos testes é salvo como JSON.
        op_a = testes[0]['op_a'] if testes and isinstance(
            testes, list) and len(testes) > 0 else 'N/A'
        op_b = testes[0]['op_b'] if testes and isinstance(
            testes, list) and len(testes) > 0 else 'N/A'
        description = testes[0]['obs'] if testes and isinstance(
            testes, list) and len(testes) > 0 else ""
        # Converte a lista de testes para JSON string
        testes_json = json.dumps(testes)

        new_row = [
            new_id, now, title, user_email, user_profile.get(
                "name", "N/A"), user_profile.get("username", "N/A"),
            'REGISTRADO', op_a, op_b, testes_json, description,
            user_profile.get(
                "main_group", "N/A"), user_profile.get("company", "")
        ]
        try:
            # Adiciona a linha
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Ocorrência detalhada registrada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao registrar: {e}"

    def add_occurrence_comment(self, occurrence_id, user_email, user_name, comment_text):
        """
        Adiciona um novo comentário a uma ocorrência específica.
        :param occurrence_id: ID da ocorrência à qual o comentário pertence.
        :param user_email: E-mail do autor do comentário.
        :param user_name: Nome do autor do comentário.
        :param comment_text: O texto do comentário.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect()  # Garante a conexão
        # Obtém a aba de comentários
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET)
        if not ws:
            return False, "Falha ao aceder à planilha de comentários."

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Gera um ID único para o comentário baseado em timestamp.
        comment_id = f"COM-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        new_row = [
            occurrence_id,
            comment_id,
            user_email,
            user_name,
            now,
            comment_text
        ]
        try:
            # Adiciona a nova linha
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Comentário adicionado com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao adicionar o comentário: {e}"

    def update_occurrence_comment(self, comment_id, new_comment_text):
        """
        Atualiza o texto de um comentário existente.
        :param comment_id: ID do comentário a ser atualizado.
        :param new_comment_text: O novo texto do comentário.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect()  # Garante a conexão
        # Obtém a aba de comentários
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET)
        if not ws:
            return False, "Falha ao aceder à planilha de comentários."

        try:
            # Encontra a célula com o ID do comentário (coluna 2)
            cell = ws.find(comment_id, in_column=2)
            if cell:
                # Atualiza a célula na coluna 6 (Comentario)
                ws.update_cell(cell.row, 6, new_comment_text)
                return True, "Comentário atualizado com sucesso."
            else:
                return False, f"Comentário com ID {comment_id} não encontrado."
        except gspread.exceptions.CellNotFound:
            return False, f"Comentário com ID {comment_id} não encontrado na planilha de comentários."
        except Exception as e:
            return False, f"Erro ao atualizar o comentário {comment_id}: {e}"

    def delete_occurrence_comment(self, comment_id):
        """
        Elimina um comentário da planilha.
        :param comment_id: ID do comentário a ser eliminado.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect()  # Garante a conexão
        # Obtém a aba de comentários
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET)
        if not ws:
            return False, "Falha ao aceder à planilha de comentários."

        try:
            # Encontra a célula com o ID do comentário (coluna 2)
            cell = ws.find(comment_id, in_column=2)
            if cell:
                # Exclui a linha inteira onde o comentário foi encontrado
                ws.delete_rows(cell.row)
                return True, "Comentário eliminado com sucesso."
            else:
                return False, f"Comentário com ID {comment_id} não encontrado."
        except gspread.exceptions.CellNotFound:
            return False, f"Comentário com ID {comment_id} não encontrado na planilha de comentários."
        except Exception as e:
            return False, f"Erro ao eliminar o comentário {comment_id}: {e}"

    def get_occurrence_comments(self, occurrence_id):
        """
        Obtém todos os comentários associados a uma ocorrência específica.
        :param occurrence_id: ID da ocorrência.
        :return: Lista de dicionários, cada um representando um comentário, ordenados por data.
        """
        self._connect()  # Garante a conexão
        # Obtém a aba de comentários
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET)
        if not ws:
            return []

        try:
            all_comments = self._get_all_records_safe(
                ws)  # Obtém todos os comentários
            # Filtra os comentários pelo ID da ocorrência e ordena por data.
            filtered_comments = [
                comment for comment in all_comments
                if comment.get('id_ocorrencia') and str(comment['id_ocorrencia']).strip().lower() == str(occurrence_id).strip().lower()
            ]
            # Ordena por 'Data_Comentario' (a chave original da planilha), do mais recente para o mais antigo.
            return sorted(filtered_comments, key=lambda x: x.get('Data_Comentario', ''), reverse=True)
        except Exception as e:
            print(
                f"Erro ao obter comentários da ocorrência {occurrence_id}: {e}")
            return []
