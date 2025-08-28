# ==============================================================================
# FICHEIRO: src/services/sheets_service.py
# DESCRIÇÃO: Lida com todas as operações de leitura e escrita na planilha
#            Google Sheets.
# DATA DA ATUALIZAÇÃO: 27/08/2025
# NOTAS: Corrigidos alertas do Pylance para tipagem de `value_input_option`
#        e resolução de `gspread.exceptions.CellNotFound`.
# ==============================================================================

import gspread
import json
import csv
from datetime import datetime
from googleapiclient.http import MediaFileUpload
import os
from tkinter import messagebox
import threading
from builtins import Exception, print, len, str, sorted, list, set, enumerate, dict, bool, isinstance, range
from gspread.utils import ValueInputOption # NOVA IMPORTAÇÃO PARA TIPAGEM

class SheetsService:
    """
    Lida com todas as operações de leitura e escrita na planilha Google Sheets.
    """
    def __init__(self, auth_service_instance):
        self.auth_service = auth_service_instance
        
        self.SPREADSHEET_ID = "1ymzB0QiZiuTnLk9h3qfFnZgcxkTKJUeT-3rn4bYqtQA" 
        self.USERS_SHEET = "users"
        self.CALLS_SHEET = "call_occurrences"
        self.SIMPLE_CALLS_SHEET = "simple_call_occurrences"
        self.EQUIPMENT_SHEET = "equipment_occurrences"
        self.OCCURRENCE_COMMENTS_SHEET = "occurrence_comments"
        self.OPERATORS_SHEET = "operators"

        self.gspread_lock = threading.Lock()
        self._GC = None
        self._SPREADSHEET = None
        self.is_connected = False

    def _connect(self):
        """Conecta-se ao Google Sheets usando as credenciais da conta de serviço."""
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
        """Obtém uma aba (worksheet) específica da planilha."""
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
        """Lê todos os registos de uma aba de forma segura (thread-safe)."""
        with self.gspread_lock:
            all_values = worksheet.get_all_values()
            if not all_values:
                return []

            raw_headers = all_values[0]
            data_rows = all_values[1:]

            processed_headers = []
            seen_headers = {}
            for header in raw_headers:
                original_header = header.strip() if header else ''
                normalized_header = original_header.lower().replace(' ', '')

                if normalized_header in seen_headers:
                    seen_headers[normalized_header] += 1
                    normalized_header = f"{normalized_header}_{seen_headers[normalized_header]}"
                else:
                    seen_headers[normalized_header] = 0

                processed_headers.append(normalized_header)

            processed_records = []
            for row in data_rows:
                processed_rec = dict()
                for i, header in enumerate(processed_headers):
                    if i < len(row):
                        value = row[i]
                        processed_rec[header] = value
                        if raw_headers[i].strip() != header:
                             processed_rec[raw_headers[i].strip()] = value
                processed_records.append(processed_rec)
            return processed_records

    def _upload_files_to_drive(self, user_credentials, file_paths):
        """Faz o upload de ficheiros para o Google Drive do utilizador."""
        if not file_paths: return bool(True), list()
        
        drive_service = self.auth_service.get_drive_service(user_credentials)
        if not drive_service: return bool(False), "Não foi possível obter o serviço do Google Drive."

        try:
            q = "mimeType='application/vnd.google-apps.folder' and name='Craft Quest Anexos' and trashed=false"
            response = drive_service.files().list(q=q, spaces='drive', fields='files(id, name)').execute()
            
            folder_id = None
            if response.get('files'):
                folder_id = response.get('files')[0].get('id')
            else:
                folder_metadata = {'name': 'Craft Quest Anexos', 'mimeType': 'application/vnd.google-apps.folder'}
                folder_id = drive_service.files().create(body=folder_metadata, fields='id').execute().get('id')

            uploaded_file_links = list()
            for file_path in file_paths:
                file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
                media = MediaFileUpload(file_path, resumable=True)
                file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
                
                drive_service.permissions().create(fileId=file.get('id'), body={'role': 'reader', 'type': 'anyone'}).execute()
                uploaded_file_links.append(file.get('webViewLink'))

            return bool(True), uploaded_file_links
        except Exception as e:
            return bool(False), f"Ocorreu um erro durante o upload para o Google Drive: {e}"

    # --- MÉTODOS DE ATUALIZAÇÃO EM LOTE ---
    def batch_update_occurrence_statuses(self, changes: dict):
        """Atualiza múltiplos status de ocorrências de uma só vez."""
        self._connect()
        if not self._SPREADSHEET: return bool(False), "Falha na conexão."

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
                for i, occ_id in enumerate(ids_in_sheet):
                    if i == 0: continue # Pula o cabeçalho
                    all_ids_map[occ_id] = {'sheet': sheet_name, 'row': i + 1}

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
            return bool(True), "Alterações salvas com sucesso."
        except Exception as e:
            return bool(False), f"Erro na atualização em lote: {e}"

    def batch_update_user_profiles(self, changes: dict):
        """Atualiza múltiplos perfis de utilizador de uma só vez."""
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return bool(False), "Falha na conexão com a aba de utilizadores."

        emails_in_sheet = ws.col_values(1)
        all_users_map = {str(email).strip().lower(): {'row': i + 1}
                         for i, email in enumerate(emails_in_sheet) if i > 0 and str(email).strip()}

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
            return bool(True), "Perfis atualizados com sucesso."
        except Exception as e:
            return bool(False), f"Erro na atualização de perfis em lote: {e}"

    # --- MÉTODOS DE LEITURA E ESCRITA ---
    def check_user_status(self, email):
        """Verifica o status e o perfil de um utilizador."""
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return dict(status="error")
        try:
            records = self._get_all_records_safe(ws)
            for user_rec in records:
                if user_rec.get("email") and str(user_rec["email"]).strip().lower() == str(email).strip().lower():
                    return user_rec
        except Exception as e:
            print(f"Erro ao ler a planilha de usuários: {e}")
            return dict(status="error")
        return dict(status="unregistered")

    def get_all_occurrences(self):
        """Obtém todas as ocorrências de todas as abas."""
        self._connect()
        calls_ws = self._get_worksheet(self.CALLS_SHEET)
        simple_calls_ws = self._get_worksheet(self.SIMPLE_CALLS_SHEET)
        equip_ws = self._get_worksheet(self.EQUIPMENT_SHEET)

        all_occurrences = []
        possible_title_keys = ['título da ocorrência', 'título', 'title']

        def get_final_title(record, record_type):
            for key in possible_title_keys:
                value = record.get(key)
                if value is not None and str(value).strip() != "":
                    return str(value).strip()
            record_id = record.get('id', 'N/A')
            if record_type == "call": return f"Chamada Detalhada {record_id}"
            elif record_type == "simple_call": return f"Chamada Simples de {record.get('origem', 'N/A')} para {record.get('destino', 'N/A')}"
            elif record_type == "equipment": return record.get('tipo de equipamento', f"Equipamento {record_id}")
            return f"Ocorrência {record_id}"

        if calls_ws:
            for rec in self._get_all_records_safe(calls_ws):
                if rec.get('id'):
                    rec['Título da Ocorrência'] = get_final_title(rec, "call")
                    all_occurrences.append(rec)
        if simple_calls_ws:
            for rec in self._get_all_records_safe(simple_calls_ws):
                if rec.get('id'):
                    rec['Título da Ocorrência'] = get_final_title(rec, "simple_call")
                    all_occurrences.append(rec)
        if equip_ws:
            for rec in self._get_all_records_safe(equip_ws):
                if rec.get('id'):
                    rec['Título da Ocorrência'] = get_final_title(rec, "equipment")
                    all_occurrences.append(rec)

        return sorted(all_occurrences, key=lambda x: x.get('Data de Registro', ''), reverse=True)

    def get_occurrences_by_user(self, user_email):
        """Obtém as ocorrências visíveis para um utilizador específico."""
        self._connect()
        user_profile = self.check_user_status(user_email)
        
        if not user_profile or user_profile.get('status') != 'approved':
            return []

        main_group = user_profile.get("main_group", "").strip().upper()
        user_company = user_profile.get("company", "").strip().upper()
        
        all_occurrences = self.get_all_occurrences()
        filtered_list = []

        if main_group == '67_TELECOM':
            return all_occurrences
        elif main_group == 'PARTNER':
            if not user_company: return []
            for occ in all_occurrences:
                occurrence_id = occ.get('id', '').strip().upper()
                occ_registrador_company = occ.get('registrador company', '').strip().upper()
                if 'CALL' in occurrence_id and 'SCALL' not in occurrence_id and occ_registrador_company == user_company:
                    filtered_list.append(occ)
            return filtered_list
        elif main_group == 'PREFEITURA':
            for occ in all_occurrences:
                occ_group = (str(occ.get("registradormaingroup") or "")).upper()
                occ_id = occ.get("id", "")
                if (occ_group == "PREFEITURA" or
                    (occ_id.startswith("EQUIP") and occ_group == "67_TELECOM") or
                    (occ_id.startswith("SCALL") and occ_group == "67_TELECOM")):
                    filtered_list.append(occ)
            return filtered_list
        return []

    def get_all_users(self):
        """Obtém todos os utilizadores registados."""
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return []
        return [rec for rec in self._get_all_records_safe(ws) if rec.get("email")]

    def request_access(self, email, full_name, username, main_group, sub_group, company_name=None):
        """Envia uma solicitação de acesso para um novo utilizador."""
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return bool(False), "Falha ao aceder à planilha."

        try:
            all_users_records = self._get_all_records_safe(ws)
            normalized_emails_in_sheet = [str(rec.get('email', '')).strip().lower() for rec in all_users_records]
            if str(email).strip().lower() in normalized_emails_in_sheet:
                return bool(False), "Solicitação já existe para este e-mail."
        except Exception as e:
            return bool(False), f"Erro ao verificar e-mail existente: {e}"

        new_row = [email, full_name, username, main_group, sub_group, "pending", company_name or ""]
        try:
            ws.append_row(new_row, value_input_option=ValueInputOption.user_entered)
            return bool(True), "Solicitação de acesso enviada com sucesso."
        except Exception as e:
            return bool(False), f"Ocorreu um erro ao enviar a solicitação: {e}"

    def get_pending_requests(self):
        """Obtém todas as solicitações de acesso pendentes."""
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return []
        all_users = self._get_all_records_safe(ws)
        return [user for user in all_users if user.get("status") and str(user.get("status")).strip().lower() == "pending"]

    def update_user_status(self, email, new_status):
        """Atualiza o status de um utilizador específico."""
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return
        try:
            cell = ws.find(email, in_column=1)
            if cell: ws.update_cell(cell.row, 6, new_status)
        except gspread.exceptions.CellNotFound: # type: ignore
            print(f"Usuário {email} não encontrado.")
        except Exception as e: print(f"Erro ao atualizar status do usuário {email}: {e}")

    def get_occurrence_by_id(self, occurrence_id):
        """Obtém os detalhes de uma ocorrência pelo seu ID."""
        self._connect()
        for occ in self.get_all_occurrences():
            if str(occ.get('id')).strip().lower() == str(occurrence_id).strip().lower():
                return occ
        return None

    def update_occurrence_status(self, occurrence_id, new_status):
        """Atualiza o status de uma ocorrência específica."""
        self._connect()
        sheet_name, status_col = None, 7
        occ_id_lower = str(occurrence_id).strip().lower()
        if 'scall' in occ_id_lower: sheet_name = self.SIMPLE_CALLS_SHEET
        elif 'call' in occ_id_lower: sheet_name = self.CALLS_SHEET
        elif 'equip' in occ_id_lower:
            sheet_name = self.EQUIPMENT_SHEET
            status_col = 6
        if not sheet_name: return bool(False), "Tipo de ocorrência desconhecido."

        ws = self._get_worksheet(sheet_name)
        if not ws: return bool(False), f"Falha ao aceder à planilha {sheet_name}."

        try:
            cell = ws.find(occurrence_id, in_column=1)
            if cell:
                ws.update_cell(cell.row, status_col, new_status)
                return bool(True), "Status atualizado com sucesso."
            else:
                return bool(False), f"Ocorrência {occurrence_id} não encontrada."
        except gspread.exceptions.CellNotFound: # type: ignore
            return bool(False), f"Ocorrência com ID {occurrence_id} não encontrada."
        except Exception as e:
            return bool(False), f"Erro ao atualizar o status da ocorrência {occurrence_id}: {e}"

    def register_simple_call_occurrence(self, user_email, data):
        """Regista uma nova ocorrência de chamada simplificada."""
        self._connect()
        ws = self._get_worksheet(self.SIMPLE_CALLS_SHEET)
        if not ws: return bool(False), "Falha ao aceder à planilha."

        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_records = self._get_all_records_safe(ws)
            new_id = f"SCALL-{len([rec for rec in current_records if rec.get('id')]) + 1:04d}"
            user_profile = self.check_user_status(user_email)
            title_to_register = f"CHAMADA SIMPLES DE {data.get('origem', 'N/A')} PARA {data.get('destino', 'N/A')}"
            new_row = [
                new_id, now, title_to_register,
                user_email, user_profile.get("name", "N/A"), user_profile.get("username", "N/A"),
                'REGISTRADO', data.get('origem'), data.get('destino'), data.get('descricao'),
                user_profile.get("main_group", "N/A"), user_profile.get("company", "")
            ]
            ws.append_row(new_row, value_input_option=ValueInputOption.user_entered)
            return bool(True), "Ocorrência registrada com sucesso."
        except Exception as e:
            return bool(False), f"Ocorreu um erro ao registrar: {e}"

    def register_equipment_occurrence(self, user_credentials, user_email, data, attachment_paths):
        """Regista uma nova ocorrência de suporte a equipamento."""
        self._connect()
        ws = self._get_worksheet(self.EQUIPMENT_SHEET)
        if not ws: return bool(False), "Falha ao aceder à planilha de equipamentos."

        upload_success, result = self._upload_files_to_drive(user_credentials, attachment_paths)
        if not upload_success: return bool(False), result

        attachment_links_json = json.dumps(result)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_records = self._get_all_records_safe(ws)
        new_id = f"EQUIP-{len([rec for rec in current_records if rec.get('id')]) + 1:04d}"
        user_profile = self.check_user_status(user_email)
        title_to_register = data.get('tipo', f"EQUIPAMENTO {new_id}")
        new_row = [
            new_id, now, user_email, user_profile.get("name", "N/A"), user_profile.get("username", "N/A"),
            'REGISTRADO', title_to_register, data.get('modelo'), data.get('ramal'),
            data.get('localizacao'), data.get('descricao'), attachment_links_json,
            user_profile.get("main_group", "N/A"), user_profile.get("company", "")
        ]
        try:
            ws.append_row(new_row, value_input_option=ValueInputOption.user_entered)
            return bool(True), "Ocorrência de equipamento registrada com sucesso."
        except Exception as e:
            return bool(False), f"Ocorreu um erro ao registrar: {e}"

    def register_full_occurrence(self, user_email, title, testes):
        """Regista uma nova ocorrência de chamada detalhada."""
        self._connect()
        ws = self._get_worksheet(self.CALLS_SHEET)
        if not ws: return bool(False), "Falha ao aceder à planilha de chamadas."

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_records = self._get_all_records_safe(ws)
        new_id = f"CALL-{len([rec for rec in current_records if rec.get('id')]) + 1:04d}"
        user_profile = self.check_user_status(user_email)
        
        op_a = testes[0]['op_a'] if testes and isinstance(testes, list) and len(testes) > 0 else 'N/A'
        op_b = testes[0]['op_b'] if testes and isinstance(testes, list) and len(testes) > 0 else 'N/A'
        description = testes[0]['obs'] if testes and isinstance(testes, list) and len(testes) > 0 else ""
        testes_json = json.dumps(testes)

        new_row = [
            new_id, now, title, user_email, user_profile.get("name", "N/A"), user_profile.get("username", "N/A"),
            'REGISTRADO', op_a, op_b, testes_json, description,
            user_profile.get("main_group", "N/A"), user_profile.get("company", "")
        ]
        try:
            ws.append_row(new_row, value_input_option=ValueInputOption.user_entered)
            return bool(True), "Ocorrência detalhada registrada com sucesso."
        except Exception as e:
            return bool(False), f"Ocorreu um erro ao registrar: {e}"

    def add_occurrence_comment(self, occurrence_id, user_email, user_name, comment_text):
        """Adiciona um novo comentário a uma ocorrência."""
        self._connect()
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET)
        if not ws: return bool(False), "Falha ao aceder à planilha de comentários."

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comment_id = f"COM-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        new_row = [occurrence_id, comment_id, user_email, user_name, now, comment_text]
        try:
            ws.append_row(new_row, value_input_option=ValueInputOption.user_entered)
            return bool(True), "Comentário adicionado com sucesso."
        except Exception as e:
            return bool(False), f"Ocorreu um erro ao adicionar o comentário: {e}"

    def update_occurrence_comment(self, comment_id, new_comment_text):
        """Atualiza o texto de um comentário existente."""
        self._connect()
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET)
        if not ws: return bool(False), "Falha ao aceder à planilha de comentários."

        try:
            cell = ws.find(comment_id, in_column=2)
            if cell:
                ws.update_cell(cell.row, 6, new_comment_text)
                return bool(True), "Comentário atualizado com sucesso."
            else:
                return bool(False), f"Comentário com ID {comment_id} não encontrado."
        except gspread.exceptions.CellNotFound: # type: ignore
            return bool(False), f"Comentário com ID {comment_id} não encontrado."
        except Exception as e:
            return bool(False), f"Erro ao atualizar o comentário {comment_id}: {e}"

    def delete_occurrence_comment(self, comment_id):
        """Elimina um comentário da planilha."""
        self._connect()
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET)
        if not ws: return bool(False), "Falha ao aceder à planilha de comentários."

        try:
            cell = ws.find(comment_id, in_column=2)
            if cell:
                ws.delete_rows(cell.row)
                return bool(True), "Comentário eliminado com sucesso."
            else:
                return bool(False), f"Comentário com ID {comment_id} não encontrado."
        except gspread.exceptions.CellNotFound: # type: ignore
            return bool(False), f"Comentário com ID {comment_id} não encontrado."
        except Exception as e:
            return bool(False), f"Erro ao eliminar o comentário {comment_id}: {e}"

    def get_occurrence_comments(self, occurrence_id):
        """Obtém todos os comentários associados a uma ocorrência."""
        self._connect()
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET)
        if not ws: return []

        try:
            all_comments = self._get_all_records_safe(ws)
            filtered_comments = [
                comment for comment in all_comments
                if comment.get('id_ocorrencia') and str(comment['id_ocorrencia']).strip().lower() == str(occurrence_id).strip().lower()
            ]
            return sorted(filtered_comments, key=lambda x: x.get('Data_Comentario', ''), reverse=True)
        except Exception as e:
            print(f"Erro ao obter comentários da ocorrência {occurrence_id}: {e}")
            return []

    def get_all_operators(self):
        """Obtém a lista de todas as operadoras da planilha de operadores."""
        self._connect()
        ws = self._get_worksheet(self.OPERATORS_SHEET)
        if not ws:
            print("AVISO: Planilha de operadores não encontrada. Retornando lista vazia.")
            return []
        try:
            # Assume AAdmin123@@que a lista de operadores está na primeira coluna
            # e pula o cabeçalho se houver
            operators = [row[0] for row in ws.get_all_values() if row and row[0].strip()][1:]
            return sorted(list(set(operators))) # Remove duplicatas e ordena
        except Exception as e:
            print(f"Erro ao obter lista de operadores: {e}")
            return []
