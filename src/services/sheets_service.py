from datetime import datetime
import random
_users_db = [
    {"email": "giovane67telecom@gmail.com", "name": "Giovani Ferreira", "username": "gferreira", "role": "admin", "status": "approved"},
    {"email": "parceiro@exemplo.com", "name": "Parceiro Exemplo", "username": "parceiro", "role": "partner", "status": "approved"},
    {"email": "joao.silva@prefeitura.example.com", "name": "João da Silva", "username": "jsilva", "role": "prefeitura", "status": "approved"},
    {"email": "maria.santos@prefeitura.example.com", "name": "Maria Santos", "username": "msantos", "role": "prefeitura", "status": "pending"},
    {"email": "pedro.costa@gmail.com", "name": "Pedro Costa", "username": "pcosta", "role": "partner", "status": "pending"},
]
_call_occurrences_db = [
    {'ID': 'CALL-001', 'Data de Registro': '2025-06-30 15:00:12', 'Título da Ocorrência': 'Chiado em ligações para Vivo (Exemplo)', 'Email do Registrador': 'parceiro@exemplo.com', 'Status': 'Resolvido', 'Operadora A': 'Vivo Fixo', 'Operadora B': 'Claro Fixo'}, 
    {'ID': 'CALL-002', 'Data de Registro': '2025-07-01 09:05:45', 'Título da Ocorrência': 'Chamadas mudas para TIM (Exemplo)', 'Email do Registrador': 'parceiro@exemplo.com', 'Status': 'Em Análise', 'Operadora A': 'Outra', 'Operadora B': 'TIM'},
    {'ID': 'CALL-003', 'Data de Registro': '2025-07-02 10:00:00', 'Título da Ocorrência': 'Chamada de (67) 99999-1111 para (67) 3421-2222', 'Email do Registrador': 'joao.silva@prefeitura.example.com', 'Status': 'Registrado', 'Operadora A': 'Vivo Fixo', 'Operadora B': 'Oi Fixo'}
]
_equipment_occurrences_db = [{'ID': 'EQUIP-001', 'Data de Registro': '2025-07-01 11:30:00', 'Tipo de Equipamento': 'Telefone IP', 'Email do Registrador': 'joao.silva@prefeitura.example.com', 'Status': 'Registrado'}]
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
def get_occurrences_by_user(credentials, user_email): return [occ for occ in _call_occurrences_db + _equipment_occurrences_db if occ["Email do Registrador"] == user_email]
def get_all_occurrences_for_admin(status_filter=None, role_filter=None):
    """Busca TODAS as ocorrências para o dashboard do admin, com filtros opcionais."""
    all_occurrences = _call_occurrences_db + _equipment_occurrences_db
    
    # Filtro por status
    if status_filter and status_filter != "Todos":
        all_occurrences = [occ for occ in all_occurrences if occ.get('Status') == status_filter]
        
    # Filtro por perfil
    if role_filter and role_filter != "Todos":
        email_to_role = {user['email']: user['role'] for user in _users_db}
        all_occurrences = [occ for occ in all_occurrences if email_to_role.get(occ.get('Email do Registrador')) == role_filter]
        
    return sorted(all_occurrences, key=lambda x: x['Data de Registro'], reverse=True)