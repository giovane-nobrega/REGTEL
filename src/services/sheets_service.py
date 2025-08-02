# ==============================================================================
# FICHEIRO: src/services/sheets_service.py
# DESCRIÇÃO: Lida com todas as operações de leitura e escrita na planilha
#            Google Sheets, que funciona como a base de dados da aplicação.
# ==============================================================================

import gspread
import json
import csv
from datetime import datetime
from googleapiclient.http import MediaFileUpload
import os
from tkinter import messagebox

class SheetsService:
    """Lida com todas as operações de leitura e escrita na planilha Google Sheets."""
    def __init__(self, auth_service_instance):
        self.auth_service = auth_service_instance
        # SUBSTITUA PELO ID DA SUA PLANILHA
        self.SPREADSHEET_ID = "1ymzB0QiZiuTnLk9h3qfFnZgcxkTKJUeT-3rn4bYqtQA" 
        self.USERS_SHEET = "users"
        self.CALLS_SHEET = "call_occurrences"
        self.EQUIPMENT_SHEET = "equipment_occurrences"

        self._SERVICE_CREDENTIALS = self.auth_service.get_service_account_credentials()
        self._GC = None
        self._SPREADSHEET = None

        if self._SERVICE_CREDENTIALS:
            try:
                # Autentica a conta de serviço
                self._GC = gspread.service_account(filename=self.auth_service.SERVICE_ACCOUNT_FILE)
                # Abre a planilha pelo ID
                self._SPREADSHEET = self._GC.open_by_key(self.SPREADSHEET_ID)
            except gspread.exceptions.SpreadsheetNotFound:
                 messagebox.showerror("Erro de Acesso", "Planilha não encontrada. Verifique o SPREADSHEET_ID e as permissões da conta de serviço.")
            except Exception as e:
                 messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao Google Sheets: {e}")

    def _get_worksheet(self, sheet_name):
        """Função auxiliar para obter uma aba específica da planilha."""
        if not self._SPREADSHEET:
            print("ERRO: A conexão com a planilha não foi estabelecida.")
            return None
        try:
            return self._SPREADSHEET.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            print(f"ERRO: A aba '{sheet_name}' não foi encontrada na planilha.")
            return None
        except Exception as e:
            print(f"ERRO ao obter a aba '{sheet_name}': {e}")
            return None

    def _get_user_info(self, user_email):
        """Busca o nome e username de um usuário a partir do seu e-mail."""
        user_profile = self.check_user_status(user_email)
        if user_profile and user_profile.get('status') != 'unregistered':
            return user_profile.get("name", "N/A"), user_profile.get("username", "N/A")
        return "N/A", "N/A"

    def check_user_status(self, email):
        """Verifica o status de um usuário na planilha."""
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return {"status": "error"}
        try:
            records = ws.get_all_records()
            for user in records:
                if user.get("email") == email: return user
        except Exception as e:
            print(f"Erro ao ler a planilha de usuários: {e}")
            return {"status": "error"}
        return {"status": "unregistered"}

    def request_access(self, email, full_name, username, main_group, sub_group, company_name=None):
        """Adiciona uma nova linha na planilha para uma solicitação de acesso."""
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return False, "Não foi possível aceder à planilha."
        try:
            if ws.find(email): return False, "Solicitação já existe para este e-mail."
        except gspread.exceptions.CellNotFound: pass
        new_row = [email, full_name, username, main_group, sub_group, "pending", company_name or ""]
        ws.append_row(new_row, value_input_option='USER_ENTERED')
        return True, "Solicitação de acesso enviada com sucesso."

    def get_pending_requests(self):
        """Retorna uma lista de todos os usuários com status 'pending'."""
        ws = self._get_worksheet(self.USERS_SHEET)
        return [user for user in ws.get_all_records() if user.get("status") == "pending"] if ws else []

    def update_user_status(self, email, new_status):
        """Atualiza o status de um usuário (ex: para 'approved' ou 'rejected')."""
        ws = self._get_worksheet(self.USERS_SHEET)
        if not ws: return
        try:
            cell = ws.find(email, in_column=1)
            if cell: ws.update_cell(cell.row, 6, new_status) # Coluna 6 para 'status'
        except gspread.exceptions.CellNotFound: print(f"Usuário {email} não encontrado.")

    def get_all_users(self):
        """Retorna uma lista de todos os usuários registrados."""
        ws = self._get_worksheet(self.USERS_SHEET)
        return ws.get_all_records() if ws else []

    def update_user_profile(self, email, new_main_group, new_sub_group, new_company=None):
        """Atualiza o perfil completo de um usuário."""
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

    def get_all_occurrences(self, search_term=None):
        """Busca todas as ocorrências de todas as abas."""
        calls_ws = self._get_worksheet(self.CALLS_SHEET)
        equip_ws = self._get_worksheet(self.EQUIPMENT_SHEET)
        all_occurrences = []
        if calls_ws: all_occurrences.extend(calls_ws.get_all_records())
        if equip_ws: all_occurrences.extend(equip_ws.get_all_records())
        if search_term:
            term = str(search_term).lower()
            all_occurrences = [occ for occ in all_occurrences if any(term in str(v).lower() for v in occ.values())]
        return sorted(all_occurrences, key=lambda x: x.get('Data de Registro', ''), reverse=True)

    def get_occurrences_by_user(self, user_email, search_term=None):
        """Busca ocorrências com base nas permissões do perfil do usuário."""
        user_profile = self.check_user_status(user_email)
        if not user_profile: return []

        main_group = user_profile.get("main_group")
        sub_group = user_profile.get("sub_group")
        user_company = user_profile.get("company", "").strip().upper() if user_profile.get("company") else None

        all_occurrences = self.get_all_occurrences(search_term=search_term)
        
        # Super Admins e Admins veem tudo
        if main_group == '67_TELECOM' and sub_group in ['SUPER_ADMIN', 'ADMIN']:
            return all_occurrences

        all_users = self.get_all_users()
        email_to_details_map = {u['email']: u for u in all_users}

        # Gerentes veem ocorrências internas e de parceiros
        if main_group == '67_TELECOM' and sub_group == 'MANAGER':
            return [occ for occ in all_occurrences if email_to_details_map.get(occ.get('Email do Registrador'), {}).get('main_group') in ['67_TELECOM', 'PARTNER']]
            
        # Usuários comuns da 67_TELECOM veem apenas as do seu grupo
        if main_group == '67_TELECOM' and sub_group == 'USER':
            return [occ for occ in all_occurrences if email_to_details_map.get(occ.get('Email do Registrador'), {}).get('main_group') == '67_TELECOM']

        # Parceiros e Prefeitura veem apenas as da sua empresa/departamento
        if main_group in ['PARTNER', 'PREFEITURA']:
            if not user_company: return []
            return [occ for occ in all_occurrences if email_to_details_map.get(occ.get('Email do Registrador'), {}).get('company', '').strip().upper() == user_company]

        return []

    def get_occurrence_by_id(self, occurrence_id):
        """Busca uma ocorrência específica pelo seu ID."""
        for occ in self.get_all_occurrences():
            if str(occ.get('ID')) == str(occurrence_id): return occ
        return None

    def update_occurrence_status(self, occurrence_id, new_status):
        """Atualiza o status de uma ocorrência."""
        sheet_name = self.CALLS_SHEET if 'CALL' in occurrence_id else self.EQUIPMENT_SHEET
        ws = self._get_worksheet(sheet_name)
        if not ws: return
        try:
            cell = ws.find(occurrence_id, in_column=1)
            # Define a coluna de status correta para cada tipo de ocorrência
            status_col = 7
            if 'EQUIP' in occurrence_id:
                status_col = 6
            if cell: ws.update_cell(cell.row, status_col, new_status)
        except gspread.exceptions.CellNotFound: print(f"Ocorrência {occurrence_id} não encontrada.")

    def get_all_operators(self):
        """Retorna uma lista única e ordenada de todas as operadoras já registradas."""
        ws = self._get_worksheet(self.CALLS_SHEET)
        if not ws: return ["VIVO", "TIM", "CLARO", "OI"]
        records = ws.get_all_records()
        operators = {rec[key] for rec in records for key in ['Operadora A', 'Operadora B'] if rec.get(key)}
        operators.update(["VIVO FIXO", "CLARO FIXO", "OI FIXO", "TIM", "EMBRATEL", "ALGAR TELECOM", "OUTRA"])
        return sorted(list(operators))

    def _upload_files_to_drive(self, user_credentials, file_paths):
        """Faz o upload de ficheiros para a pasta 'Craft Quest Anexos' no Drive do usuário."""
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
                folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
                folder_id = folder.get('id')

            uploaded_file_links = []
            for file_path in file_paths:
                file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
                media = MediaFileUpload(file_path, resumable=True)
                file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
                # Torna o ficheiro visível para qualquer pessoa com o link
                drive_service.permissions().create(fileId=file.get('id'), body={'role': 'reader', 'type': 'anyone'}).execute()
                uploaded_file_links.append(file.get('webViewLink'))
            return True, uploaded_file_links
        except Exception as e:
            return False, f"Ocorreu um erro durante o upload para o Google Drive: {e}"

    def register_simple_call_occurrence(self, user_email, data):
        """Registra uma ocorrência de chamada simplificada."""
        ws = self._get_worksheet(self.CALLS_SHEET)
        if not ws: return False, "Falha ao aceder à planilha de chamadas."
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_id = f"CALL-{len(ws.get_all_records()) + 1:04d}"
            user_name, user_username = self._get_user_info(user_email)
            title = f"CHAMADA DE {data.get('origem')} PARA {data.get('destino')}"
            
            # Estrutura da linha para a planilha 'call_occurrences'
            new_row = [
                new_id, now, title, user_email, user_name, user_username, 
                'REGISTRADO', "", "", "[]", data.get('descricao'), "[]"
            ]
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Ocorrência registrada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao registrar a ocorrência: {e}"

    def register_equipment_occurrence(self, user_credentials, user_email, data, attachment_paths):
        """Registra uma ocorrência de equipamento, incluindo upload de ficheiros."""
        ws = self._get_worksheet(self.EQUIPMENT_SHEET)
        if not ws: return False, "Falha ao aceder à planilha de equipamentos."
        
        upload_success, result = self._upload_files_to_drive(user_credentials, attachment_paths)
        if not upload_success:
            return False, result
        
        attachment_links_json = json.dumps(result)
        
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_id = f"EQUIP-{len(ws.get_all_records()) + 1:04d}"
            user_name, user_username = self._get_user_info(user_email)

            # Estrutura da linha para a planilha 'equipment_occurrences'
            new_row = [
                new_id, now, user_email, user_name, user_username, 'REGISTRADO',
                data.get('tipo'), data.get('modelo'), data.get('ramal'),
                data.get('localizacao'), data.get('descricao'), attachment_links_json
            ]
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Ocorrência registrada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao registrar a ocorrência de equipamento: {e}"

    def register_full_occurrence(self, user_email, title, testes):
        """Registra uma ocorrência de chamada detalhada."""
        ws = self._get_worksheet(self.CALLS_SHEET)
        if not ws: return False, "Falha ao aceder à planilha de chamadas."
        
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_id = f"CALL-{len(ws.get_all_records()) + 1:04d}"
            user_name, user_username = self._get_user_info(user_email)
            
            op_a = testes[0]['op_a'] if testes else 'N/A'
            op_b = testes[0]['op_b'] if testes else 'N/A'
            description = testes[0]['obs'] if testes else ""
            testes_json = json.dumps(testes)

            # Estrutura da linha para a planilha 'call_occurrences'
            new_row = [
                new_id, now, title, user_email, user_name, user_username, 
                'REGISTRADO', op_a, op_b, testes_json, description, "[]"
            ]
            ws.append_row(new_row, value_input_option='USER_ENTERED')
            return True, "Ocorrência detalhada registrada com sucesso."
        except Exception as e:
            return False, f"Ocorreu um erro ao registrar a ocorrência detalhada: {e}"
