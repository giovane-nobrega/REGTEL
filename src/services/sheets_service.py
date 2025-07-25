from datetime import datetime
import random
import json
import csv
from googleapiclient.http import MediaFileUpload
import os
# Importa o auth_service para poder usar a função get_drive_service
from services import auth_service

# --- BANCO DE DADOS SIMULADO ---

_users_db = [
    {"email": "giovane67telecom@gmail.com", "name": "GIOVANI FERREIRA", "username": "gferreira", "role": "admin", "status": "approved"},
    {"email": "parceiro@exemplo.com", "name": "PARCEIRO EXEMPLO", "username": "parceiro", "role": "partner", "company": "M2 TELECOMUNICAÇÕES", "status": "approved"},
    {"email": "joao.silva@prefeitura.example.com", "name": "JOÃO DA SILVA", "username": "jsilva", "role": "prefeitura", "status": "approved"},
    {"email": "maria.santos@prefeitura.example.com", "name": "MARIA SANTOS", "username": "msantos", "role": "prefeitura", "status": "pending"},
    {"email": "pedro.costa@gmail.com", "name": "PEDRO COSTA", "username": "pcosta", "role": "partner", "company": "MDA FIBRA", "status": "pending"},
    {"email": "parceiro67@exemplo.com", "name": "PARCEIRO 67 INTERNET", "username": "parceiro67", "role": "partner", "company": "67 INTERNET", "status": "approved"},
    {"email": "user67@exemplo.com", "name": "USUÁRIO 67 TELECOM", "username": "user67", "role": "telecom_user", "status": "approved"},
]

_call_occurrences_db = [
    {'ID': 'CALL-001', 'Data de Registro': '2025-06-30 15:00:12', 'Título da Ocorrência': 'CHIADO EM LIGAÇÕES PARA VIVO (EXEMPLO)', 'Email do Registrador': 'parceiro@exemplo.com', 'Nome do Registrador': 'PARCEIRO EXEMPLO', 'Username do Registrador': 'parceiro', 'Status': 'RESOLVIDO', 'Operadora A': 'VIVO FIXO', 'Operadora B': 'CLARO FIXO', 'Testes': '[{"horario": "15:00", "num_a": "67999991111", "op_a": "VIVO", "num_b": "6734212222", "op_b": "OI", "status": "CHIADO", "obs": "TESTE 1"}]', 'Anexos': '[]'}, 
    {'ID': 'CALL-002', 'Data de Registro': '2025-07-01 09:05:45', 'Título da Ocorrência': 'CHAMADAS MUDAS PARA TIM (EXEMPLO)', 'Email do Registrador': 'parceiro@exemplo.com', 'Nome do Registrador': 'PARCEIRO EXEMPLO', 'Username do Registrador': 'parceiro', 'Status': 'EM ANÁLISE', 'Operadora A': 'OUTRA', 'Operadora B': 'TIM', 'Testes': '[]', 'Anexos': '[]'},
    {'ID': 'CALL-003', 'Data de Registro': '2025-07-02 10:00:00', 'Título da Ocorrência': 'CHAMADA DE (67) 99999-1111 PARA (67) 3421-2222', 'Email do Registrador': 'joao.silva@prefeitura.example.com', 'Nome do Registrador': 'JOÃO DA SILVA', 'Username do Registrador': 'jsilva', 'Status': 'REGISTRADO', 'Operadora A': 'VIVO FIXO', 'Operadora B': 'OI FIXO', 'Testes': '[]', 'Anexos': '[]'}
]

_equipment_occurrences_db = [{'ID': 'EQUIP-001', 'Data de Registro': '2025-07-01 11:30:00', 'Tipo de Equipamento': 'TELEFONE IP', 'Email do Registrador': 'joao.silva@prefeitura.example.com', 'Nome do Registrador': 'JOÃO DA SILVA', 'Username do Registrador': 'jsilva', 'Status': 'REGISTRADO', 'Anexos': '[]'}]

# --- FUNÇÕES DE SERVIÇO ---

def _get_user_info(user_email):
    """Função auxiliar para encontrar o nome e username de um utilizador."""
    for user in _users_db:
        if user["email"] == user_email:
            return user.get("name", "N/A"), user.get("username", "N/A")
    return "N/A", "N/A"

