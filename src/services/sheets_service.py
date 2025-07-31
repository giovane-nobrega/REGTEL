import gspread
import json
import csv
from datetime import datetime
from googleapiclient.http import MediaFileUpload
import os
import traceback
from services import auth_service

# ==============================================================================
# --- CONFIGURAÇÃO E AUTENTICAÇÃO INICIAL ---
# ==============================================================================
SPREADSHEET_ID = "1ymzB0QiZiuTnLk9h3qfFnZgcxkTKJUeT-3rn4bYqtQA"
USERS_SHEET = "users"
CALLS_SHEET = "call_occurrences"
EQUIPMENT_SHEET = "equipment_occurrences"

_SERVICE_CREDENTIALS = auth_service.get_service_account_credentials()
_GC = gspread.service_account(filename=auth_service.SERVICE_ACCOUNT_FILE, scopes=auth_service.SCOPES_SERVICE_ACCOUNT) if _SERVICE_CREDENTIALS else None
_SPREADSHEET = _GC.open_by_key(SPREADSHEET_ID) if _GC else None

# ==============================================================================
# --- FUNÇÕES AUXILIARES ---
# ==============================================================================

def _get_worksheet(sheet_name):
    if not _SPREADSHEET:
        print("ERRO: A conexão com a planilha não foi estabelecida.")
        return None
    try:
        return _SPREADSHEET.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"ERRO: A aba '{sheet_name}' não foi encontrada na planilha.")
        return None
    except Exception as e:
        print(f"ERRO ao obter a aba '{sheet_name}': {e}")
        return None

def _get_user_info(user_email):
    user_profile = check_user_status(user_email)
    if user_profile:
        return user_profile.get("name", "N/A"), user_profile.get("username", "N/A")
    return "N/A", "N/A"

def _upload_files_to_drive(user_credentials, file_paths):
    if not file_paths: return True, []
    drive_service = auth_service.get_drive_service(user_credentials)
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
# --- FUNÇÕES DE SERVIÇO (USANDO A CONTA DE SERVIÇO) ---
# ==============================================================================

def check_user_status(email):
    ws = _get_worksheet(USERS_SHEET)
    if not ws: return {"status": "error", "role": None}
    for user in ws.get_all_records():
        if user.get("email") == email: return user
    return {"status": "unregistered", "role": None}

def request_access(email, full_name, username, role, company_name=None):
    ws = _get_worksheet(USERS_SHEET)
    if not ws: return False, "Não foi possível aceder à planilha."
    try:
        if ws.find(email): return False, "Solicitação já existe para este e-mail."
    except gspread.exceptions.CellNotFound: pass
    new_row = [email, full_name, username, role, "pending", company_name or ""]
    ws.append_row(new_row, value_input_option='USER_ENTERED')
    return True, "Solicitação de acesso enviada com sucesso."

def get_pending_requests():
    ws = _get_worksheet(USERS_SHEET)
    return [user for user in ws.get_all_records() if user.get("status") == "pending"] if ws else []

def update_user_status(email, new_status):
    ws = _get_worksheet(USERS_SHEET)
    if not ws: return
    try:
        cell = ws.find(email, in_column=1)
        if cell: ws.update_cell(cell.row, 5, new_status)
    except gspread.exceptions.CellNotFound: print(f"Usuário {email} não encontrado.")

def get_all_users():
    ws = _get_worksheet(USERS_SHEET)
    return ws.get_all_records() if ws else []

def update_user_profile(email, new_role, new_company=None):
    ws = _get_worksheet(USERS_SHEET)
    if not ws: return
    try:
        cell = ws.find(email, in_column=1)
        if cell:
            ws.update_cell(cell.row, 4, new_role)
            company_to_save = new_company if new_role == 'partner' else ""
            ws.update_cell(cell.row, 6, company_to_save)
    except gspread.exceptions.CellNotFound:
        print(f"Usuário {email} não encontrado.")

def register_simple_call_occurrence(user_email, data):
    ws = _get_worksheet(CALLS_SHEET)
    if not ws: return False, "Falha ao aceder à planilha."
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_id = f"CALL-{len(ws.get_all_records()) + 1:04d}"
    user_name, user_username = _get_user_info(user_email)
    title = f"CHAMADA DE {data.get('origem')} PARA {data.get('destino')}"
    new_row = [new_id, now, title, user_email, user_name, user_username, 'REGISTRADO', "", "", "[]", data.get('descricao'), "[]"]
    ws.append_row(new_row, value_input_option='USER_ENTERED')
    return True, "Ocorrência registrada com sucesso."

def register_equipment_occurrence(user_credentials, user_email, data, attachment_paths):
    ws = _get_worksheet(EQUIPMENT_SHEET)
    if not ws: return False, "Falha ao aceder à planilha."
    upload_success, result = _upload_files_to_drive(user_credentials, attachment_paths)
    if not upload_success: return False, result
    attachment_links_json = json.dumps(result)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_id = f"EQUIP-{len(ws.get_all_records()) + 1:04d}"
    user_name, user_username = _get_user_info(user_email)
    new_row = [new_id, now, user_email, user_name, user_username, 'REGISTRADO', data.get('tipo'), data.get('modelo'), data.get('ramal'), data.get('localizacao'), data.get('descricao'), attachment_links_json]
    ws.append_row(new_row, value_input_option='USER_ENTERED')
    return True, "Ocorrência registrada com sucesso."

