# ==============================================================================
# FICHEIRO: src/services/sheets_service.py
# DESCRIÇÃO: Lida com todas as operações de leitura e escrita na planilha
#            Google Sheets. (VERSÃO OTIMIZADA COM ARRANQUE RÁPIDO)
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
        self.is_connected = False # Flag para controlar o estado da conexão

    def _connect(self):
        """
        Conecta-se ao Google Sheets apenas se ainda não estiver conectado.
        Esta função é chamada pela primeira vez que a aplicação precisa de aceder à planilha.
        """
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

    def _get_all_records_safe(self, worksheet):
        """Função segura que usa o lock para ler todos os registos de uma aba."""
        with self.gspread_lock:
            return worksheet.get_all_records()

    def _get_worksheet(self, sheet_name):
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
        
        if calls_ws: 
            all_occurrences.extend([rec for rec in self._get_all_records_safe(calls_ws) if rec.get('ID')])
        
        if simple_calls_ws:
            all_occurrences.extend([rec for rec in self._get_all_records_safe(simple_calls_ws) if rec.get('ID')])

        if equip_ws:
            equip_records = [rec for rec in self._get_all_records_safe(equip_ws) if rec.get('ID')]
            for rec in equip_records:
                rec['Título da Ocorrência'] = rec.get('Tipo de Equipamento', f"EQUIPAMENTO {rec.get('ID')}")
            all_occurrences.extend(equip_records)
            
        return sorted(all_occurrences, key=lambda x: x.get('Data de Registro', ''), reverse=True)

    def get_all_operators(self):
        self._connect()
        base_operators = {
            "VIVO", "CLARO", "TIM", "OI", "ALGAR TELECOM", "SERCOMTEL", 
            "NEXTEL", "VULCANET", "CTBC TELECOM", "UNO INTERNET",
            "VIVO FIXO", "CLARO FIXO", "OI FIXO", "EMBRATEL"
        }
        
        ws = self._get_worksheet(self.CALLS_SHEET)
        if not ws:
            return sorted(list(base_operators))
        
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

    def get_occurrences_by_user(self, user_email):
        self._connect()
        user_profile = self.check_user_status(user_email)
        if not user_profile or user_profile.get('status') != 'approved':
            return []

        main_group = user_profile.get("main_group")
        user_company = user_profile.get("company", "").strip().upper() if user_profile.get("company") else None

        all_occurrences = self.get_all_occurrences()
        
        if main_group == '67_TELECOM':
            return all_occurrences

        if main_group in ['PARTNER', 'PREFEITURA']:
            if not user_company: return []
            return [occ for occ in all_occurrences if occ.get('Registrador Company', '').strip().upper() == user_company]

        return []
        
    def update_user_status(self, email, new_status):
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return
        try:
            cell = ws.find(email, in_column=1)
            if cell: ws.update_cell(cell.row, 6, new_status)
        except gspread.exceptions.CellNotFound: print(f"Usuário {email} não encontrado.")

    def get_all_users(self):
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return []
        return [user for user in self._get_all_records_safe(ws) if user.get("email")]

    def update_user_profile(self, email, new_main_group, new_sub_group, new_company=None):
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return
        try:
            cell = ws.find(email, in_column=1)
            if cell:
                ws.update_cell(cell.row, 4, new_main_group)
                ws.update_cell(cell.row, 5, new_sub_group)
                company_to_save = new_company if new_main_group in ['PARTNER', 'PREFEITURA'] else ""
                ws.update_cell(cell.row, 7, company_to_save)
        except gspread.exceptions.CellNotFound:
            print(f"Usuário {email} não encontrado.")
            
    def get_occurrence_by_id(self, occurrence_id):
        self._connect()
        for occ in self.get_all_occurrences():
            if str(occ.get('ID')) == str(occurrence_id): return occ
        return None

    def update_occurrence_status(self, occurrence_id, new_status):
        self._connect()
        sheet_name, status_col = None, 7
        
        if 'SCALL' in str(occurrence_id):
            sheet_name = self.SIMPLE_CALLS_SHEET
        elif 'CALL' in str(occurrence_id):
            sheet_name = self.CALLS_SHEET
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

    def _upload_files_to_drive(self, user_credentials, file_paths):
        self._connect()
        # ... (implementação completa)
        pass

    def register_simple_call_occurrence(self, user_email, data):
        self._connect()
        ws = self._get_worksheet(self.SIMPLE_CALLS_SHEET)
        if not ws: return False, "Falha ao aceder à planilha de chamadas simplificadas."
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_id = f"SCALL-{len(self._get_all_records_safe(ws)) + 1:04d}"
            user_name, user_username = self._get_user_info(user_email)
            title = f"CHAMADA SIMPLES DE {data.get('origem')} PARA {data.get('destino')}"
            
            user_profile = self.check_user_status(user_email)
            registrador_main_group = user_profile.get("main_group", "N/A")
            registrador_company = user_profile.get("company", "")

            new_row = [
                new_id, now, title, user_email, user_name, user_username, 
                'REGISTRADO', data.get('origem'), data.get('destino'), data.get('descricao'),
                registrador_main_group, registrador_company
            ]
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Ocorrência registrada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao registrar a ocorrência: {e}"

    def register_equipment_occurrence(self, user_credentials, user_email, data, attachment_paths):
        self._connect()
        # ... (implementação completa)
        pass

    def register_full_occurrence(self, user_email, title, testes):
        self._connect()
        # ... (implementação completa)
        pass