def _upload_files_to_drive(credentials, file_paths):
    if not file_paths:
        return True, [] # Sucesso, nenhuma ação necessária

    drive_service = auth_service.get_drive_service(credentials)
    if not drive_service:
        return False, "Não foi possível obter o serviço do Google Drive."

    try:
        folder_id = None
        q = "mimeType='application/vnd.google-apps.folder' and name='Craft Quest Anexos' and trashed=false"
        response = drive_service.files().list(q=q, spaces='drive', fields='files(id, name)').execute()
        if not response.get('files'):
            folder_metadata = {'name': 'Craft Quest Anexos', 'mimeType': 'application/vnd.google-apps.folder'}
            folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')
        else:
            folder_id = response.get('files')[0].get('id')

        uploaded_file_links = []
        for file_path in file_paths:
            file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
            media = MediaFileUpload(file_path, resumable=True)
            file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
            
            drive_service.permissions().create(fileId=file.get('id'), body={'role': 'reader', 'type': 'anyone'}).execute()
            
            uploaded_file_links.append(file.get('webViewLink'))
        
        return True, uploaded_file_links

    except Exception as e:
        error_message = f"Ocorreu um erro durante o upload para o Google Drive:\n\n{e}\n\nVerifique se a API do Google Drive está ativa no seu projeto e se autorizou o acesso."
        print(error_message)
        return False, error_message

def register_equipment_occurrence(credentials, user_email, data, attachment_paths):
    upload_success, result = _upload_files_to_drive(credentials, attachment_paths)
    
    if not upload_success:
        return False, result

    attachment_links = result
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_id = f"EQUIP-{len(_equipment_occurrences_db) + 1:03d}"
    user_name, user_username = _get_user_info(user_email)
    
    new_occurrence = {
        'ID': new_id,
        'Data de Registro': now,
        'Email do Registrador': user_email,
        'Nome do Registrador': user_name,
        'Username do Registrador': user_username,
        'Status': 'REGISTRADO',
        'Tipo de Equipamento': data.get('tipo'),
        'Marca/Modelo': data.get('modelo'),
        'Identificação (Nº Série)': data.get('serial'),
        'Localização': data.get('localizacao'),
        'Descrição do Problema': data.get('descricao'),
        'Anexos': json.dumps(attachment_links)
    }
    _equipment_occurrences_db.append(new_occurrence)
    return True, "Ocorrência de equipamento registrada com sucesso."

def register_simple_call_occurrence(user_email, data):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_id = f"CALL-{len(_call_occurrences_db) + 1:03d}"
    user_name, user_username = _get_user_info(user_email)
    title = f"CHAMADA DE {data.get('origem')} PARA {data.get('destino')}"

    new_occurrence = {
        'ID': new_id,
        'Data de Registro': now,
        'Título da Ocorrência': title,
        'Email do Registrador': user_email,
        'Nome do Registrador': user_name,
        'Username do Registrador': user_username,
        'Status': 'REGISTRADO',
        'Descrição do Problema': data.get('descricao'),
        'Testes': '[]',
        'Anexos': '[]'
    }
    _call_occurrences_db.append(new_occurrence)
    return True, "Ocorrência de chamada registrada com sucesso."

def register_full_occurrence(user_email, title, testes):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_id = f"CALL-{len(_call_occurrences_db) + 1:03d}"
    user_name, user_username = _get_user_info(user_email)
    op_a = testes[0]['op_a'] if testes else 'N/A'
    op_b = testes[0]['op_b'] if testes else 'N/A'
    testes_json = json.dumps(testes)
    
    new_occurrence = {
        'ID': new_id,
        'Data de Registro': now,
        'Título da Ocorrência': title,
        'Email do Registrador': user_email,
        'Nome do Registrador': user_name,
        'Username do Registrador': user_username,
        'Status': 'REGISTRADO',
        'Operadora A': op_a,
        'Operadora B': op_b,
        'Testes': testes_json,
        'Anexos': '[]'
    }
    _call_occurrences_db.append(new_occurrence)
    return True, "Ocorrência detalhada registrada com sucesso."

def get_occurrence_by_id(occurrence_id):
    all_occurrences = _call_occurrences_db + _equipment_occurrences_db
    for occ in all_occurrences:
        if occ.get('ID') == occurrence_id:
            return occ
    return None

def write_to_csv(data_list, file_path):
    if not data_list:
        return False, "A lista de dados está vazia."
    headers = [
        'ID', 'Data de Registro', 'Título da Ocorrência', 'Email do Registrador', 
        'Nome do Registrador', 'Username do Registrador', 'Status', 
        'Operadora A', 'Operadora B', 'Testes', 'Tipo de Equipamento', 
        'Marca/Modelo', 'Identificação (Nº Série)', 'Localização', 'Descrição do Problema', 'Anexos'
    ]
    try:
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data_list)
        return True, f"Relatório salvo com sucesso em:\n{file_path}"
    except (IOError, Exception) as e:
        return False, f"Ocorreu um erro ao salvar o ficheiro: {e}"

