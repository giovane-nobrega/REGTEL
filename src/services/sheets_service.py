# ==============================================================================
# FICHEIRO: src/services/sheets_service.py
# DESCRIÇÃO: Lida com todas as operações de leitura e escrita na planilha
#            Google Sheets, otimizado com operações em lote.
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
        """Função segura que usa um lock para ler todos os registos de uma aba."""
        with self.gspread_lock:
            return worksheet.get_all_records()

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
            return True, uploaded_file_links
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
                ids_in_sheet = ws.col_values(1)
                for i, cell_id in enumerate(ids_in_sheet):
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

        all_users_map = {str(user.get('email')): {'row': i + 2} for i, user in enumerate(self._get_all_records_safe(ws))}
        
        cells_to_update = []
        for email, profile_changes in changes.items():
            if email in all_users_map:
                row = all_users_map[email]['row']
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
            records = [user for user in self._get_all_records_safe(ws) if user.get("email")]
            for user in records:
                if user.get("email") == email: return user
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
        if calls_ws: all_occurrences.extend([rec for rec in self._get_all_records_safe(calls_ws) if rec.get('ID')])
        if simple_calls_ws: all_occurrences.extend([rec for rec in self._get_all_records_safe(simple_calls_ws) if rec.get('ID')])
        if equip_ws:
            equip_records = [rec for rec in self._get_all_records_safe(equip_ws) if rec.get('ID')]
            for rec in equip_records: rec['Título da Ocorrência'] = rec.get('Tipo de Equipamento', f"EQUIPAMENTO {rec.get('ID')}")
            all_occurrences.extend(equip_records)
            
        return sorted(all_occurrences, key=lambda x: x.get('Data de Registro', ''), reverse=True)

    def get_occurrences_by_user(self, user_email):
        self._connect()
        user_profile = self.check_user_status(user_email)
        if not user_profile or user_profile.get('status') != 'approved': return []

        main_group = user_profile.get("main_group")
        user_company = user_profile.get("company", "").strip().upper() if user_profile.get("company") else None

        all_occurrences = self.get_all_occurrences()
        
        if main_group == '67_TELECOM': return all_occurrences

        if main_group in ['PARTNER', 'PREFEITURA']:
            if not user_company: return []
            return [occ for occ in all_occurrences if occ.get('Registrador Company', '').strip().upper() == user_company]

        return []

    def get_all_users(self):
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return []
        return [user for user in self._get_all_records_safe(ws) if user.get("email")]

    def get_all_operators(self):
        self._connect()
        base_operators = {"VIVO", "CLARO", "TIM", "OI", "ALGAR TELECOM", "SERCOMTEL", "NEXTEL", "VULCANET", "CTBC TELECOM", "UNO INTERNET", "VIVO FIXO", "CLARO FIXO", "OI FIXO", "EMBRATEL"}
        ws = self._get_worksheet(self.CALLS_SHEET)
        if not ws: return sorted(list(base_operators))
        try:
            records = [rec for rec in self._get_all_records_safe(ws) if rec.get('ID')]
            sheet_operators = {rec[key] for rec in records for key in ['Operadora A', 'Operadora B'] if rec.get(key)}
            base_operators.update(sheet_operators)
        except Exception as e:
            print(f"Erro ao ler operadoras da planilha: {e}")
        return sorted(list(base_operators))
    
    def request_access(self, email, full_name, username, main_group, sub_group, company_name=None):
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return False, "Não foi possível aceder à planilha."
        try:
            if ws.find(email): return False, "Solicitação já existe para este e-mail."
        except gspread.exceptions.CellNotFound: pass
        new_row = [email, full_name, username, main_group, sub_group, "pending", company_name or ""]
        ws.append_row(new_row, value_input_option='USER_ENTERED')
        return True, "Solicitação de acesso enviada com sucesso."

    def get_pending_requests(self):
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return []
        all_users = [user for user in self._get_all_records_safe(ws) if user.get("email")]
        return [user for user in all_users if user.get("status") == "pending"]
        
    def update_user_status(self, email, new_status):
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return
        try:
            cell = ws.find(email, in_column=1)
            if cell: ws.update_cell(cell.row, 6, new_status)
        except gspread.exceptions.CellNotFound: print(f"Usuário {email} não encontrado.")

    def get_occurrence_by_id(self, occurrence_id):
        self._connect()
        for occ in self.get_all_occurrences():
            if str(occ.get('ID')) == str(occurrence_id): return occ
        return None

    def update_occurrence_status(self, occurrence_id, new_status):
        self._connect()
        sheet_name, status_col = None, 7
        if 'SCALL' in str(occurrence_id): sheet_name = self.SIMPLE_CALLS_SHEET
        elif 'CALL' in str(occurrence_id): sheet_name = self.CALLS_SHEET
        elif 'EQUIP' in str(occurrence_id):
            sheet_name = self.EQUIPMENT_SHEET
            status_col = 6
        if not sheet_name: return
        ws = self._get_worksheet(sheet_name)
        if not ws: return
        try:
            cell = ws.find(occurrence_id, in_column=1)
            if cell: ws.update_cell(cell.row, status_col, new_status)
        except gspread.exceptions.CellNotFound: print(f"Ocorrência {occurrence_id} não encontrada.")

    def register_simple_call_occurrence(self, user_email, data):
        self._connect()
        ws = self._get_worksheet(self.SIMPLE_CALLS_SHEET)
        if not ws: return False, "Falha ao aceder à planilha."
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_id = f"SCALL-{len(self._get_all_records_safe(ws)) + 1:04d}"
            user_profile = self.check_user_status(user_email)
            new_row = [
                new_id, now, f"CHAMADA SIMPLES DE {data.get('origem')} PARA {data.get('destino')}",
                user_email, user_profile.get("name", "N/A"), user_profile.get("username", "N/A"), 
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
        new_id = f"EQUIP-{len(self._get_all_records_safe(ws)) + 1:04d}"
        user_profile = self.check_user_status(user_email)
        
        new_row = [
            new_id, now, user_email, user_profile.get("name", "N/A"), user_profile.get("username", "N/A"),
            'REGISTRADO', data.get('tipo'), data.get('modelo'), data.get('ramal'),
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
        new_id = f"CALL-{len(self._get_all_records_safe(ws)) + 1:04d}"
        user_profile = self.check_user_status(user_email)
        op_a = testes[0]['op_a'] if testes else 'N/A'
        op_b = testes[0]['op_b'] if testes else 'N/A'
        description = testes[0]['obs'] if testes else ""
        testes_json = json.dumps(testes)
        
        new_row = [
            new_id, now, title, user_email, user_profile.get("name", "N/A"), user_profile.get("username", "N/A"),
            'REGISTRADO', op_a, op_b, testes_json, description, "[]",
            user_profile.get("main_group", "N/A"), user_profile.get("company", "")
        ]
        try:
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Ocorrência detalhada registrada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao registrar a ocorrência detalhada: {e}"
