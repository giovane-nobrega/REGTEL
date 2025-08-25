# ==============================================================================
# FICHEIRO: src/services/sheets_service.py
# DESCRIÇÃO: Lida com todas as operações de leitura e escrita na planilha
#            Google Sheets, otimizado com operações em lote.
#            Gere o acesso a diferentes abas (folhas) e tipos de ocorrências.
#            CORRIGIDO: Lógica de filtragem para o grupo PREFEITURA e tratamento de NoneType.
#            CORRIGIDO: Uso da chave normalizada 'registradormaingroup'.
# ==============================================================================

import gspread # Biblioteca Python para interagir com a Google Sheets API
import json # Usado para serializar/desserializar dados JSON (ex: testes, anexos)
import csv # Usado para exportação de dados CSV (se implementado)
from datetime import datetime # Usado para timestamps
from googleapiclient.http import MediaFileUpload # Usado para upload de ficheiros para o Google Drive
import os # Usado para operações de sistema de ficheiros
from tkinter import messagebox # Usado para exibir mensagens de erro/informação
import threading # Usado para garantir segurança de thread ao aceder a recursos compartilhados (gspread)
from builtins import Exception, print, len, str, sorted, list, set, enumerate, dict, bool, isinstance, range # CORRIGIDO: Importa built-ins explicitamente para satisfazer o Pylance

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
        self.auth_service = auth_service_instance # Referência ao serviço de autenticação
        
        # --- IDs e Nomes de Planilhas/Abas ---
        # ATUALIZE: SPREADSHEET_ID com o ID da sua planilha principal do Google Sheets.
        self.SPREADSHEET_ID = "1ymzB0QiZiuTnLk9h3qfFnZgcxkTKJUeT-3rn4bYqtQA" 
        self.USERS_SHEET = "users" # Aba para gerenciar utilizadores e seus status
        self.CALLS_SHEET = "call_occurrences" # Aba para ocorrências de chamada detalhadas
        self.SIMPLE_CALLS_SHEET = "simple_call_occurrences" # Aba para ocorrências de chamada simplificadas
        self.EQUIPMENT_SHEET = "equipment_occurrences" # Aba para ocorrências de equipamento
        self.OCCURRENCE_COMMENTS_SHEET = "occurrence_comments" # Nova aba para armazenar comentários de ocorrências

        self.gspread_lock = threading.Lock() # Um lock para garantir que as operações do gspread sejam thread-safe
        self._GC = None # Cliente gspread (Google Client)
        self._SPREADSHEET = None # Objeto da planilha aberta
        self.is_connected = False # Flag para verificar o estado da conexão

    def _connect(self):
        """
        Conecta-se ao Google Sheets usando as credenciais da conta de serviço.
        A conexão é estabelecida apenas uma vez (singleton pattern) e é thread-safe.
        """
        if self.is_connected:
            return # Já conectado, não faz nada

        with self.gspread_lock: # Adquire o lock para garantir que apenas uma thread se conecta por vez
            if self.is_connected:
                return # Dupla verificação dentro do lock

            # Obtém as credenciais da conta de serviço do AuthService.
            self._SERVICE_CREDENTIALS = self.auth_service.get_service_account_credentials()
            if not self._SERVICE_CREDENTIALS:
                return # Não foi possível obter as credenciais, retorna

            try:
                # Autentica com o gspread usando o ficheiro de credenciais da conta de serviço.
                self._GC = gspread.service_account(filename=self.auth_service.SERVICE_ACCOUNT_FILE)
                # Abre a planilha pelo seu ID.
                self._SPREADSHEET = self._GC.open_by_key(self.SPREADSHEET_ID)
                self.is_connected = True # Marca a conexão como bem-sucedida
            except Exception as e:
                 messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao Google Sheets: {e}")

    def _get_worksheet(self, sheet_name):
        """
        Obtém uma aba (worksheet) específica da planilha.
        :param sheet_name: O nome da aba (string).
        :return: O objeto da aba (Worksheet) ou None se não for encontrada ou houver erro.
        """
        self._connect() # Garante que a conexão com o Google Sheets está estabelecida
        if not self._SPREADSHEET: return None # Se a planilha não foi aberta, retorna None

        try:
            return self._SPREADSHEET.worksheet(sheet_name) # Retorna a aba pelo nome
        except gspread.exceptions.WorksheetNotFound:
            print(f"ERRO: A aba '{sheet_name}' não foi encontrada na planilha.")
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
        with self.gspread_lock: # Adquire o lock para garantir acesso exclusivo à aba durante a leitura
            raw_records = worksheet.get_all_records() # Obtém todos os registos como uma lista de dicionários
            processed_records = []
            for rec in raw_records:
                processed_rec = dict() # Usando dict explicitamente
                for k, v in rec.items():
                    original_key = k # Mantém a chave original (como está na planilha)
                    normalized_key = k.strip().lower() # Cria uma versão normalizada (minúsculas, sem espaços)

                    processed_rec[original_key] = v # Armazena o valor com a chave original
                    if original_key != normalized_key: # Evita duplicação se a chave já for normalizada
                        processed_rec[normalized_key] = v # Armazena o valor com a chave normalizada
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
        if not file_paths: return bool(True), list() # Usando bool e list explicitamente
        
        drive_service = self.auth_service.get_drive_service(user_credentials) # Obtém o serviço do Google Drive
        if not drive_service: return bool(False), "Não foi possível obter o serviço do Google Drive."

        try:
            # Procura por uma pasta existente chamada "Craft Quest Anexos"
            q = "mimeType='application/vnd.google-apps.folder' and name='Craft Quest Anexos' and trashed=false"
            response = drive_service.files().list(q=q, spaces='drive', fields='files(id, name)').execute()
            
            folder_id = None
            if response.get('files'):
                folder_id = response.get('files')[0].get('id') # Usa a primeira pasta encontrada
            else:
                # Se a pasta não existir, cria uma nova.
                folder_metadata = {'name': 'Craft Quest Anexos', 'mimeType': 'application/vnd.google-apps.folder'}
                folder_id = drive_service.files().create(body=folder_metadata, fields='id').execute().get('id')

            uploaded_file_links = list() # Usando list explicitamente
            for file_path in file_paths:
                file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
                media = MediaFileUpload(file_path, resumable=True) # Prepara o ficheiro para upload resumível
                file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
                
                # Torna o ficheiro publicamente acessível (qualquer uno pode ler)
                # ATENÇÃO: Reavalie esta permissão se os anexos puderem conter dados sensíveis.
                # Se o acesso público não for estritamente necessário, remova esta linha ou restrinja o acesso.
                drive_service.permissions().create(fileId=file.get('id'), body={'role': 'reader', 'type': 'anyone'}).execute()
                uploaded_file_links.append(file.get('webViewLink')) # Adiciona o link de visualização

            return bool(True), uploaded_file_links # Usando bool explicitamente
        except Exception as e:
            return bool(False), f"Ocorreu um erro durante o upload para o Google Drive: {e}"

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
        self._connect() # Garante a conexão
        if not self._SPREADSHEET: return bool(False), "Falha na conexão."

        updates_by_sheet = dict() # Usando dict explicitamente
        updates_by_sheet[self.CALLS_SHEET] = list()
        updates_by_sheet[self.SIMPLE_CALLS_SHEET] = list()
        updates_by_sheet[self.EQUIPMENT_SHEET] = list()


        all_ids_map = dict() # Usando dict explicitamente
        # Mapeia todos os IDs de ocorrência para suas abas e linhas.
        for sheet_name in updates_by_sheet.keys(): # CORRIGIDO: Era updates_by_sheets
            ws = self._get_worksheet(sheet_name)
            if ws:
                ids_in_sheet = ws.col_values(1) # Obtém todos os valores da primeira coluna (IDs)
                for i in range(len(ids_in_sheet)): # Usando range e len explicitamente
                    if i == 0: continue # Ignora o cabeçalho
                    all_ids_map[ids_in_sheet[i]] = {'sheet': sheet_name, 'row': i + 1} # Armazena a aba e a linha

        # Prepara as células a serem atualizadas.
        for occ_id, new_status in changes.items():
            if occ_id in all_ids_map:
                info = all_ids_map[occ_id]
                sheet_name = info['sheet']
                # A coluna do status é diferente para ocorrências de equipamento (coluna 6) e outras (coluna 7).
                status_col = 6 if sheet_name == self.EQUIPMENT_SHEET else 7
                updates_by_sheet[sheet_name].append(gspread.Cell(info['row'], status_col, value=new_status))

        try:
            with self.gspread_lock: # Adquire o lock para operações em lote seguras
                for sheet_name, cells_to_update in updates_by_sheet.items():
                    if cells_to_update:
                        ws = self._get_worksheet(sheet_name)
                        if ws: ws.update_cells(cells_to_update) # Realiza a atualização em lote para cada aba
            return bool(True), "Alterações salvas com sucesso." # Usando bool explicitamente
        except Exception as e:
            return bool(False), f"Erro na atualização em lote: {e}" # Usando bool explicitamente

    def batch_update_user_profiles(self, changes: dict):
        """
        Atualiza múltiplos perfis de utilizador de uma só vez usando operações em lote.
        :param changes: Dicionário onde a chave é o e-mail do utilizador e o valor é um dicionário
                        com as mudanças de perfil (main_group, sub_group, company).
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect() # Garante a conexão
        ws = self._get_worksheet(self.USERS_SHEET) # Obtém a aba de utilizadores
        if not ws: return bool(False), "Falha na conexão com a aba de utilizadores." # Usando bool explicitamente

        emails_in_sheet = ws.col_values(1) # Obtém todos os e-mails da primeira coluna
        # Mapeia e-mails normalizados para suas linhas na planilha.
        all_users_map = {str(emails_in_sheet[i]).strip().lower(): {'row': i + 1} # Usando str explicitamente
                         for i in range(1, len(emails_in_sheet)) if str(emails_in_sheet[i]).strip()} # Usando str e len explicitamente

        cells_to_update = list() # Usando list explicitamente
        # Prepara as células a serem atualizadas.
        for email, profile_changes in changes.items():
            normalized_email = email.strip().lower()
            if normalized_email in all_users_map:
                row = all_users_map[normalized_email]['row']
                # Adiciona células para atualizar Grupo Principal (col 4), Subgrupo (col 5), Empresa (col 7)
                cells_to_update.append(gspread.Cell(row, 4, value=profile_changes['main_group']))
                cells_to_update.append(gspread.Cell(row, 5, value=profile_changes['sub_group']))
                cells_to_update.append(gspread.Cell(row, 7, value=profile_changes['company']))

        try:
            with self.gspread_lock: # Adquire o lock para operações em lote seguras
                if cells_to_update:
                    ws.update_cells(cells_to_update) # Realiza a atualização em lote
            return bool(True), "Perfis atualizados com sucesso." # Usando bool explicitamente
        except Exception as e:
            return bool(False), f"Erro na atualização de perfis em lote: {e}" # Usando bool explicitamente

    # ==============================================================================
    # --- MÉTODOS DE LEITURA E ESCRITA DE OCORRÊNCIAS/UTILIZADORES ---
    # ==============================================================================

    def check_user_status(self, email):
        """
        Verifica o status e o perfil de um utilizador na planilha 'users'.
        :param email: E-mail do utilizador a ser verificado.
        :return: Dicionário com os dados do perfil do utilizador ou status de erro/não registado.
        """
        self._connect() # Garante a conexão
        ws = self._get_worksheet(self.USERS_SHEET) # Obtém a aba de utilizadores
        if not ws: return dict(status="error") # Usando dict explicitamente
        try:
            records = self._get_all_records_safe(ws) # Obtém todos os registos com chaves normalizadas
            for user_rec in records:
                if user_rec.get("email") and str(user_rec["email"]).strip().lower() == str(email).strip().lower(): # Usando str explicitamente
                    return user_rec # Retorna o dicionário completo do perfil
        except Exception as e:
            print(f"Erro ao ler a planilha de usuários: {e}") # Usando print explicitamente
            return dict(status="error") # Usando dict explicitamente
        return dict(status="unregistered") # Usando dict explicitamente

    def get_all_occurrences(self):
        """
        Obtém todas as ocorrências de todas as abas (chamadas detalhadas, simples, equipamento).
        Normaliza os títulos das ocorrências para exibição consistente.
        :return: Lista de todas as ocorrências, ordenadas pela data de registo (mais recente primeiro).
        """
        self._connect() # Garante a conexão
        calls_ws = self._get_worksheet(self.CALLS_SHEET)
        simple_calls_ws = self._get_worksheet(self.SIMPLE_CALLS_SHEET)
        equip_ws = self._get_worksheet(self.EQUIPMENT_SHEET)

        all_occurrences = list() # Usando list explicitamente

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
                if value is not None and str(value).strip() != "": # Usando str explicitamente
                    return str(value).strip() # Usando str explicitamente

            # Se nenhum título do utilizador for encontrado, gera um padrão.
            record_id = record.get('id', 'N/A')
            if record_type == "call":
                return f"Chamada Detalhada {record_id}"
            elif record_type == "simple_call":
                return f"Chamada Simples de {record.get('origem', 'N/A')} para {record.get('destino', 'N/A')}"
            elif record_type == "equipment":
                return record.get('tipo de equipamento', f"Equipamento {record_id}")

            return f"Ocorrência {record_id}" # Fallback final

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
                    rec['Título da Ocorrência'] = get_final_title(rec, "simple_call")
                    all_occurrences.append(rec)

        # Processa ocorrências de equipamento.
        if equip_ws:
            equip_records = self._get_all_records_safe(equip_ws)
            for rec in equip_records:
                if rec.get('id'):
                    rec['Título da Ocorrência'] = get_final_title(rec, "equipment")
                    all_occurrences.append(rec)

        # Retorna os registos ordenados pela data de registo (mais recente primeiro).
        return sorted(all_occurrences, key=lambda x: x.get('Data de Registro', ''), reverse=True) # Usando sorted explicitamente


    def get_occurrences_by_user(self, user_email):
        """
        Obtém as ocorrências visíveis para um utilizador específico,
        filtrando com base no seu perfil e empresa/departamento.
        :param user_email: E-mail do utilizador.
        :return: Lista de ocorrências visíveis para o utilizador.
        """
        self._connect() # Garante a conexão
        user_profile = self.check_user_status(user_email) # Obtém o perfil do utilizador
        
        # --- DEBUG: Informações do Perfil do Utilizador ---
        print(f"\n=== DEBUG get_occurrences_by_user ===")
        print("Usuário:", user_email, "Grupo:", user_profile.get("main_group"))
        # ----------------------------------------------------

        if not user_profile or user_profile.get('status') != 'approved':
            print("DEBUG: Utilizador não aprovado ou perfil não encontrado. Retornando lista vazia.") # Usando print explicitamente
            return list() # Usando list explicitamente

        main_group = user_profile.get("main_group", "").strip().upper()
        user_company = user_profile.get("company", "").strip().upper()
        user_sub_group = user_profile.get("sub_group", "").strip().upper() # Pega o subgrupo do utilizador

        all_occurrences = self.get_all_occurrences() # Obtém TODAS as ocorrências
        filtered_list = list() # Lista para armazenar as ocorrências filtradas

        # --- DEBUG: Informações sobre as ocorrências ---
        if all_occurrences:
            print("OCC KEYS (primeira ocorrência):", list(all_occurrences[0].keys()))
            print("OCC SAMPLE (primeira ocorrência):", all_occurrences[0])
        else:
            print("Nenhuma ocorrência carregada.")
        # ------------------------------------------------

        print(f"DEBUG: Grupo Principal: {main_group}, Subgrupo do Utilizador: '{user_sub_group}', Empresa do Utilizador: '{user_company}'") # Usando print explicitamente
        print(f"DEBUG: Total de ocorrências carregadas (antes do filtro): {len(all_occurrences)}") # Usando print e len explicitamente

        # Lógica de filtragem baseada no grupo e subgrupo do utilizador.
        
        # 67 Telecom users (todos os subgrupos) veem todas as ocorrências.
        if main_group == '67_TELECOM':
            print("DEBUG: Grupo 67_TELECOM detectado. Retornando TODAS as ocorrências.") # Usando print explicitamente
            return all_occurrences

        # Parceiros:
        # 1. Não devem ver ocorrências de equipamento.
        # 2. Não devem ver ocorrências de chamada simples.
        # 3. Devem ver ocorrências de chamada detalhada (CALL) onde a 'Registrador Company' corresponde à sua 'user_company'.
        elif main_group == 'PARTNER':
            if not user_company:
                print(f"AVISO: Utilizador {user_email} do grupo {main_group} não tem empresa definida. Retornando lista vazia.") # Usando print explicitamente
                return list() # Usando list explicitamente
            
            for occ in all_occurrences:
                occurrence_id = occ.get('id', '').strip().upper() # Usando a chave normalizada 'id'
                occ_registrador_company = occ.get('registrador company', '').strip().upper() # Usando a chave normalizada 'registrador company'

                # Excluir ocorrências de equipamento para utilizadores PARTNER
                if 'EQUIP' in occurrence_id:
                    print(f"DEBUG PARTNER: Excluindo ocorrência de equipamento ID: {occurrence_id}")
                    continue # Pula esta ocorrência

                # Excluir ocorrências de chamada simples para utilizadores PARTNER
                if 'SCALL' in occurrence_id:
                    print(f"DEBUG PARTNER: Excluindo ocorrência de chamada simples ID: {occurrence_id}")
                    continue # Pula esta ocorrência

                # Incluir ocorrências de chamada detalhada (CALL) se a empresa corresponder
                if 'CALL' in occurrence_id and occ_registrador_company == user_company:
                    filtered_list.append(occ)
                    print(f"DEBUG PARTNER: Incluindo ocorrência detalhada ID: {occurrence_id} (Empresa Registradora: {occ_registrador_company} == Empresa do Usuário: {user_company})")
                else:
                    print(f"DEBUG PARTNER: Excluindo ocorrência ID: {occurrence_id} (Não é CALL ou empresa não corresponde)")

            print(f"DEBUG: Grupo '{main_group}' detectado. Filtrando por empresa '{user_company}', excluindo equipamentos e chamadas simples. Ocorrências filtradas: {len(filtered_list)}") # Usando print e len explicitamente
            return filtered_list

        # Prefeitura:
        # Devem ver:
        # 1. Suas próprias ocorrências (qualquer tipo: CALL, SCALL, EQUIP)
        # 2. Ocorrências de EQUIPAMENTO ('EQUIP') registradas por utilizadores '67_TELECOM'
        # 3. Ocorrências de CHAMADA SIMPLES ('SCALL') registradas por utilizadores '67_TELECOM'
        elif main_group == 'PREFEITURA':
            for occ in all_occurrences:
                # Tenta pegar tanto a chave normalizada quanto a original para robustez
                occ_group = (str(occ.get("registradormaingroup") or occ.get("RegistradorMainGroup") or "")).upper()
                occ_id = occ.get("id", "") # Usar a chave normalizada 'id'

                # Condição para incluir ocorrências:
                # 1. Se a ocorrência foi registrada por um usuário da PREFEITURA (qualquer tipo)
                # OU
                # 2. Se a ocorrência é de EQUIPAMENTO E foi registrada por um usuário da 67_TELECOM
                # OU
                # 3. Se a ocorrência é de CHAMADA SIMPLES E foi registrada por um usuário da 67_TELECOM
                if (occ_group == "PREFEITURA" or
                    (occ_id.startswith("EQUIP") and occ_group == "67_TELECOM") or
                    (occ_id.startswith("SCALL") and occ_group == "67_TELECOM")):
                    filtered_list.append(occ)
                    print(f"DEBUG PREFEITURA: Incluindo ocorrência ID: {occ_id} (Registrador Main Group: {occ_group})")
                else:
                    print(f"DEBUG PREFEITURA: Excluindo ocorrência ID: {occ_id} (Não corresponde às regras da Prefeitura)")

            print(f"DEBUG: Grupo '{main_group}' detectado. Ocorrências filtradas: {len(filtered_list)}") # Usando print e len explicitamente
            return filtered_list

        print(f"DEBUG: Perfil '{main_group}' não mapeado para regras de visualização. Retornando lista vazia.") # Usando print explicitamente
        return list() # Usando list explicitamente

    def get_active_occurrences_for_admin_dashboard(self):
        """
        Obtém todas as ocorrências e filtra aquelas com status 'RESOLVIDO' ou 'CANCELADO',
        destinadas à exibição no dashboard de gestão do administrador.
        :return: Lista de ocorrências ativas.
        """
        all_occurrences = self.get_all_occurrences() # Obtém todas as ocorrências

        # Define os status que são considerados "ativos" para o dashboard.
        active_statuses = ["REGISTRADO", "EM ANÁLISE", "AGUARDANDO TERCEIROS", "PARCIALMENTE RESOLVIDO"]

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
        self._connect() # Garante a conexão
        ws = self._get_worksheet(self.USERS_SHEET) # Obtém a aba de utilizadores
        if not ws: return list() # Usando list explicitamente
        return [rec for rec in self._get_all_records_safe(ws) if rec.get("email")] # Usando list explicitamente

    def get_all_operators(self):
        """
        Obtém uma lista de todas as operadoras de telefonia,
        incluindo uma base predefinida e operadoras encontradas nas ocorrências.
        :return: Lista ordenada de operadoras únicas.
        """
        self._connect() # Garante a conexão
        # Conjunto de operadoras base predefinidas.
        base_operators = set({"VIVO", "CLARO", "TIM", "OI", "ALGAR TELECOM", "SERCOMTEL", "NEXTEL", "VULCANET", "CTBC TELECOM", "UNO INTERNET", "VIVO FIXO", "CLARO FIXO", "OI FIXO", "EMBRATEL"}) # Usando set explicitamente
        
        ws = self._get_worksheet(self.CALLS_SHEET) # Obtém a aba de chamadas detalhadas
        if not ws: return sorted(list(base_operators)) # Usando sorted e list explicitamente

        try:
            records = self._get_all_records_safe(ws) # Obtém os registos de chamadas
            sheet_operators = set() # Usando set explicitamente
            for rec in records:
                op_a = rec.get('operadora a') # Obtém operadora A (chave normalizada)
                op_b = rec.get('operadora b') # Obtém operadora B (chave normalizada)
                if op_a and str(op_a).strip() != "": # Usando str explicitamente
                    sheet_operators.add(str(op_a).strip().upper()) # Usando str explicitamente
                if op_b and str(op_b).strip() != "": # Usando str explicitamente
                    sheet_operators.add(str(op_b).strip().upper()) # Usando str explicitamente
            base_operators.update(sheet_operators) # Adiciona operadoras encontradas às base
        except Exception as e:
            print(f"Erro ao ler operadoras da planilha: {e}") # Usando print explicitamente
        return sorted(list(base_operators)) # Usando sorted e list explicitamente

    def request_access(self, email, full_name, username, main_group, sub_group, company_name=None):
        """
        Envia uma solicitação de acesso para um novo utilizador para a planilha 'users'.
        Verifica se o e-mail já existe antes de adicionar.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect() # Garante a conexão
        ws = self._get_worksheet(self.USERS_SHEET) # Obtém a aba de utilizadores
        if not ws: return bool(False), "Falha ao aceder à planilha." # Usando bool explicitamente

        try:
            all_users_records = self._get_all_records_safe(ws) # Obtém todos os utilizadores
            normalized_emails_in_sheet = [str(rec.get('email', '')).strip().lower() for rec in all_users_records] # Usando str explicitamente

            if str(email).strip().lower() in normalized_emails_in_sheet: # Usando str explicitamente
                return bool(False), "Solicitação já existe para este e-mail." # Usando bool explicitamente
        except Exception as e:
            return bool(False), f"Erro ao verificar e-mail existente: {e}" # Usando bool explicitamente

        # Prepara a nova linha com os dados da solicitação.
        new_row = [
            email,              # Coluna 1: Email
            full_name,          # Coluna 2: Nome Completo
            username,           # Coluna 3: Username
            main_group,         # Coluna 4: Grupo Principal
            sub_group,          # Coluna 5: Subgrupo
            "pending",          # Coluna 6: Status inicial como "pending"
            company_name or ""  # Coluna 7: Empresa/Departamento (vazio se None)
        ]
        try:
            ws.append_row(new_row, value_input_option='USER_ENTERED') # pyright: ignore[reportArgumentType] # Adiciona a nova linha
            return bool(True), "Solicitação de acesso enviada com sucesso." # Usando bool explicitamente
        except Exception as e:
            return bool(False), f"Ocorreu um erro ao enviar a solicitação: {e}" # Usando bool explicitamente

    def get_pending_requests(self):
        """
        Obtém todas as solicitações de acesso de utilizadores com status 'pending'.
        :return: Lista de dicionários, cada um representando uma solicitação pendente.
        """
        self._connect() # Garante a conexão
        ws = self._get_worksheet(self.USERS_SHEET) # Obtém a aba de utilizadores
        if not ws: return list() # Usando list explicitamente
        all_users = self._get_all_records_safe(ws) # Obtém todos os utilizadores
        return [user for user in all_users if user.get("status") and str(user.get("status")).strip().lower() == "pending"] # Usando str explicitamente

    def update_user_status(self, email, new_status):
        """
        Atualiza o status de um utilizador específico na planilha 'users'.
        :param email: E-mail do utilizador.
        :param new_status: Novo status (ex: 'approved', 'rejected').
        """
        self._connect() # Garante a conexão
        ws = self._get_worksheet(self.USERS_SHEET) # Obtém a aba de utilizadores
        if not ws: return
        try:
            cell = ws.find(email, in_column=1) # Encontra a célula com o e-mail na coluna 1
            if cell: ws.update_cell(cell.row, 6, new_status) # Atualiza a célula na coluna 6 (Status)
        except gspread.exceptions.CellNotFound: print(f"Usuário {email} não encontrado.") # pyright: ignore[reportAttributeAccessIssue] # Usando print explicitamente
        except Exception as e: print(f"Erro ao atualizar status do usuário {email}: {e}") # Usando print explicitamente

    def get_occurrence_by_id(self, occurrence_id):
        """
        Obtém os detalhes de uma ocorrência pelo seu ID.
        :param occurrence_id: ID da ocorrência.
        :return: Dicionário com os detalhes da ocorrência ou None se não for encontrada.
        """
        self._connect() # Garante a conexão
        # Reutiliza get_all_occurrences que já normaliza títulos e chaves.
        for occ in self.get_all_occurrences():
            if str(occ.get('id')).strip().lower() == str(occurrence_id).strip().lower(): # Usando str explicitamente
                return occ # Retorna a ocorrência completa
        return None

    def update_occurrence_status(self, occurrence_id, new_status):
        """
        Atualiza o status de uma ocorrência específica.
        :param occurrence_id: ID da ocorrência.
        :param new_status: Novo status da ocorrência.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect() # Garante a conexão
        sheet_name, status_col = None, 7 # Coluna padrão para status
        
        # Determina a aba correta e a coluna do status com base no prefixo do ID da ocorrência.
        occ_id_lower = str(occurrence_id).strip().lower() # Usando str explicitamente
        if 'scall' in occ_id_lower: sheet_name = self.SIMPLE_CALLS_SHEET
        elif 'call' in occ_id_lower: sheet_name = self.CALLS_SHEET
        elif 'equip' in occ_id_lower:
            sheet_name = self.EQUIPMENT_SHEET
            status_col = 6 # Coluna do status é diferente para equipamentos
        if not sheet_name: return bool(False), "Tipo de ocorrência desconhecido." # Usando bool explicitamente

        ws = self._get_worksheet(sheet_name) # Obtém a aba
        if not ws: return bool(False), f"Falha ao aceder à planilha {sheet_name}." # Usando bool explicitamente

        try:
            cell = ws.find(occurrence_id, in_column=1) # Encontra a célula com o ID do comentário (coluna 2)
            if cell:
                ws.update_cell(cell.row, status_col, new_status) # Atualiza a célula na coluna correta (status_col)
                return bool(True), "Status atualizado com sucesso." # Usando bool explicitamente
            else:
                return bool(False), f"Ocorrência {occurrence_id} não encontrada." # Usando bool explicitamente
        except gspread.exceptions.CellNotFound: # pyright: ignore[reportAttributeAccessIssue]
            return bool(False), f"Ocorrência com ID {occurrence_id} não encontrada na planilha {sheet_name}." # Usando bool explicitamente
        except Exception as e:
            return bool(False), f"Erro ao atualizar o status da ocorrência {occurrence_id}: {e}" # Usando bool explicitamente

    def register_simple_call_occurrence(self, user_email, data):
        """
        Regista uma nova ocorrência de chamada simplificada.
        :param user_email: E-mail do utilizador que está a registar.
        :param data: Dicionário com os dados do formulário da ocorrência.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect() # Garante a conexão
        ws = self._get_worksheet(self.SIMPLE_CALLS_SHEET) # Obtém a aba
        if not ws: return bool(False), "Falha ao aceder à planilha." # Usando bool explicitamente

        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Timestamp atual
            current_records = self._get_all_records_safe(ws)
            # Gera um novo ID único para a ocorrência.
            new_id = f"SCALL-{len([rec for rec in current_records if rec.get('id')]) + 1:04d}" # Usando len explicitamente

            user_profile = self.check_user_status(user_email) # Obtém o perfil do utilizador
            # Define um título padrão para a ocorrência.
            title_to_register = f"CHAMADA SIMPLES DE {data.get('origem', 'N/A')} PARA {data.get('destino', 'N/A')}"
            
            # Prepara a nova linha com todos os dados.
            new_row = [
                new_id, now, title_to_register,
                user_email, user_profile.get("name", "N/A"), user_profile.get("username", "N/A"),
                'REGISTRADO', data.get('origem'), data.get('destino'), data.get('descricao'),
                user_profile.get("main_group", "N/A"), user_profile.get("company", "")
            ]
            ws.append_row(new_row, value_input_option='USER_ENTERED') # pyright: ignore[reportArgumentType] # Adiciona a linha
            return bool(True), "Ocorrência registrada com sucesso." # Usando bool explicitamente
        except Exception as e:
            return bool(False), f"Ocorreu um erro ao registrar: {e}" # Usando bool explicitamente

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
        self._connect() # Garante a conexão
        ws = self._get_worksheet(self.EQUIPMENT_SHEET) # Obtém a aba
        if not ws: return bool(False), "Falha ao aceder à planilha de equipamentos." # Usando bool explicitamente

        # Tenta fazer o upload dos ficheiros para o Google Drive.
        upload_success, result = self._upload_files_to_drive(user_credentials, attachment_paths)
        if not upload_success: return bool(False), result # Usando bool explicitamente

        attachment_links_json = json.dumps(result) # Converte a lista de links para JSON string
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        current_records = self._get_all_records_safe(ws)
        new_id = f"EQUIP-{len([rec for rec in current_records if rec.get('id')]) + 1:04d}" # Usando len explicitamente

        user_profile = self.check_user_status(user_email)

        title_to_register = data.get('tipo', f"EQUIPAMENTO {new_id}") # Título baseado no tipo de equipamento
        new_row = [
            new_id, now, user_email, user_profile.get("name", "N/A"), user_profile.get("username", "N/A"),
            'REGISTRADO', title_to_register, data.get('modelo'), data.get('ramal'),
            data.get('localizacao'), data.get('descricao'), attachment_links_json,
            user_profile.get("main_group", "N/A"), user_profile.get("company", "")
        ]
        try:
            ws.append_row(new_row, value_input_option='USER_ENTERED') # pyright: ignore[reportArgumentType] # Adiciona a linha
            return bool(True), "Ocorrência de equipamento registrada com sucesso." # Usando bool explicitamente
        except Exception as e:
            return bool(False), f"Ocorreu um erro ao registrar: {e}" # Usando bool explicitamente

    def register_full_occurrence(self, user_email, title, testes):
        """
        Regista uma nova ocorrência de chamada detalhada.
        :param user_email: E-mail do utilizador.
        :param title: Título da ocorrência.
        :param testes: Lista de dicionários com os dados dos testes de ligação.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect() # Garante a conexão
        ws = self._get_worksheet(self.CALLS_SHEET) # Obtém a aba
        if not ws: return bool(False), "Falha ao aceder à planilha de chamadas." # Usando bool explicitamente

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        current_records = self._get_all_records_safe(ws)
        new_id = f"CALL-{len([rec for rec in current_records if rec.get('id')]) + 1:04d}" # Usando len explicitamente

        user_profile = self.check_user_status(user_email)
        
        # Extrai informações dos testes para as colunas principais (Operadora A, Operadora B, Descrição)
        # O restante dos testes é salvo como JSON.
        op_a = testes[0]['op_a'] if testes and isinstance(testes, list) and len(testes) > 0 else 'N/A' # Usando isinstance, list, len explicitamente
        op_b = testes[0]['op_b'] if testes and isinstance(testes, list) and len(testes) > 0 else 'N/A' # Usando isinstance, list, len explicitamente
        description = testes[0]['obs'] if testes and isinstance(testes, list) and len(testes) > 0 else "" # Usando isinstance, list, len explicitamente
        testes_json = json.dumps(testes) # Converte a lista de testes para JSON string

        new_row = [
            new_id, now, title, user_email, user_profile.get("name", "N/A"), user_profile.get("username", "N/A"),
            'REGISTRADO', op_a, op_b, testes_json, description,
            user_profile.get("main_group", "N/A"), user_profile.get("company", "")
        ]
        try:
            ws.append_row(new_row, value_input_option='USER_ENTERED') # pyright: ignore[reportArgumentType] # Adiciona a linha
            return bool(True), "Ocorrência detalhada registrada com sucesso." # Usando bool explicitamente
        except Exception as e:
            return bool(False), f"Ocorreu um erro ao registrar: {e}" # Usando bool explicitamente

    def add_occurrence_comment(self, occurrence_id, user_email, user_name, comment_text):
        """
        Adiciona um novo comentário a uma ocorrência específica.
        :param occurrence_id: ID da ocorrência à qual o comentário pertence.
        :param user_email: E-mail do autor do comentário.
        :param user_name: Nome do autor do comentário.
        :param comment_text: O texto do comentário.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect() # Garante a conexão
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET) # Obtém a aba de comentários
        if not ws: return bool(False), "Falha ao aceder à planilha de comentários." # Usando bool explicitamente

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
            ws.append_row(new_row, value_input_option='USER_ENTERED') # pyright: ignore[reportArgumentType] # Adiciona a nova linha
            return bool(True), "Comentário adicionado com sucesso." # Usando bool explicitamente
        except Exception as e:
            return bool(False), f"Ocorreu um erro ao adicionar o comentário: {e}" # Usando bool explicitamente

    def update_occurrence_comment(self, comment_id, new_comment_text):
        """
        Atualiza o texto de um comentário existente.
        :param comment_id: ID do comentário a ser atualizado.
        :param new_comment_text: O novo texto do comentário.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect() # Garante a conexão
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET) # Obtém a aba de comentários
        if not ws: return bool(False), "Falha ao aceder à planilha de comentários." # Usando bool explicitamente

        try:
            cell = ws.find(comment_id, in_column=2) # Encontra a célula com o ID do comentário (coluna 2)
            if cell:
                ws.update_cell(cell.row, 6, new_comment_text) # Atualiza a célula na coluna 6 (Comentario)
                return bool(True), "Comentário atualizado com sucesso." # Usando bool explicitamente
            else:
                return bool(False), f"Comentário com ID {comment_id} não encontrado." # Usando bool explicitamente
        except gspread.exceptions.CellNotFound: # pyright: ignore[reportAttributeAccessIssue]
            return bool(False), f"Comentário com ID {comment_id} não encontrado na planilha de comentários." # Usando bool explicitamente
        except Exception as e:
            return bool(False), f"Erro ao atualizar o comentário {comment_id}: {e}" # Usando bool explicitamente

    def delete_occurrence_comment(self, comment_id):
        """
        Elimina um comentário da planilha.
        :param comment_id: ID do comentário a ser eliminado.
        :return: Tupla (True, mensagem) se sucesso, ou (False, mensagem_de_erro).
        """
        self._connect() # Garante a conexão
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET) # Obtém a aba de comentários
        if not ws: return bool(False), "Falha ao aceder à planilha de comentários." # Usando bool explicitamente

        try:
            cell = ws.find(comment_id, in_column=2) # Encontra a célula com o ID do comentário (coluna 2)
            if cell:
                ws.delete_rows(cell.row) # Exclui a linha inteira onde o comentário foi encontrado
                return bool(True), "Comentário eliminado com sucesso." # Usando bool explicitamente
            else:
                return bool(False), f"Comentário com ID {comment_id} não encontrado." # Usando bool explicitamente
        except gspread.exceptions.CellNotFound: # pyright: ignore[reportAttributeAccessIssue]
            return bool(False), f"Comentário com ID {comment_id} não encontrado na planilha de comentários." # Usando bool explicitamente
        except Exception as e:
            return bool(False), f"Erro ao eliminar o comentário {comment_id}: {e}" # Usando bool explicitamente

    def get_occurrence_comments(self, occurrence_id):
        """
        Obtém todos os comentários associados a uma ocorrência específica.
        :param occurrence_id: ID da ocorrência.
        :return: Lista de dicionários, cada um representando um comentário, ordenados por data.
        """
        self._connect() # Garante a conexão
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET) # Obtém a aba de comentários
        if not ws: return list() # Usando list explicitamente

        try:
            all_comments = self._get_all_records_safe(ws) # Obtém todos os comentários
            # Filtra os comentários pelo ID da ocorrência e ordena por data.
            filtered_comments = [
                comment for comment in all_comments
                if comment.get('id_ocorrencia') and str(comment['id_ocorrencia']).strip().lower() == str(occurrence_id).strip().lower() # Usando str explicitamente
            ]
            # Ordena por 'Data_Comentario' (a chave original da planilha), do mais recente para o mais antigo.
            return sorted(filtered_comments, key=lambda x: x.get('Data_Comentario', ''), reverse=True) # Usando sorted explicitamente
        except Exception as e:
            print(f"Erro ao obter comentários da ocorrência {occurrence_id}: {e}") # Usando print explicitamente
            return list() # Usando list explicitamente
