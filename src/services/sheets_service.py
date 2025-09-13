# ==============================================================================
# FICHEIRO: src/services/sheets_service.py
# DESCRIÇÃO: Lida com todas as operações de leitura e escrita na planilha
#            Google Sheets.
# DATA DA ATUALIZAÇÃO: 28/08/2025
# NOTAS: Corrigidos os alertas do Pylance relacionados a valores 'None' no cache
#        e na lógica de data. Adicionadas verificações explícitas de 'None'
#        para garantir que as operações de cache e de data sejam seguras.
# ==============================================================================

import gspread
import json
import uuid
import csv
from datetime import datetime, timedelta
from googleapiclient.http import MediaFileUpload
import os
from tkinter import messagebox
import threading
from gspread.utils import ValueInputOption
from typing import Optional, Dict, Any, List, Union, Tuple

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
        # NOTA: A constante OCCURRENCES_SHEET não estava definida.
        # Se você tiver uma aba que consolida todas as ocorrências, adicione o nome dela aqui.
        # Por enquanto, será comentado para evitar erros.
        # self.OCCURRENCES_SHEET = "all_occurrences"
        self.OPERATORS_SHEET = "operators"

        self.gspread_lock = threading.Lock()
        self._GC: Optional[gspread.Client] = None
        self._SPREADSHEET: Optional[gspread.Spreadsheet] = None
        self.is_connected = False
        
        self._cache: Dict[str, Dict[str, Any]] = {
            self.USERS_SHEET: {'data': None, 'timestamp': None},
            self.CALLS_SHEET: {'data': None, 'timestamp': None},
            self.SIMPLE_CALLS_SHEET: {'data': None, 'timestamp': None},
            self.EQUIPMENT_SHEET: {'data': None, 'timestamp': None},
            self.OPERATORS_SHEET: {'data': None, 'timestamp': None},
            "all_occurrences_cache": {'data': None, 'timestamp': None}
        }
        self.CACHE_DURATION_MINUTES = 5


    def _connect(self):
        """Conecta-se ao Google Sheets."""
        print(f"DEBUG: Tentando conectar ao Google Sheets...")
        if self.is_connected and self._SPREADSHEET:
            try:
                if self._SPREADSHEET.id:
                    print(f"DEBUG: Já conectado ao Sheets")
                    return
            except Exception:
                print(f"DEBUG: Conexão anterior inválida, reconectando...")
                self.is_connected = False
                self._GC = None
                self._SPREADSHEET = None
        
        with self.gspread_lock:
            if self.is_connected:
                return

            print(f"DEBUG: Obtendo credenciais da conta de serviço...")
            self._SERVICE_CREDENTIALS = self.auth_service.get_service_account_credentials()
            if not self._SERVICE_CREDENTIALS:
                print(f"DEBUG: Erro ao obter credenciais da conta de serviço")
                self.is_connected = False
                return

            try:
                print(f"DEBUG: Conectando com gspread...")
                self._GC = gspread.service_account(filename=self.auth_service.SERVICE_ACCOUNT_FILE)
                print(f"DEBUG: Abrindo planilha com ID: {self.SPREADSHEET_ID}")
                self._SPREADSHEET = self._GC.open_by_key(self.SPREADSHEET_ID)
                self.is_connected = True
                print(f"DEBUG: Conectado com sucesso ao Google Sheets")
            except Exception as e:
                 print(f"DEBUG: Erro ao conectar ao Google Sheets: {e}")
                 messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao Google Sheets: {e}")
                 self.is_connected = False
                 self._GC = None
                 self._SPREADSHEET = None

    def _get_worksheet(self, sheet_name: str) -> Optional[gspread.Worksheet]:
        """Obtém uma aba específica da planilha."""
        self._connect()
        if not self._SPREADSHEET: 
            print(f"ERRO: Não conectado à planilha principal. Falha ao obter a aba '{sheet_name}'.")
            return None

        try:
            return self._SPREADSHEET.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            print(f"ERRO: A aba '{sheet_name}' não foi encontrada na planilha.")
            messagebox.showerror("Erro de Planilha", f"A aba '{sheet_name}' não foi encontrada na planilha do Google Sheets. Verifique o nome da aba.")
            return None
        except Exception as e:
            print(f"ERRO ao obter a aba '{sheet_name}': {e}")
            messagebox.showerror("Erro de Acesso", f"Ocorreu um erro ao tentar aceder à aba '{sheet_name}': {e}")
            return None

    def _get_all_records_safe(self, worksheet: gspread.Worksheet) -> List[Dict[str, str]]:
        """Lê todos os registos de uma aba de forma segura."""
        with self.gspread_lock:
            all_values = worksheet.get_all_values()
            if not all_values:
                return []

            raw_headers = all_values[0]
            data_rows = all_values[1:]

            processed_headers = []
            seen_headers: Dict[str, int] = {}
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

    def _share_file_with_users(self, drive_service: Any, file_id: str, uploader_email: str):
        """Compartilha o arquivo com o uploader e administradores."""
        emails_to_share_with = {uploader_email}
        
        try:
            all_users = self.get_all_users()
            if all_users:
                # Coleta emails de administradores, garantindo que não sejam None
                admin_emails: List[str] = []
                for user in all_users:
                    email = user.get('email')
                    if (user.get('sub_group') in ['ADMIN', 'SUPER_ADMIN'] and 
                        email is not None):
                        admin_emails.append(email)
                
                emails_to_share_with.update(admin_emails)
        except Exception as e:
            print(f"AVISO: Não foi possível obter lista de administradores: {e}")

        for email in emails_to_share_with:
            try:
                permission = {
                    'type': 'user',
                    'role': 'reader',
                    'emailAddress': email
                }
                drive_service.permissions().create(fileId=file_id, body=permission, fields='id').execute()
            except Exception as e:
                print(f"AVISO: Não foi possível compartilhar o arquivo {file_id} com {email}. Erro: {e}")

    def _upload_files_to_drive(self, user_credentials: Any, file_paths: List[str], uploader_email: str) -> Tuple[bool, Union[str, List[str]]]:
        """Faz upload de ficheiros para o Google Drive."""
        if not file_paths:
            return True, []
        
        drive_service = self.auth_service.get_drive_service(user_credentials)
        if not drive_service:
            return False, "Não foi possível obter o serviço do Google Drive."

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
                
                self._share_file_with_users(drive_service, file.get('id'), uploader_email)

                uploaded_file_links.append(file.get('webViewLink'))

            return True, uploaded_file_links
        except Exception as e:
            return False, f"Ocorreu um erro durante o upload para o Google Drive: {e}"

    # --- MÉTODOS DE CRIAÇÃO DE OCORRÊNCIAS ---

    def register_full_occurrence(self, user_email: str, title: str, tests: List[Dict[str, str]]) -> Tuple[bool, str]:
        """Registra uma ocorrência de chamada detalhada com testes."""
        self._connect()
        ws = self._get_worksheet(self.CALLS_SHEET)
        if not ws:
            return False, "Falha ao aceder à planilha de ocorrências de chamada."

        user_profile = self.check_user_status(user_email)
        if not user_profile or user_profile.get("status") != "approved":
            return False, "Utilizador não autorizado."

        try:
            occurrence_id = f"CALL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
            registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "REGISTRADO"
            tests_json = json.dumps(tests)

            new_row = [
                occurrence_id, title, registration_date, user_email,
                user_profile.get("name", ""), user_profile.get("username", ""),
                status, tests_json, "[]", # Anexos (vazio por defeito)
                user_profile.get("main_group", ""), user_profile.get("company", "")
            ]
            
            ws.append_row(new_row, value_input_option=ValueInputOption.user_entered)
            self._cache.pop("all_occurrences_cache", None)
            return True, f"Ocorrência {occurrence_id} registada com sucesso."
        except Exception as e:
            return False, f"Erro ao registar ocorrência: {e}"

    def register_simple_call_occurrence(self, user_email: str, data: Dict[str, str]) -> Tuple[bool, str]:
        """Registra uma ocorrência de chamada simplificada."""
        self._connect()
        ws = self._get_worksheet(self.SIMPLE_CALLS_SHEET)
        if not ws: return False, "Falha ao aceder à planilha de chamadas simples."

        user_profile = self.check_user_status(user_email)
        if not user_profile or user_profile.get("status") != "approved": return False, "Utilizador não autorizado."

        try:
            occurrence_id = f"SCALL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
            registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "REGISTRADO"
            title = f"CHAMADA SIMPLES DE {data.get('origem', 'N/A')} PARA {data.get('destino', 'N/A')}"

            new_row = [
                occurrence_id, title, registration_date, user_email,
                user_profile.get("name", ""), user_profile.get("username", ""), status,
                data.get("origem", ""), data.get("destino", ""), data.get("operadora", ""),
                data.get("status_chamada", ""), data.get("observacoes", ""),
                user_profile.get("main_group", ""), user_profile.get("company", "")
            ]
            ws.append_row(new_row, value_input_option=ValueInputOption.user_entered)
            self._cache.pop("all_occurrences_cache", None)
            return True, f"Ocorrência {occurrence_id} registada com sucesso."
        except Exception as e:
            return False, f"Erro ao registar ocorrência de chamada simples: {e}"

    def register_equipment_occurrence(self, user_credentials: Any, user_email: str, data: Dict[str, str], attachment_paths: List[str]) -> Tuple[bool, str]:
        """Registra uma ocorrência de equipamento, com upload de anexos."""
        self._connect()
        ws = self._get_worksheet(self.EQUIPMENT_SHEET)
        if not ws: return False, "Falha ao aceder à planilha de ocorrências de equipamento."

        user_profile = self.check_user_status(user_email)
        if not user_profile or user_profile.get("status") != "approved": return False, "Utilizador não autorizado."

        uploaded_file_links = []
        if attachment_paths:
            success, result = self._upload_files_to_drive(user_credentials, attachment_paths, user_email)
            if not success: return False, f"Falha no upload de anexos: {result}"
            uploaded_file_links = result

        try:
            occurrence_id = f"EQUIP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
            registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "REGISTRADO"
            title = f"SUPORTE EQUIPAMENTO: {data.get('tipo_equipamento', 'N/A')} - {data.get('localizacao', 'N/A')}"
            anexos_json = json.dumps(uploaded_file_links)

            new_row = [
                occurrence_id, title, registration_date, user_email, user_profile.get("name", ""), status,
                data.get("tipo_equipamento", ""), data.get("modelo", ""), data.get("ramal", ""),
                data.get("localizacao", ""), data.get("descricao_problema", ""), anexos_json,
                user_profile.get("main_group", ""), user_profile.get("company", "")
            ]
            ws.append_row(new_row, value_input_option=ValueInputOption.user_entered)
            self._cache.pop("all_occurrences_cache", None)
            return True, f"Ocorrência {occurrence_id} registada com sucesso."
        except Exception as e:
            return False, f"Erro ao registar ocorrência de equipamento: {e}"

    def batch_update_occurrence_statuses(self, changes: Dict[str, str]) -> Tuple[bool, str]:
        """Atualiza múltiplos status de ocorrências de uma só vez."""
        self._connect()
        if not self._SPREADSHEET: return False, "Falha na conexão."

        updates_by_sheet: Dict[str, List[gspread.Cell]] = {
            self.CALLS_SHEET: [],
            self.SIMPLE_CALLS_SHEET: [],
            self.EQUIPMENT_SHEET: []
        }

        all_ids_map: Dict[str, Dict[str, Any]] = {}
        for sheet_name in updates_by_sheet.keys():
            ws = self._get_worksheet(sheet_name)
            if ws:
                ids_in_sheet = ws.col_values(1)
                for i, occ_id in enumerate(ids_in_sheet):
                    if i == 0: continue  # Pula o cabeçalho
                    if occ_id:  # Verificar se occ_id não é None ou vazio
                        all_ids_map[str(occ_id)] = {'sheet': sheet_name, 'row': i + 1}

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

    def batch_update_user_profiles(self, changes: Dict[str, Dict[str, str]]) -> Tuple[bool, str]:
        """Atualiza múltiplos perfis de utilizador de uma só vez."""
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return False, "Falha na conexão com a aba de utilizadores."

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
            return True, "Perfis atualizados com sucesso."
        except Exception as e:
            return False, f"Erro na atualização de perfis em lote: {e}"

    def check_user_status(self, email: str) -> Dict[str, str]:
        """Verifica o status e o perfil de um utilizador."""
        print(f"DEBUG: Verificando status do usuário: {email}")
        self._connect()
        print(f"DEBUG: Conectado ao Sheets: {self.is_connected}")
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws:
            print("DEBUG: Erro ao acessar planilha de usuários")
            return {"status": "error"}
        
        cache_key = self.USERS_SHEET
        cache_data = self._cache[cache_key]['data']
        cache_timestamp = self._cache[cache_key]['timestamp']
        
        is_cache_valid = (
            cache_data is not None and
            cache_timestamp is not None and
            (datetime.now() - cache_timestamp).total_seconds() < (self.CACHE_DURATION_MINUTES * 60)
        )
        if is_cache_valid:
            records = cache_data
        else:
            try:
                records = self._get_all_records_safe(ws)
                self._cache[cache_key]['data'] = records
                self._cache[cache_key]['timestamp'] = datetime.now()
            except Exception as e:
                print(f"Erro ao ler a planilha de usuários: {e}")
                return {"status": "error"}
        
        if records is None:
            return {"status": "error"}
            
        print(f"DEBUG: Buscando usuário em {len(records) if records else 0} registros")
        for user_rec in records:
            if user_rec.get("email") and str(user_rec["email"]).strip().lower() == email.strip().lower():
                print(f"DEBUG: Usuário encontrado: {user_rec}")
                return user_rec
        print(f"DEBUG: Usuário não encontrado, retornando unregistered")
        return {"status": "unregistered"}

    def get_all_users(self, force_refresh: bool = False) -> List[Dict[str, str]]:
        """Obtém todos os utilizadores registados, utilizando cache."""
        cache_key = self.USERS_SHEET
        cache_data = self._cache[cache_key]['data']
        cache_timestamp = self._cache[cache_key]['timestamp']
        
        is_cache_valid = (
            cache_data is not None and
            cache_timestamp is not None and
            (datetime.now() - cache_timestamp).total_seconds() < (self.CACHE_DURATION_MINUTES * 60)
        )
        if not force_refresh and is_cache_valid:
            return cache_data or []
            
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return []
        
        records = [rec for rec in (self._get_all_records_safe(ws) or []) if rec.get("email")]
        self._cache[cache_key]['data'] = records
        self._cache[cache_key]['timestamp'] = datetime.now()
        return records

    def request_access(self, email: str, full_name: str, username: str, main_group: str, sub_group: str, company_name: Optional[str] = None) -> Tuple[bool, str]:
        """Envia uma solicitação de acesso para um novo utilizador."""
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return False, "Falha ao aceder à planilha."

        try:
            all_users_records = self._get_all_records_safe(ws)
            if all_users_records is None:
                return False, "Erro ao verificar e-mail existente: dados da planilha ausentes."
            
            normalized_emails_in_sheet = [str(rec.get('email', '')).strip().lower() for rec in all_users_records]
            if email.strip().lower() in normalized_emails_in_sheet:
                return False, "Solicitação já existe para este e-mail."
        except Exception as e:
            return False, f"Erro ao verificar e-mail existente: {e}"

        new_row = [email, full_name, username, main_group, sub_group, "pending", company_name or ""]
        try:
            ws.append_row(new_row, value_input_option=ValueInputOption.user_entered)
            self._cache[self.USERS_SHEET]['data'] = None
            return True, "Solicitação de acesso enviada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao enviar a solicitação: {e}"

    def get_pending_requests(self) -> List[Dict[str, str]]:
        """Obtém todas as solicitações de acesso pendentes, utilizando cache."""
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return []
        
        all_users = self.get_all_users()
        return [user for user in (all_users or []) if user.get("status") and str(user.get("status")).strip().lower() == "pending"]

    def update_user_status(self, email: str, new_status: str) -> Tuple[bool, str]:
        """Atualiza o status de um utilizador específico."""
        self._connect()
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return False, "Falha ao aceder à planilha de usuários."
        try:
            cell = ws.find(email, in_column=1)
            if cell: 
                ws.update_cell(cell.row, 6, new_status)
                self._cache[self.USERS_SHEET]['data'] = None
            return True, "Status do usuário atualizado com sucesso."
        except Exception as e:
            if "not found" in str(e).lower():
                print(f"Usuário {email} não encontrado.")
                return False, f"Usuário {email} não encontrado na planilha."
            else:
                print(f"Erro ao atualizar status do usuário {email}: {e}")
                return False, f"Erro ao atualizar status do usuário {email}: {e}"

    def update_occurrence_status(self, occurrence_id: str, new_status: str) -> Tuple[bool, str]:
        """Atualiza o status de uma ocorrência específica."""
        self._connect()
        sheet_name, status_col = "", 7
        occ_id_lower = occurrence_id.strip().lower()
        if 'scall' in occ_id_lower: sheet_name = self.SIMPLE_CALLS_SHEET
        elif 'call' in occ_id_lower: sheet_name = self.CALLS_SHEET
        elif 'equip' in occ_id_lower:
            sheet_name = self.EQUIPMENT_SHEET
            status_col = 6
        if not sheet_name: return False, "Tipo de ocorrência desconhecido."

        ws = self._get_worksheet(sheet_name)
        if not ws: return False, f"Falha ao aceder à planilha {sheet_name}."

        try:
            cell = ws.find(occurrence_id, in_column=1)
            if cell:
                ws.update_cell(cell.row, status_col, new_status)
                self._cache.pop("all_occurrences_cache", None)
                if self._cache.get(sheet_name):
                    self._cache[sheet_name]['data'] = None
                return True, "Status atualizado com sucesso."
            else:
                return False, f"Ocorrência {occurrence_id} não encontrada."
        except Exception as e:
            if "not found" in str(e).lower():
                return False, f"Ocorrência com ID {occurrence_id} não encontrada."
            else:
                return False, f"Erro ao atualizar o status da ocorrência {occurrence_id}: {e}"

    def update_occurrence_comment(self, comment_id: str, new_comment_text: str) -> Tuple[bool, str]:
        """Atualiza o texto de um comentário existente."""
        self._connect()
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET)
        if not ws: return False, "Falha ao aceder à planilha de comentários."

        try:
            cell = ws.find(comment_id, in_column=2)
            if cell:
                ws.update_cell(cell.row, 6, new_comment_text)
                return True, "Comentário atualizado com sucesso."
            else:
                return False, f"Comentário com ID {comment_id} não encontrado."
        except Exception as e:
            if "not found" in str(e).lower():
                return False, f"Comentário com ID {comment_id} não encontrado."
            else:
                return False, f"Erro ao atualizar o comentário {comment_id}: {e}"

    def delete_occurrence_comment(self, comment_id: str) -> Tuple[bool, str]:
        """Elimina um comentário da planilha."""
        self._connect()
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET)
        if not ws: return False, "Falha ao aceder à planilha de comentários."

        try:
            cell = ws.find(comment_id, in_column=2)
            if cell:
                ws.delete_rows(cell.row)
                return True, "Comentário eliminado com sucesso."
            else:
                return False, f"Comentário com ID {comment_id} não encontrado."
        except Exception as e:
            if "not found" in str(e).lower():
                return False, f"Comentário com ID {comment_id} não encontrado."
            else:
                return False, f"Erro ao eliminar o comentário {comment_id}: {e}"

    def get_occurrence_comments(self, occurrence_id: str) -> List[Dict[str, str]]:
        """Obtém todos os comentários associados a uma ocorrência."""
        self._connect()
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET)
        if not ws: return []

        try:
            all_comments = self._get_all_records_safe(ws)
            if not all_comments:
                return []
            filtered_comments = [
                comment for comment in all_comments
                if comment.get('id_ocorrencia') and str(comment['id_ocorrencia']).strip().lower() == occurrence_id.strip().lower()
            ]
            return sorted(filtered_comments, key=lambda x: x.get('Data_Comentario', ''), reverse=True)
        except Exception as e:
            print(f"Erro ao obter comentários da ocorrência {occurrence_id}: {e}")
            return []

    def get_all_operators(self, force_refresh: bool = False) -> List[str]:
        """Obtém a lista de todas as operadoras da planilha de operadores."""
        cache_key = self.OPERATORS_SHEET
        cache_data = self._cache[cache_key]['data']
        cache_timestamp = self._cache[cache_key]['timestamp']
        
        is_cache_valid = (
            cache_data is not None and
            cache_timestamp is not None and
            (datetime.now() - cache_timestamp).total_seconds() < (self.CACHE_DURATION_MINUTES * 60)
        )
        if not force_refresh and is_cache_valid:
            return cache_data or []
            
        self._connect()
        ws = self._get_worksheet(self.OPERATORS_SHEET)
        if not ws:
            return []
        try:
            all_records = self._get_all_records_safe(ws)
            operators = [rec.get('operadora', '') for rec in (all_records or []) if rec.get('operadora')]
            if not operators:
                print(f"AVISO: A planilha '{self.OPERATORS_SHEET}' está vazia ou não contém operadoras.")
                messagebox.showwarning("Dados Incompletos", f"A planilha '{self.OPERATORS_SHEET}' está vazia ou não contém dados de operadoras. As sugestões não serão exibidas.")
                return []
            
            unique_operators = sorted(list(set(operators)))
            self._cache[cache_key]['data'] = unique_operators
            self._cache[cache_key]['timestamp'] = datetime.now()
            return unique_operators
        except Exception as e:
            print(f"Erro ao obter lista de operadoras da planilha '{self.OPERATORS_SHEET}': {e}")
            messagebox.showerror("Erro de Leitura", f"Ocorreu um erro ao ler a lista de operadoras da planilha '{self.OPERATORS_SHEET}': {e}")
            return []

    def get_occurrence_by_id(self, occurrence_id: str) -> Optional[Dict[str, str]]:
        """Obtém os detalhes de uma ocorrência específica pelo seu ID."""
        all_occurrences = self.get_all_occurrences()
        
        for occ in all_occurrences:
            if occ.get('ID') and str(occ['ID']).strip().lower() == occurrence_id.strip().lower():
                return occ
        
        all_occurrences_fresh = self.get_all_occurrences(force_refresh=True)
        for occ in all_occurrences_fresh:
            if occ.get('ID') and str(occ['ID']).strip().lower() == occurrence_id.strip().lower():
                return occ
        
        return None

    def add_occurrence_comment(self, occurrence_id: str, user_email: str, user_name: str, comment_text: str) -> Tuple[bool, str]:
        """Adiciona um novo comentário a uma ocorrência."""
        self._connect()
        ws = self._get_worksheet(self.OCCURRENCE_COMMENTS_SHEET)
        if not ws: return False, "Falha ao aceder à planilha de comentários."

        try:
            comment_id = f"CMT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
            comment_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            new_row = [occurrence_id, comment_id, user_email, user_name, comment_date, comment_text]

            ws.append_row(new_row, value_input_option=ValueInputOption.user_entered)
            return True, "Comentário adicionado com sucesso."
        except Exception as e:
            return False, f"Erro ao adicionar comentário: {e}"


    # --- MÉTODOS DE OCORRÊNCIAS (Combinados) ---

    def get_all_occurrences(self, force_refresh: bool = False) -> List[Dict[str, str]]:
        """
        Obtém TODAS as ocorrências de todas as abas (chamada, equipamento, etc.),
        utilizando um cache consolidado.
        """
        cache_key = "all_occurrences_cache"
        cache_entry = self._cache.get(cache_key)

        if cache_entry:
            is_cache_valid = (
                cache_entry.get('data') is not None and
                cache_entry.get('timestamp') is not None and
                (datetime.now() - cache_entry['timestamp']).total_seconds() < (self.CACHE_DURATION_MINUTES * 60)
            )
            if not force_refresh and is_cache_valid:
                return cache_entry['data'] or []

        all_occurrences = []
        sheet_names = [self.CALLS_SHEET, self.SIMPLE_CALLS_SHEET, self.EQUIPMENT_SHEET]

        for sheet_name in sheet_names:
            ws = self._get_worksheet(sheet_name)
            if ws:
                try:
                    records = self._get_all_records_safe(ws)
                    if records:
                        all_occurrences.extend(records)
                except Exception as e:
                    print(f"Erro ao ler a aba '{sheet_name}': {e}")

        # Ordena por data de registro, do mais novo para o mais antigo
        # Adicionado tratamento para casos onde a data pode estar ausente ou mal formatada
        def sort_key(occ):
            date_str = occ.get('Data de Registro')
            if not date_str:
                return datetime.min
            try:
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                return datetime.min

        sorted_occurrences = sorted(all_occurrences, key=sort_key, reverse=True)

        self._cache[cache_key] = {'data': sorted_occurrences, 'timestamp': datetime.now()}
        return sorted_occurrences


    def get_all_occurrences_for_admin(self, force_refresh: bool = False) -> List[Dict[str, str]]:
        """Obtém todas as ocorrências para o dashboard de admin, utilizando cache."""
        # Este método agora é um wrapper para get_all_occurrences, pois o admin vê tudo.
        return self.get_all_occurrences(force_refresh=force_refresh)

    def get_occurrences_by_user(self, user_email: str, force_refresh: bool = False) -> List[Dict[str, str]]:
        """
        Obtém as ocorrências visíveis para um utilizador específico, respeitando as regras de grupo.
        - 67_TELECOM: Acesso total a todas as ocorrências.
        - PREFEITURA: Acesso apenas a ocorrências do grupo 'PREFEITURA'.
        - PARTNER: Acesso apenas a ocorrências da sua própria empresa dentro do grupo 'PARTNER'.
        - Outros: Acesso apenas às ocorrências que registou.
        """
        all_occurrences = self.get_all_occurrences(force_refresh=force_refresh)
        user_profile = self.check_user_status(user_email)

        main_group = user_profile.get("main_group")
        if not main_group:
            return []

        # Super Admins e Admins (67_TELECOM) veem tudo
        if main_group == "67_TELECOM":
            return all_occurrences

        # Prefeitura vê APENAS as suas próprias ocorrências
        if main_group == "PREFEITURA":
            return [
                occ for occ in all_occurrences
                if str(occ.get('registradormaingroup', '')).upper() == "PREFEITURA"
            ]

        # Parceiros veem APENAS as da sua própria empresa
        if main_group == "PARTNER":
            user_company = user_profile.get("company")
            if not user_company:
                # Se um parceiro não tem empresa definida, não deve ver nenhuma ocorrência de parceiro.
                return []
            
            return [
                occ for occ in all_occurrences
                if str(occ.get('registradormaingroup', '')).upper() == "PARTNER" and \
                   str(occ.get('registradorcompany', '')).upper() == str(user_company).upper()
            ]

        # Caso padrão (se houver outros grupos no futuro), mostra apenas as próprias
        return [occ for occ in all_occurrences if occ.get('Registrador (e-mail)') == user_email]

    def clear_all_cache(self):
        """Limpa todo o cache da planilha."""
        for key in self._cache:
            self._cache[key]['data'] = None
            self._cache[key]['timestamp'] = None

    def register_occurrence(self, user_email: str, data: Dict[str, str], tests: List[Dict[str, str]], attachment_path: Optional[str] = None) -> Tuple[bool, str]:
        """Registra uma ocorrência de chamada detalhada com testes e anexos opcionais."""
        self._connect()
        ws = self._get_worksheet(self.CALLS_SHEET)
        if not ws:
            return False, "Falha ao aceder à planilha de ocorrências de chamada."

        user_profile = self.check_user_status(user_email)
        if not user_profile or user_profile.get("status") != "approved":
            return False, "Utilizador não autorizado."

        try:
            occurrence_id = f"CALL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
            registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "REGISTRADO"
            tests_json = json.dumps(tests)
            attachment_json = json.dumps([attachment_path] if attachment_path else [])

            new_row = [
                occurrence_id, data.get('title', ''), registration_date, user_email,
                user_profile.get("name", ""), user_profile.get("username", ""),
                status, tests_json, attachment_json,
                user_profile.get("main_group", ""), user_profile.get("company", "")
            ]
            
            ws.append_row(new_row, value_input_option=ValueInputOption.user_entered)
            self._cache.pop("all_occurrences_cache", None)
            return True, f"Ocorrência {occurrence_id} registada com sucesso."
        except Exception as e:
            return False, f"Erro ao registar ocorrência: {e}"