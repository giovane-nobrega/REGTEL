# ==============================================================================
# FICHEIRO: src/services/sheets_service.py
# DESCRIÇÃO: Lida com todas as operações de leitura e escrita na planilha
#            Google Sheets, otimizado com operações em lote.
#            (VERSÃO COM NORMALIZAÇÃO ROBUSTA DE CHAVES E TÍTULOS)
# ==============================================================================

import gspread
import json
import csv
from datetime import datetime
from googleapiclient.http import MediaFileUpload
import os
from tkinter import messagebox
import threading

class SheetsService:
    """Lida com todas as operações de leitura e escrita na planilha Google Sheets."""
    def __init__(self, auth_service_instance):
        self.auth_service = auth_service_instance
        self.SPREADSHEET_ID = "1ymzB0QiZiuTnLk9h3qfFnZgcxkTKJUeT-3rn4bYqtQA" 
        self.USERS_SHEET = "users"
        self.CALLS_SHEET = "call_occurrences"
        self.SIMPLE_CALLS_SHEET = "simple_call_occurrences"
        self.EQUIPMENT_SHEET = "equipment_occurrences"

        self.gspread_lock = threading.Lock()
        self._GC = None
        self._SPREADSHEET = None
        self.is_connected = False

    def _connect(self):
        """Conecta-se ao Google Sheets usando a conta de serviço."""
        if self.is_connected:
            return

        with self.gspread_lock:
            if self.is_connected:
                return
            
            self._SERVICE_CREDENTIALS = self.auth_service.get_service_account_credentials()
            if not self._SERVICE_CREDENTIALS:
                return
            try:
                self._GC = gspread.service_account(filename=self.auth_service.SERVICE_ACCOUNT_FILE)
                self._SPREADSHEET = self._GC.open_by_key(self.SPREADSHEET_ID)
                self.is_connected = True
            except Exception as e:
                 messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao Google Sheets: {e}")

    def _get_worksheet(self, sheet_name):
        """Obtém uma aba (worksheet) da planilha."""
        self._connect()
        if not self._SPREADSHEET: return None
        try:
            return self._SPREADSHEET.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"ERRO: A aba '{sheet_name}' não foi encontrada na planilha.")
            return None
        except Exception as e:
            print(f"ERRO ao obter a aba '{sheet_name}': {e}")
            return None

    def _get_all_records_safe(self, worksheet):
        """
        Função segura que usa um lock para ler todos os registos de uma aba.
        Retorna uma lista de dicionários onde cada dicionário contém:
        1. As chaves originais (como vêm do gspread).
        2. Chaves normalizadas (minúsculas, sem espaços) para fácil acesso interno.
        """
        with self.gspread_lock:
            raw_records = worksheet.get_all_records()
            processed_records = []
            for rec in raw_records:
                # Cria um novo dicionário que conterá tanto as chaves originais quanto as normalizadas
                processed_rec = {}
                for k, v in rec.items():
                    original_key = k # Mantém a chave original
                    normalized_key = k.strip().lower() # Cria a chave normalizada

                    processed_rec[original_key] = v # Armazena o valor com a chave original
                    if original_key != normalized_key: # Evita duplicação se a chave já for normalizada
                        processed_rec[normalized_key] = v # Armazena o valor com a chave normalizada
                processed_records.append(processed_rec)
            return processed_records

    def _upload_files_to_drive(self, user_credentials, file_paths):
        """Faz o upload de ficheiros para o Google Drive do utilizador."""
        if not file_paths: return True, []
        drive_service = self.auth_service.get_drive_service(user_credentials)
        if not drive_service: return False, "Não foi possível obter o serviço do Google Drive."
        try:
            q = "mimeType='application/vnd.google-apps.folder' and name='Craft Quest Anexos' and trashed=false"
            response = drive_service.files().list(q=q, spaces='drive', fields='files(id, name)').execute()
            folder_id = response.get('files')[0].get('id') if response.get('files') else drive_service.files().create(body={'name': 'Craft Quest Anexos', 'mimeType': 'application/vnd.google-apps.folder'}, fields='id').execute().get('id')
            uploaded_file_links = []
            for file_path in file_paths:
                file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
                media = MediaFileUpload(file_path, resumable=True)
                file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
                drive_service.permissions().create(fileId=file.get('id'), body={'role': 'reader', 'type': 'anyone'}).execute()
                uploaded_file_links.append(file.get('webViewLink'))
            return True, f"Upload de {len(uploaded_file_links)} ficheiro(s) concluído."
        except Exception as e:
            return False, f"Ocorreu um erro durante o upload para o Google Drive: {e}"

    # ==============================================================================
    # --- MÉTODOS DE ATUALIZAÇÃO EM LOTE (OTIMIZADOS) ---
    # ==============================================================================
    
    def batch_update_occurrence_statuses(self, changes: dict):
        """Atualiza múltiplos status de ocorrências de uma só vez."""
        self._connect()
        if not self._SPREADSHEET: return False, "Falha na conexão."

        updates_by_sheet = {
            self.CALLS_SHEET: [],
            self.SIMPLE_CALLS_SHEET: [],
            self.EQUIPMENT_SHEET: []
        }

        all_ids_map = {}
        for sheet_name in updates_by_sheet.keys():
            ws = self._get_worksheet(sheet_name)
            if ws:
                ids_in_sheet = ws.col_values(1) # Obtém valores brutos da coluna 1
                for i, cell_id in enumerate(ids_in_sheet):
                    if i == 0: continue # Ignorar cabeçalho
                    all_ids_map[cell_id] = {'sheet': sheet_name, 'row': i + 1}


        for occ_id, new_status in changes.items():
            if occ_id in all_ids_map:
                info = all_ids_map[occ_id]
                sheet_name = info['sheet']
                status_col = 6 if sheet_name == self.EQUIPMENT_SHEET else 7 
                updates_by_sheet[sheet_name].append(gspread.Cell(info['row'], status_col, value=new_status))

        try:
            with self.gspread_lock:
                for sheet_name, cells_to_update in updates_by_sheet.items():
                    if cells_to_update:
                        ws = self._get_worksheet(sheet_name)
                        if ws: ws.update_cells(cells_to_update)
            return True, "Alterações salvas com sucesso."
        except Exception as e:
            return False, f"Erro na atualização em lote: {e}"

    def batch_update_user_profiles(self, changes: dict):
        """Atualiza múltiplos perfis de utilizador de uma só vez."""
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return False, "Falha na conexão com a aba de utilizadores."

        emails_in_sheet = ws.col_values(1) # Obtém e-mails brutos da coluna 1
        all_users_map = {emails_in_sheet[i].strip().lower(): {'row': i + 1} 
                         for i in range(1, len(emails_in_sheet)) if emails_in_sheet[i].strip()}

        cells_to_update = []
        for email, profile_changes in changes.items():
            normalized_email = email.strip().lower()
            if normalized_email in all_users_map:
                row = all_users_map[normalized_email]['row']
                cells_to_update.append(gspread.Cell(row, 4, value=profile_changes['main_group']))
                cells_to_update.append(gspread.Cell(row, 5, value=profile_changes['sub_group']))
                cells_to_update.append(gspread.Cell(row, 7, value=profile_changes['company']))

        try:
            with self.gspread_lock:
                if cells_to_update:
                    ws.update_cells(cells_to_update)
            return True, "Perfis atualizados com sucesso."
        except Exception as e:
            return False, f"Erro na atualização de perfis em lote: {e}"

    # ==============================================================================
    # --- MÉTODOS DE LEITURA E ESCRITA ---
    # ==============================================================================

    def check_user_status(self, email):
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return {"status": "error"}
        try:
            records = self._get_all_records_safe(ws) # Obtém registos com chaves originais e normalizadas
            for user_rec in records:
                # Usa a chave normalizada 'email' para a comparação
                if user_rec.get("email") and user_rec["email"].strip().lower() == email.strip().lower():
                    return user_rec # Retorna o dicionário completo (com chaves originais e normalizadas)
        except Exception as e:
            print(f"Erro ao ler a planilha de usuários: {e}")
            return {"status": "error"}
        return {"status": "unregistered"}

    def get_all_occurrences(self):
        self._connect()
        calls_ws = self._get_worksheet(self.CALLS_SHEET)
        simple_calls_ws = self._get_worksheet(self.SIMPLE_CALLS_SHEET)
        equip_ws = self._get_worksheet(self.EQUIPMENT_SHEET)
        
        all_occurrences = []

        # Chaves comuns para o título, em ordem de preferência (usar chaves normalizadas)
        possible_title_keys = ['título da ocorrência', 'título', 'title']
        
        def get_final_title(record, record_type):
            """
            Tenta encontrar um título válido no registo (usando chaves normalizadas)
            ou gera um padrão se nenhum título do usuário for encontrado.
            """
            # Tenta encontrar o título do usuário primeiro
            for key in possible_title_keys:
                value = record.get(key)
                if value is not None and str(value).strip() != "":
                    return str(value).strip()
            
            # Se nenhum título do usuário for encontrado, gera um padrão baseado no tipo de ocorrência
            record_id = record.get('id', 'N/A') # ID também virá normalizado
            if record_type == "call": # Chamadas detalhadas
                return f"Chamada Detalhada {record_id}"
            elif record_type == "simple_call": # Chamadas simplificadas
                return f"Chamada Simples de {record.get('origem', 'N/A')} para {record.get('destino', 'N/A')}"
            elif record_type == "equipment": # Ocorrências de equipamento
                return record.get('tipo de equipamento', f"Equipamento {record_id}")
            
            return f"Ocorrência {record_id}" # Fallback final


        if calls_ws:
            calls_records = self._get_all_records_safe(calls_ws) # Registros com chaves originais e normalizadas
            for rec in calls_records:
                if rec.get('id'): # Processa apenas registos com ID normalizado
                    rec['Título da Ocorrência'] = get_final_title(rec, "call") # Adiciona o título finalizado
                    all_occurrences.append(rec)

        if simple_calls_ws:
            simple_calls_records = self._get_all_records_safe(simple_calls_ws)
            for rec in simple_calls_records:
                if rec.get('id'):
                    rec['Título da Ocorrência'] = get_final_title(rec, "simple_call")
                    all_occurrences.append(rec)

        if equip_ws:
            equip_records = self._get_all_records_safe(equip_ws)
            for rec in equip_records:
                if rec.get('id'):
                    rec['Título da Ocorrência'] = get_final_title(rec, "equipment")
                    all_occurrences.append(rec)
            
        # Retorna os registros com chaves originais e normalizadas, e 'Título da Ocorrência' preenchido
        return sorted(all_occurrences, key=lambda x: x.get('Data de Registro', ''), reverse=True)


    def get_occurrences_by_user(self, user_email):
        self._connect()
        user_profile = self.check_user_status(user_email) # Retorna perfil com chaves originais e normalizadas
        if not user_profile or user_profile.get('status') != 'approved': return []

        main_group = user_profile.get("main_group") # Acessa a chave original 'main_group'
        user_company = user_profile.get("company", "").strip().upper() # Acessa a chave original 'company'

        all_occurrences = self.get_all_occurrences() # Usa o método que já normaliza chaves e títulos
        
        if main_group == '67_TELECOM': return all_occurrences

        if main_group in ['PARTNER', 'PREFEITURA']:
            if not user_company: return []
            # Compara usando a chave original 'Registrador Company'
            return [occ for occ in all_occurrences if occ.get('Registrador Company', '').strip().upper() == user_company]

        return []

    def get_all_users(self):
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return []
        # _get_all_records_safe já retorna com chaves originais e normalizadas
        return [rec for rec in self._get_all_records_safe(ws) if rec.get("email")]

    def get_all_operators(self):
        self._connect()
        base_operators = {"VIVO", "CLARO", "TIM", "OI", "ALGAR TELECOM", "SERCOMTEL", "NEXTEL", "VULCANET", "CTBC TELECOM", "UNO INTERNET", "VIVO FIXO", "CLARO FIXO", "OI FIXO", "EMBRATEL"}
        ws = self._get_worksheet(self.CALLS_SHEET)
        if not ws: return sorted(list(base_operators))
        try:
            records = self._get_all_records_safe(ws) # Obtém registos com chaves originais e normalizadas
            sheet_operators = set()
            for rec in records:
                op_a = rec.get('operadora a') # Acessa a chave normalizada
                op_b = rec.get('operadora b') # Acessa a chave normalizada
                if op_a and str(op_a).strip() != "":
                    sheet_operators.add(str(op_a).strip().upper())
                if op_b and str(op_b).strip() != "":
                    sheet_operators.add(str(op_b).strip().upper())
            base_operators.update(sheet_operators)
        except Exception as e:
            print(f"Erro ao ler operadoras da planilha: {e}")
        return sorted(list(base_operators))
    
    def request_access(self, email, full_name, username, main_group, sub_group, company_name=None):
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return False, "Falha ao aceder à planilha."
        try:
            all_users_records = self._get_all_records_safe(ws) # Obtém registos com chaves originais e normalizadas
            normalized_emails_in_sheet = [str(rec.get('email', '')).strip().lower() for rec in all_users_records]
            
            if email.strip().lower() in normalized_emails_in_sheet:
                return False, "Solicitação já existe para este e-mail."
        except Exception as e:
            return False, f"Erro ao verificar e-mail existente: {e}"

        # --- AQUI ESTÁ A CORREÇÃO: A NOVA ORDEM DA LINHA ---
        new_row = [
            email,              # Coluna 1: Email
            full_name,          # Coluna 2: Nome Completo
            username,           # Coluna 3: Username
            main_group,         # Coluna 4: Grupo Principal
            sub_group,          # Coluna 5: Subgrupo
            "pending",          # Coluna 6: Status
            company_name or ""  # Coluna 7: Empresa/Departamento
        ]
        # ----------------------------------------------------
        try:
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Solicitação de acesso enviada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao enviar a solicitação: {e}"

    def get_pending_requests(self):
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return []
        all_users = self._get_all_records_safe(ws) # Usa _get_all_records_safe que retorna chaves originais e normalizadas
        return [user for user in all_users if user.get("status") and str(user.get("status")).strip().lower() == "pending"]
        
    def update_user_status(self, email, new_status):
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return
        try:
            # ws.find busca na planilha, não nos records normalizados.
            cell = ws.find(email, in_column=1) # Assume que a coluna 1 é o e-mail
            if cell: ws.update_cell(cell.row, 6, new_status) # Coluna 6 é o status
        except gspread.exceptions.CellNotFound: print(f"Usuário {email} não encontrado.")
        except Exception as e: print(f"Erro ao atualizar status do usuário {email}: {e}")


    def get_occurrence_by_id(self, occurrence_id):
        self._connect()
        # get_all_occurrences já normaliza os títulos e chaves, então podemos usá-lo aqui
        for occ in self.get_all_occurrences():
            # Compara usando a chave normalizada 'id'
            if str(occ.get('id')).strip().lower() == str(occurrence_id).strip().lower(): 
                return occ # Retorna o dicionário com chaves originais e normalizadas
        return None

    def update_occurrence_status(self, occurrence_id, new_status):
        self._connect()
        sheet_name, status_col = None, 7
        # Usa IDs normalizados para a verificação
        occ_id_lower = str(occurrence_id).strip().lower()
        if 'scall' in occ_id_lower: sheet_name = self.SIMPLE_CALLS_SHEET
        elif 'call' in occ_id_lower: sheet_name = self.CALLS_SHEET
        elif 'equip' in occ_id_lower:
            sheet_name = self.EQUIPMENT_SHEET
            status_col = 6
        if not sheet_name: return
        ws = self._get_worksheet(sheet_name)
        if not ws: return
        try:
            # ws.find busca na planilha, não nos records normalizados.
            cell = ws.find(occurrence_id, in_column=1) # Assume que a coluna 1 é o ID
            if cell: ws.update_cell(cell.row, status_col, new_status)
        except gspread.exceptions.CellNotFound: print(f"Ocorrência {occurrence_id} não encontrada.")
        except Exception as e: print(f"Erro ao atualizar status da ocorrência {occurrence_id}: {e}")

    def register_simple_call_occurrence(self, user_email, data):
        self._connect()
        ws = self._get_worksheet(self.SIMPLE_CALLS_SHEET)
        if not ws: return False, "Falha ao aceder à planilha."
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_records = self._get_all_records_safe(ws)
            new_id = f"SCALL-{len([rec for rec in current_records if rec.get('id')]) + 1:04d}" # Usa 'id' normalizado
            
            user_profile = self.check_user_status(user_email)
            title_to_register = f"CHAMADA SIMPLES DE {data.get('origem', 'N/A')} PARA {data.get('destino', 'N/A')}"
            new_row = [
                new_id, now, title_to_register, # Coluna 3 é o título
                user_email, user_profile.get("Nome Completo", "N/A"), user_profile.get("username", "N/A"), # Usar chaves originais para guardar
                'REGISTRADO', data.get('origem'), data.get('destino'), data.get('descricao'),
                user_profile.get("main_group", "N/A"), user_profile.get("company", "")
            ]
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Ocorrência registrada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao registrar: {e}"

    def register_equipment_occurrence(self, user_credentials, user_email, data, attachment_paths):
        self._connect()
        ws = self._get_worksheet(self.EQUIPMENT_SHEET)
        if not ws: return False, "Falha ao aceder à planilha de equipamentos."
        
        upload_success, result = self._upload_files_to_drive(user_credentials, attachment_paths)
        if not upload_success: return False, result
        
        attachment_links_json = json.dumps(result)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        current_records = self._get_all_records_safe(ws)
        new_id = f"EQUIP-{len([rec for rec in current_records if rec.get('id')]) + 1:04d}" # Usa 'id' normalizado

        user_profile = self.check_user_status(user_email)
        
        title_to_register = data.get('tipo', f"EQUIPAMENTO {new_id}") # Usar tipo como título
        new_row = [
            new_id, now, user_email, user_profile.get("Nome Completo", "N/A"), user_profile.get("username", "N/A"), # Usar chaves originais para guardar
            'REGISTRADO', title_to_register, data.get('modelo'), data.get('ramal'),
            data.get('localizacao'), data.get('descricao'), attachment_links_json,
            user_profile.get("main_group", "N/A"), user_profile.get("company", "")
        ]
        try:
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Ocorrência de equipamento registrada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao registrar a ocorrência de equipamento: {e}"

    def register_full_occurrence(self, user_email, title, testes):
        self._connect()
        ws = self._get_worksheet(self.CALLS_SHEET)
        if not ws: return False, "Falha ao aceder à planilha de chamadas."
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        current_records = self._get_all_records_safe(ws)
        new_id = f"CALL-{len([rec for rec in current_records if rec.get('id')]) + 1:04d}" # Usa 'id' normalizado

        user_profile = self.check_user_status(user_email)
        op_a = testes[0]['op_a'] if testes else 'N/A'
        op_b = testes[0]['op_b'] if testes else 'N/A'
        description = testes[0]['obs'] if testes else ""
        testes_json = json.dumps(testes)
        
        new_row = [
            new_id, now, title, user_email, user_profile.get("Nome Completo", "N/A"), user_profile.get("username", "N/A"), # Usar chaves originais para guardar
            'REGISTRADO', op_a, op_b, testes_json, description, "[]",
            user_profile.get("main_group", "N/A"), user_profile.get("company", "")
        ]
        try:
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Ocorrência detalhada registrada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao registrar a ocorrência detalhada: {e}"