def get_all_operators():
    operators = set()
    for occ in _call_occurrences_db:
        if occ.get('Operadora A'): operators.add(occ['Operadora A'])
        if occ.get('Operadora B'): operators.add(occ['Operadora B'])
    default_operators = ["VIVO FIXO", "CLARO FIXO", "OI FIXO", "TIM", "EMBRATEL", "ALGAR TELECOM", "OUTRA"]
    operators.update(default_operators)
    return sorted(list(operators))

def get_all_partner_companies():
    companies = set(user['company'] for user in _users_db if user.get('role') == 'partner' and user.get('company'))
    return sorted(list(companies))

def check_user_status(email):
    for user in _users_db:
        if user["email"] == email: return user
    return {"status": "unregistered", "role": None}

def request_access(email, full_name, username, role_name, company_name=None):
    role_map = {"Parceiro": "partner", "Prefeitura": "prefeitura", "Colaboradores 67": "telecom_user"}
    role = role_map.get(role_name, "unknown")
    for user in _users_db:
        if user["email"] == email: return
    
    new_user = {"email": email, "name": full_name, "username": username, "role": role, "status": "pending"}
    if role == "partner" and company_name:
        new_user["company"] = company_name
        
    _users_db.append(new_user)

def get_pending_requests(): return [user for user in _users_db if user["status"] == "pending"]

def update_user_status(email, new_status):
    for user in _users_db:
        if user["email"] == email:
            user["status"] = new_status
            return

def get_all_users():
    return _users_db

def update_user_role(email, new_role):
    for user in _users_db:
        if user["email"] == email:
            user["role"] = new_role
            return

def update_occurrence_status(occurrence_id, new_status):
    all_occurrences = _call_occurrences_db + _equipment_occurrences_db
    for occ in all_occurrences:
        if occ.get('ID') == occurrence_id:
            if occ['Status'] != new_status:
                occ['Status'] = new_status
                return True
    return False

def get_occurrences_by_user(credentials, user_email, search_term=None):
    user_profile = check_user_status(user_email)
    user_role = user_profile.get("role")
    
    user_occurrences = []
    all_occurrences = _call_occurrences_db + _equipment_occurrences_db

    if user_role == 'telecom_user':
        telecom_user_emails = {u['email'] for u in _users_db if u.get('role') == 'telecom_user'}
        user_occurrences = [occ for occ in all_occurrences if occ.get("Email do Registrador") in telecom_user_emails]
    else:
        user_occurrences = [occ for occ in all_occurrences if occ.get("Email do Registrador") == user_email]

    if search_term:
        term = search_term.lower()
        filtered_list = []
        for occ in user_occurrences:
            if (term in occ.get('ID', '').lower() or
                term in occ.get('Título da Ocorrência', '').lower() or
                term in occ.get('Tipo de Equipamento', '').lower() or
                term in occ.get('Data de Registro', '').lower()):
                filtered_list.append(occ)
        return filtered_list
    return sorted(user_occurrences, key=lambda x: x['Data de Registro'], reverse=True)

def get_all_occurrences_for_admin(status_filter=None, role_filter=None, search_term=None):
    all_occurrences = _call_occurrences_db + _equipment_occurrences_db
    if status_filter and status_filter != "Todos":
        all_occurrences = [occ for occ in all_occurrences if occ.get('Status') == status_filter]
    
    if role_filter and role_filter != "Todos":
        email_to_user_details = {user['email']: user for user in _users_db}
        
        valid_roles = ["partner", "prefeitura", "telecom_user"]
        if role_filter in valid_roles:
            all_occurrences = [
                occ for occ in all_occurrences 
                if email_to_user_details.get(occ.get('Email do Registrador'), {}).get('role') == role_filter
            ]
        else:
            all_occurrences = [
                occ for occ in all_occurrences 
                if email_to_user_details.get(occ.get('Email do Registrador'), {}).get('company') == role_filter
            ]

    if search_term:
        term = search_term.lower()
        filtered_list = []
        for occ in all_occurrences:
            if (term in occ.get('ID', '').lower() or
                term in occ.get('Título da Ocorrência', '').lower() or
                term in occ.get('Tipo de Equipamento', '').lower() or
                term in occ.get('Data de Registro', '').lower() or
                term in occ.get('Email do Registrador', '').lower()):
                filtered_list.append(occ)
        return filtered_list
    return sorted(all_occurrences, key=lambda x: x['Data de Registro'], reverse=True)
