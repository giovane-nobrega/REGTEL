# ==============================================================================
# ARQUIVO: src/services/sheets_service.py
# DESCRIÇÃO: (VERSÃO REATORADA) Lida com as operações de baixo nível e a lógica
#            de filtragem de dados da planilha Google Sheets.
# ==============================================================================

import gspread
from googleapiclient.http import MediaFileUpload
from datetime import datetime
from tkinter import messagebox
import threading
from builtins import Exception, print, len, str, sorted, list, set, enumerate, dict, bool, isinstance, range
import os

class SheetsService:
    """
    Serviço de baixo nível para interação direta com a API do Google Sheets.
    Responsável pela conexão, autenticação de serviço e operações CRUD,
    bem como a lógica de filtragem de dados.
    """
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
        """Estabelece a conexão com a API do Google Sheets usando uma conta de serviço."""
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
        """Obtém um objeto de planilha (aba) pelo nome."""
        self._connect()
        if not self._SPREADSHEET: return None
        try:
            return self._SPREADSHEET.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"ERRO: A aba '{sheet_name}' não foi encontrada.")
            return None
        except Exception as e:
            print(f"ERRO ao obter a aba '{sheet_name}': {e}")
            return None
            
    def _get_all_records_safe(self, worksheet):
        """Lê todos os registros de uma planilha de forma segura, normalizando os cabeçalhos."""
        with self.gspread_lock:
            try:
                all_values = worksheet.get_all_values()
                if not all_values: return []
                raw_headers = all_values[0]
                data_rows = all_values[1:]
                processed_headers = []
                seen_headers = {}
                for i, header in enumerate(raw_headers):
                    original_header = header.strip() if header else f"col_{i}"
                    normalized_header = original_header.lower().replace(' ', '')
                    if normalized_header in seen_headers:
                        seen_headers[normalized_header] += 1
                        normalized_header = f"{normalized_header}_{seen_headers[normalized_header]}"
                    else:
                        seen_headers[normalized_header] = 0
                    processed_headers.append(normalized_header)
                processed_records = []
                for row in data_rows:
                    processed_rec = {}
                    for i, header in enumerate(processed_headers):
                        if i < len(row):
                            value = row[i]
                            processed_rec[header] = value
                            if raw_headers[i].strip() and raw_headers[i].strip() != header:
                                processed_rec[raw_headers[i].strip()] = value
                    processed_records.append(processed_rec)
                return processed_records
            except Exception as e:
                print(f"ERRO CRÍTICO em _get_all_records_safe para '{worksheet.title}': {e}")
                return []

    def upload_files_to_drive(self, user_credentials, file_paths):
        """Faz o upload de arquivos para o Google Drive do usuário."""
        if not file_paths: return True, []
        drive_service = self.auth_service.get_drive_service(user_credentials)
        if not drive_service: return False, "Não foi possível obter o serviço do Google Drive."
        try:
            q = "mimeType='application/vnd.google-apps.folder' and name='Craft Quest Anexos' and trashed=false"
            response = drive_service.files().list(q=q, spaces='drive', fields='files(id, name)').execute()
            folder_id = None
            if response.get('files'):
                folder_id = response.get('files')[0].get('id')
            else:
                folder_metadata = {'name': 'Craft Quest Anexos', 'mimeType': 'application/vnd.google-apps.folder'}
                folder_id = drive_service.files().create(body=folder_metadata, fields='id').execute().get('id')
            
            uploaded_file_links = []
            for file_path in file_paths:
                file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
                media = MediaFileUpload(file_path, resumable=True)
                file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
                drive_service.permissions().create(fileId=file.get('id'), body={'role': 'reader', 'type': 'anyone'}).execute()
                uploaded_file_links.append(file.get('webViewLink'))
            return True, uploaded_file_links
        except Exception as e:
            return False, f"Erro durante o upload para o Google Drive: {e}"

    # ==============================================================================
    # --- MÉTODOS DE ACESSO E FILTRAGEM DE DADOS ---
    # ==============================================================================
    
    def get_all_occurrences(self):
        """Busca todas as ocorrências de todas as abas e as normaliza."""
        all_occurrences = []
        sheet_map = {
            self.CALLS_SHEET: "call",
            self.SIMPLE_CALLS_SHEET: "simple_call",
            self.EQUIPMENT_SHEET: "equipment"
        }

        for sheet_name, record_type in sheet_map.items():
            ws = self._get_worksheet(sheet_name)
            if ws:
                records = self._get_all_records_safe(ws)
                for rec in records:
                    if rec.get('id'):
                        rec['Título da Ocorrência'] = self._get_final_title(rec, record_type)
                        all_occurrences.append(rec)

        return sorted(all_occurrences, key=lambda x: x.get('Data de Registro', ''), reverse=True)

    def _get_final_title(self, record, record_type):
        """
        Função auxiliar para determinar o título de uma ocorrência, priorizando
        o título registrado pelo usuário.
        """
        possible_title_headers = ['Título da Ocorrência', 'Título', 'Title']
        
        for header in possible_title_headers:
            value = record.get(header) or record.get(header.lower().replace(' ', ''))
            if value and str(value).strip():
                return str(value).strip()
        
        record_id = record.get('id', 'N/A')
        if record_type == "simple_call":
            origem = record.get('origem') or record.get('númerodeorigem') or 'N/A'
            destino = record.get('destino') or record.get('númerodedestino') or 'N/A'
            return f"Chamada Simples de {origem} para {destino}"
        elif record_type == "equipment":
            return record.get('tipo', f"Equipamento {record_id}")
        
        return f"Ocorrência {record_id}"

    def get_occurrences_by_user(self, user_email):
        """
        Obtém as ocorrências visíveis para um usuário específico,
        filtrando com base no seu perfil e empresa/departamento.
        """
        user_profile = self.check_user_status(user_email)
        if not user_profile or user_profile.get('status') != 'approved':
            return []

        main_group = user_profile.get("main_group", "").strip().upper()
        user_company = user_profile.get("company", "").strip().upper()
        all_occurrences = self.get_all_occurrences()
        
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

    def get_occurrence_by_id(self, occurrence_id):
        """
        Obtém os detalhes de uma ocorrência específica pelo seu ID.
        """
        for occ in self.get_all_occurrences():
            if str(occ.get('id')).strip().lower() == str(occurrence_id).strip().lower():
                return occ
        return None

    # --- MÉTODOS DE REGISTRO (CREATE) ---
    def register_simple_call_occurrence(self, data):
        """Registra uma ocorrência de chamada simples na planilha."""
        ws = self._get_worksheet(self.SIMPLE_CALLS_SHEET)
        if not ws: return False, "Falha ao acessar a planilha."
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_ids = [rec.get('id') for rec in self._get_all_records_safe(ws) if rec.get('id')]
            new_id = f"SCALL-{len(current_ids) + 1:04d}"
            new_row = [new_id, now, data['title'], data['user_email'], data['user_name'], data['user_username'],
                       data['status'], data['origem'], data['destino'], data['descricao'],
                       data['main_group'], data['company']]
            ws.append_row(new_row, value_input_option='USER_ENTERED') # pyright: ignore[reportArgumentType]
            return True, "Ocorrência registrada com sucesso."
        except Exception as e:
            return False, f"Erro ao registrar: {e}"

    def register_equipment_occurrence(self, data):
        """Registra uma ocorrência de equipamento na planilha."""
        ws = self._get_worksheet(self.EQUIPMENT_SHEET)
        if not ws: return False, "Falha ao acessar a planilha."
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_ids = [rec.get('id') for rec in self._get_all_records_safe(ws) if rec.get('id')]
            new_id = f"EQUIP-{len(current_ids) + 1:04d}"
            new_row = [new_id, now, data['user_email'], data['user_name'], data['user_username'],
                       data['status'], data['title'], data['modelo'], data['ramal'],
                       data['localizacao'], data['descricao'], data['anexos_json'],
                       data['main_group'], data['company']]
            ws.append_row(new_row, value_input_option='USER_ENTERED') # pyright: ignore[reportArgumentType]
            return True, "Ocorrência de equipamento registrada com sucesso."
        except Exception as e:
            return False, f"Erro ao registrar: {e}"

    def register_full_occurrence(self, data):
        """Registra uma ocorrência de chamada detalhada na planilha."""
        ws = self._get_worksheet(self.CALLS_SHEET)
        if not ws: return False, "Falha ao acessar a planilha."
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_ids = [rec.get('id') for rec in self._get_all_records_safe(ws) if rec.get('id')]
            new_id = f"CALL-{len(current_ids) + 1:04d}"
            new_row = [new_id, now, data['title'], data['user_email'], data['user_name'], data['user_username'],
                       data['status'], data['op_a'], data['op_b'], data['testes_json'], data['description'],
                       data['main_group'], data['company']]
            ws.append_row(new_row, value_input_option='USER_ENTERED') # pyright: ignore[reportArgumentType]
            return True, "Ocorrência detalhada registrada com sucesso."
        except Exception as e:
            return False, f"Erro ao registrar: {e}"

    # --- Usuários ---
    def check_user_status(self, email):
        """Busca o perfil de um usuário específico pelo e-mail."""
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return {'status': 'error'}
        try:
            records = self._get_all_records_safe(ws)
            for user_rec in records:
                if str(user_rec.get("email", "")).strip().lower() == str(email).strip().lower():
                    return user_rec
        except Exception as e:
            print(f"Erro ao ler planilha de usuários: {e}")
            return {'status': 'error'}
        return {'status': 'unregistered'}

    def get_all_users(self):
        """Busca todos os usuários da planilha."""
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return []
        return [rec for rec in self._get_all_records_safe(ws) if rec.get("email")]

    def request_access(self, email, full_name, username, main_group, sub_group, company_name=None):
        """Adiciona uma nova solicitação de acesso à planilha."""
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return False, "Falha ao acessar a planilha."
        try:
            all_emails = [str(rec.get('email', '')).strip().lower() for rec in self._get_all_records_safe(ws)]
            if str(email).strip().lower() in all_emails:
                return False, "Solicitação já existe para este e-mail."
            
            new_row = [email, full_name, username, main_group, sub_group, "pending", company_name or ""]
            ws.append_row(new_row, value_input_option='USER_ENTERED') # pyright: ignore[reportArgumentType]
            return True, "Solicitação de acesso enviada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao enviar a solicitação: {e}"
            
    # --- Operações em Lote e Outras ---
    def get_pending_requests(self):
        """
        Obtém todas as solicitações de acesso de usuários com status 'pending'.
        """
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return []
        all_users = self._get_all_records_safe(ws)
        return [user for user in all_users if str(user.get("status", "")).strip().lower() == "pending"]