def register_full_occurrence(user_email, title, testes):
    ws = _get_worksheet(CALLS_SHEET)
    if not ws: return False, "Falha ao aceder à planilha."
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_id = f"CALL-{len(ws.get_all_records()) + 1:04d}"
    user_name, user_username = _get_user_info(user_email)
    op_a = testes[0]['op_a'] if testes else 'N/A'
    op_b = testes[0]['op_b'] if testes else 'N/A'
    description = testes[0]['obs'] if testes else ""
    testes_json = json.dumps(testes)
    new_row = [new_id, now, title, user_email, user_name, user_username, 'REGISTRADO', op_a, op_b, testes_json, description, "[]"]
    ws.append_row(new_row, value_input_option='USER_ENTERED')
    return True, "Ocorrência detalhada registrada com sucesso."

def get_all_occurrences(status_filter=None, role_filter=None, search_term=None):
    calls_ws = _get_worksheet(CALLS_SHEET)
    equip_ws = _get_worksheet(EQUIPMENT_SHEET)
    all_occurrences = []
    if calls_ws: all_occurrences.extend(calls_ws.get_all_records())
    if equip_ws: all_occurrences.extend(equip_ws.get_all_records())
    if status_filter and status_filter != "Todos":
        all_occurrences = [occ for occ in all_occurrences if occ.get('Status') == status_filter]
    if role_filter and role_filter != "Todos":
        users_data = get_all_users()
        email_to_user_details = {user['email']: user for user in users_data}
        if role_filter in ["partner", "prefeitura", "telecom_user"]:
            all_occurrences = [occ for occ in all_occurrences if email_to_user_details.get(occ.get('Email do Registrador'), {}).get('role') == role_filter]
        else:
            all_occurrences = [occ for occ in all_occurrences if email_to_user_details.get(occ.get('Email do Registrador'), {}).get('company') == role_filter]
    if search_term:
        term = str(search_term).lower()
        all_occurrences = [occ for occ in all_occurrences if any(term in str(v).lower() for v in occ.values())]
    return sorted(all_occurrences, key=lambda x: x.get('Data de Registro', ''), reverse=True)

# --- ALTERAÇÃO AQUI: Lógica de filtragem do histórico reescrita para maior robustez ---
def get_occurrences_by_user(user_email, search_term=None):
    user_profile = check_user_status(user_email)
    if not user_profile:
        return []

    user_role = user_profile.get("role")
    # Limpa os dados da empresa para garantir uma comparação fiável
    user_company = user_profile.get("company", "").strip().upper() if user_profile.get("company") else None

    all_occurrences = get_all_occurrences(search_term=search_term)
    all_users = get_all_users()
    user_occurrences = []

    if user_role in ['admin', 'telecom_user']:
        return sorted(all_occurrences, key=lambda x: x.get('Data de Registro', ''), reverse=True)
    
    elif user_role == 'prefeitura':
        prefeitura_user_emails = {u['email'] for u in all_users if u.get('role') == 'prefeitura'}
        user_occurrences = [occ for occ in all_occurrences if occ.get("Email do Registrador") in prefeitura_user_emails]

    elif user_role == 'partner':
        if user_company:
            # Compara os nomes das empresas de forma insensível a maiúsculas/minúsculas e espaços
            company_user_emails = {
                u['email'] for u in all_users 
                if u.get('company') and u.get('company').strip().upper() == user_company
            }
            for occ in all_occurrences:
                if 'CALL' in occ.get('ID', '') and occ.get("Email do Registrador") in company_user_emails:
                    user_occurrences.append(occ)
    else:
        user_occurrences = [occ for occ in all_occurrences if occ.get("Email do Registrador") == user_email]

    return sorted(user_occurrences, key=lambda x: x.get('Data de Registro', ''), reverse=True)
# --- FIM DA ALTERAÇÃO ---

def get_occurrence_by_id(occurrence_id):
    for occ in get_all_occurrences():
        if str(occ.get('ID')) == str(occurrence_id): return occ
    return None

def update_occurrence_status(occurrence_id, new_status):
    sheet_name = CALLS_SHEET if 'CALL' in occurrence_id else EQUIPMENT_SHEET
    ws = _get_worksheet(sheet_name)
    if not ws: return
    try:
        cell = ws.find(occurrence_id, in_column=1)
        if cell: ws.update_cell(cell.row, 7, new_status)
    except gspread.exceptions.CellNotFound: print(f"Ocorrência {occurrence_id} não encontrada.")

def get_all_operators():
    ws = _get_worksheet(CALLS_SHEET)
    if not ws: return ["VIVO", "TIM", "CLARO", "OI"]
    records = ws.get_all_records()
    operators = {rec[key] for rec in records for key in ['Operadora A', 'Operadora B'] if rec.get(key)}
    operators.update(["VIVO FIXO", "CLARO FIXO", "OI FIXO", "TIM", "EMBRATEL", "ALGAR TELECOM", "OUTRA"])
    return sorted(list(operators))

def get_all_partner_companies():
    return sorted([
        "M2 TELECOMUNICAÇÕES", 
        "MDA FIBRA", 
        "DISK SISTEMA TELECOM", 
        "GMN TELECOM", 
        "67 INTERNET"
    ])

def write_to_csv(data_list, file_path):
    if not data_list: return False, "A lista de dados está vazia."
    try:
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=list(data_list[0].keys()), extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data_list)
        return True, f"Relatório salvo com sucesso em:\n{file_path}"
    except (IOError, Exception) as e:
        return False, f"Ocorreu um erro ao salvar o ficheiro: {e}"
