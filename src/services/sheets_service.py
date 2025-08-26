# ==============================================================================
# ARQUIVO: src/services/sheets_service.py
# ==============================================================================

import gspread
from googleapiclient.http import MediaFileUpload
from datetime import datetime
from tkinter import messagebox
import threading
import os

class SheetsService:
    """ Serviço de baixo nível para interação direta com a API do Google Sheets. """
    def __init__(self, auth_service_instance):
        self.auth_service = auth_service_instance
        self.SPREADSHEET_ID = "1ymzB0QiZiuTnLk9h3qfFnZgcxkTKJUeT-3rn4bYqtQA"
        self.USERS_SHEET = "users"
        self.CALLS_SHEET = "call_occurrences"
        self.SIMPLE_CALLS_SHEET = "simple_call_occurrences"
        self.EQUIPMENT_SHEET = "equipment_occurrences"
        self.OCCURRENCE_COMMENTS_SHEET = "occurrence_comments"
        self.gspread_lock = threading.Lock()
        self._GC = None
        self._SPREADSHEET = None
        self.is_connected = False

    def _connect(self):
        if self.is_connected: return
        with self.gspread_lock:
            if self.is_connected: return
            credentials = self.auth_service.get_service_account_credentials()
            if not credentials: return
            try:
                self._GC = gspread.service_account(filename=self.auth_service.SERVICE_ACCOUNT_FILE)
                self._SPREADSHEET = self._GC.open_by_key(self.SPREADSHEET_ID)
                self.is_connected = True
            except Exception as e:
                 messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao Google Sheets: {e}")

    def _get_worksheet(self, sheet_name):
        self._connect()
        if not self._SPREADSHEET: return None
        try:
            return self._SPREADSHEET.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            return None

    def _get_all_records_safe(self, worksheet):
        with self.gspread_lock:
            try:
                all_values = worksheet.get_all_values()
                if not all_values: return []
                raw_headers = all_values[0]
                data_rows = all_values[1:]
                processed_headers = [h.strip().lower().replace(' ', '') for h in raw_headers]
                processed_records = [dict(zip(processed_headers, row)) for row in data_rows]
                return processed_records
            except Exception as e:
                print(f"ERRO CRÍTICO em _get_all_records_safe: {e}")
                return []

    def get_all_occurrences(self):
        all_occurrences = []
        for sheet_name in [self.CALLS_SHEET, self.SIMPLE_CALLS_SHEET, self.EQUIPMENT_SHEET]:
            ws = self._get_worksheet(sheet_name)
            if ws:
                all_occurrences.extend(self._get_all_records_safe(ws))
        return all_occurrences

    def get_occurrence_by_id(self, occurrence_id):
        for occ in self.get_all_occurrences():
            if str(occ.get('id')).strip().lower() == str(occurrence_id).strip().lower():
                return occ
        return None

    def register_simple_call_occurrence(self, data):
        ws = self._get_worksheet(self.SIMPLE_CALLS_SHEET)
        if not ws: return False, "Falha ao acessar a planilha."
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_id = f"SCALL-{len(self._get_all_records_safe(ws)) + 1:04d}"
            new_row = [new_id, now, data['title'], data['user_email'], data['user_name'], data['user_username'],
                       data['status'], data['origem'], data['destino'], data['descricao'],
                       data['main_group'], data['company']]
            ws.append_row(new_row, value_input_option='USER_ENTERED') # pyright: ignore[reportArgumentType]
            return True, "Ocorrência registrada."
        except Exception as e:
            return False, str(e)

    def get_all_users(self):
        ws = self._get_worksheet(self.USERS_SHEET)
        return self._get_all_records_safe(ws) if ws else []

    def check_user_status(self, email):
        for user in self.get_all_users():
            if user.get('email', '').strip().lower() == email.strip().lower():
                return user
        return {'status': 'unregistered'}

    def get_all_operators(self):
        ws = self._get_worksheet(self.CALLS_SHEET)
        if not ws: return []
        operators = set()
        for rec in self._get_all_records_safe(ws):
            operators.add(rec.get('operadoraa', '').strip().upper())
            operators.add(rec.get('operadorab', '').strip().upper())
        return sorted([op for op in operators if op])