from datetime import datetime
import random
_users_db = [{"email": "admin@craftquest.com", "role": "admin", "status": "approved"}, {"email": "parceiro@67telecom.com", "role": "partner", "status": "approved"}, {"email": "joao.silva@prefeitura.example.com", "role": "prefeitura", "status": "approved"}, {"email": "maria.santos@prefeitura.example.com", "role": "prefeitura", "status": "pending"}, {"email": "pedro.costa@gmail.com", "role": "partner", "status": "pending"}]
_call_occurrences_db = [{'ID': 'CALL-001', 'Data de Registro': '2025-06-30 15:00:12', 'Título da Ocorrência': 'Chiado em ligações para Vivo (Exemplo)', 'Email do Registrador': 'parceiro@67telecom.com', 'Status': 'Resolvido'}, {'ID': 'CALL-002', 'Data de Registro': '2025-07-01 09:05:45', 'Título da Ocorrência': 'Chamadas mudas para TIM (Exemplo)', 'Email do Registrador': 'parceiro@67telecom.com', 'Status': 'Em Análise'}]
_equipment_occurrences_db = [{'ID': 'EQUIP-001', 'Data de Registro': '2025-07-01 11:30:00', 'Tipo de Equipamento': 'Telefone IP', 'Email do Registrador': 'joao.silva@prefeitura.example.com', 'Status': 'Registrado'}]
def check_user_status(email):
    for user in _users_db:
        if user["email"] == email: return user
    return {"status": "unregistered", "role": None}
def request_access(email, role_name):
    role_map = {"Parceiro 67 Telecom": "partner", "Prefeitura de Ponta Porã": "prefeitura"}
    role = role_map.get(role_name, "unknown")
    for user in _users_db:
        if user["email"] == email: return
    _users_db.append({"email": email, "role": role, "status": "pending"})
def get_pending_requests(): return [user for user in _users_db if user["status"] == "pending"]
def update_user_status(email, new_status):
    for user in _users_db:
        if user["email"] == email:
            user["status"] = new_status
            return
def update_occurrence_status(occurrence_id, new_status):
    all_occurrences = _call_occurrences_db + _equipment_occurrences_db
    for occ in all_occurrences:
        if occ.get('ID') == occurrence_id:
            if occ['Status'] != new_status:
                occ['Status'] = new_status
                return True
    return False
def save_simple_call_occurrence(credentials, user_email, title, description): _call_occurrences_db.append({'ID': f"CALL-{random.randint(100, 999)}", "Data de Registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Email do Registrador": user_email, "Título da Ocorrência": title, "Status": "Registrado"})
def save_occurrence_with_tests(credentials, user_email, titulo_ocorrencia, testes_adicionados): _call_occurrences_db.append({'ID': f"CALL-{random.randint(100, 999)}", "Data de Registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Email do Registrador": user_email, "Título da Ocorrência": titulo_ocorrencia, "Status": "Registrado"})
def save_equipment_occurrence(credentials, user_email, equip_data): _equipment_occurrences_db.append({'ID': f"EQUIP-{random.randint(100, 999)}", "Data de Registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Email do Registrador": user_email, "Tipo de Equipamento": equip_data.get('tipo', 'N/A'), "Status": "Registrado"})
def get_occurrences_by_user(credentials, user_email): return [occ for occ in _call_occurrences_db + _equipment_occurrences_db if occ["Email do Registrador"] == user_email]
def get_all_occurrences_for_admin(): return sorted(_call_occurrences_db + _equipment_occurrences_db, key=lambda x: x['Data de Registro'], reverse=True)