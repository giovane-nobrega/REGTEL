from datetime import datetime
import random
import json

# --- BANCO DE DADOS SIMULADO ---

_users_db = [
    {"email": "giovane67telecom@gmail.com", "name": "GIOVANI FERREIRA", "username": "gferreira", "role": "admin", "status": "approved"},
    {"email": "parceiro@exemplo.com", "name": "PARCEIRO EXEMPLO", "username": "parceiro", "role": "partner", "status": "approved"},
    {"email": "joao.silva@prefeitura.example.com", "name": "JOÃO DA SILVA", "username": "jsilva", "role": "prefeitura", "status": "approved"},
    {"email": "maria.santos@prefeitura.example.com", "name": "MARIA SANTOS", "username": "msantos", "role": "prefeitura", "status": "pending"},
    {"email": "pedro.costa@gmail.com", "name": "PEDRO COSTA", "username": "pcosta", "role": "partner", "status": "pending"},
]

_call_occurrences_db = [
    {'ID': 'CALL-001', 'Data de Registro': '2025-06-30 15:00:12', 'Título da Ocorrência': 'CHIADO EM LIGAÇÕES PARA VIVO (EXEMPLO)', 'Email do Registrador': 'parceiro@exemplo.com', 'Status': 'Resolvido', 'Operadora A': 'VIVO FIXO', 'Operadora B': 'CLARO FIXO', 'Testes': '[]'}, 
    {'ID': 'CALL-002', 'Data de Registro': '2025-07-01 09:05:45', 'Título da Ocorrência': 'CHAMADAS MUDAS PARA TIM (EXEMPLO)', 'Email do Registrador': 'parceiro@exemplo.com', 'Status': 'Em Análise', 'Operadora A': 'OUTRA', 'Operadora B': 'TIM', 'Testes': '[]'},
    {'ID': 'CALL-003', 'Data de Registro': '2025-07-02 10:00:00', 'Título da Ocorrência': 'CHAMADA DE (67) 99999-1111 PARA (67) 3421-2222', 'Email do Registrador': 'joao.silva@prefeitura.example.com', 'Status': 'Registrado', 'Operadora A': 'VIVO FIXO', 'Operadora B': 'OI FIXO', 'Testes': '[]'}
]

_equipment_occurrences_db = [{'ID': 'EQUIP-001', 'Data de Registro': '2025-07-01 11:30:00', 'Tipo de Equipamento': 'TELEFONE IP', 'Email do Registrador': 'joao.silva@prefeitura.example.com', 'Status': 'Registrado'}]

# --- FUNÇÕES DE SERVIÇO ---

# ALTERAÇÃO AQUI: Nova função para obter todas as operadoras únicas
def get_all_operators():
    """Busca todas as operadoras únicas já registradas e as retorna em ordem alfabética."""
    operators = set()
    for occ in _call_occurrences_db:
        if occ.get('Operadora A'):
            operators.add(occ['Operadora A'])
        if occ.get('Operadora B'):
            operators.add(occ['Operadora B'])
    
    # Adiciona uma lista padrão para garantir que as principais sempre existam
    default_operators = ["VIVO FIXO", "CLARO FIXO", "OI FIXO", "TIM", "EMBRATEL", "ALGAR TELECOM", "OUTRA"]
    operators.update(default_operators)
    
    return sorted(list(operators))

def check_user_status(email):
    for user in _users_db:
        if user["email"] == email: return user
    return {"status": "unregistered", "role": None}

def request_access(email, full_name, username, role_name):
    role_map = {"Parceiro 67 Telecom": "partner", "Prefeitura de Ponta Porã": "prefeitura"}
    role = role_map.get(role_name, "unknown")
    for user in _users_db:
        if user["email"] == email: return
    _users_db.append({"email": email, "name": full_name, "username": username, "role": role, "status": "pending"})

def register_full_occurrence(user_email, title, testes):
    """Registra uma ocorrência detalhada com múltiplos testes."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_id = f"CALL-{len(_call_occurrences_db) + 1:03d}"
    op_a = testes[0]['op_a'] if testes else 'N/A'
    op_b = testes[0]['op_b'] if testes else 'N/A'
    testes_json = json.dumps(testes)
    new_occurrence = {
        'ID': new_id,
        'Data de Registro': now,
        'Título da Ocorrência': title,
        'Email do Registrador': user_email,
        'Status': 'REGISTRADO',
        'Operadora A': op_a,
        'Operadora B': op_b,
        'Testes': testes_json
    }
    _call_occurrences_db.append(new_occurrence)
    return True

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
    user_occurrences = [occ for occ in _call_occurrences_db + _equipment_occurrences_db if occ.get("Email do Registrador") == user_email]
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
        email_to_role = {user['email']: user['role'] for user in _users_db}
        all_occurrences = [occ for occ in all_occurrences if email_to_role.get(occ.get('Email do Registrador')) == role_filter]
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
