# ==============================================================================
# FICHEIRO: src/app.py
# DESCRIÇÃO: Controlador principal da aplicação. Orquestra a lógica,
#            serviços e navegação entre as diferentes views.
# ==============================================================================

import customtkinter as ctk
from tkinter import messagebox
import threading

# Importações dos módulos de serviço e das views, respeitando a estrutura de pastas
from services.auth_service import AuthService
from services.sheets_service import SheetsService
from views.access_views import RequestAccessView, PendingApprovalView
from views.admin_dashboard_view import AdminDashboardView
from views.equipment_view import EquipmentView
from views.history_view import HistoryView
from views.login_view import LoginView
from views.main_menu_view import MainMenuView
from views.occurrence_detail_view import OccurrenceDetailView
from views.registration_view import RegistrationView
from views.simple_call_view import SimpleCallView


class App(ctk.CTk):
    """
    Classe principal da aplicação, herda de ctk.CTk para ser a janela raiz.
    """
    def __init__(self):
        super().__init__()
        self.title("Plataforma de Registro de Ocorrências (Craft Quest)")
        self.geometry("900x750")
        self.minsize(800, 650)
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Inicialização dos serviços
        self.auth_service = AuthService()
        self.sheets_service = SheetsService(self.auth_service)

        # Variáveis de estado da aplicação
        self.credentials = None
        self.user_email = "Carregando..."
        self.user_profile = {}
        self.detail_window = None
        self.testes_adicionados = []
        self.editing_index = None
        self.operator_list = []

        # Container principal para as telas (views)
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True)

        self.frames = {}
        # Lista de todas as classes de View que a aplicação utiliza
        view_classes = (
            LoginView, RequestAccessView, PendingApprovalView, MainMenuView,
            AdminDashboardView, HistoryView, RegistrationView, SimpleCallView,
            EquipmentView
        )

        # Itera sobre as classes de View para inicializá-las e armazená-las
        for F in view_classes:
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.place(relwidth=1.0, relheight=1.0)
        
        # Inicia a verificação de login ao arrancar a aplicação
        self.check_initial_login()

    def show_frame(self, page_name):
        """Traz uma frame (tela) específica para a frente."""
        frame = self.frames[page_name]
        # Se a frame tiver um método 'on_show', executa-o (para limpar campos, etc.)
        if hasattr(frame, 'on_show'):
            frame.on_show()
        frame.tkraise()

    def show_occurrence_details(self, occurrence_id):
        """Abre a janela de detalhes da ocorrência."""
        # Impede que múltiplas janelas de detalhe sejam abertas
        if self.detail_window and self.detail_window.winfo_exists():
            self.detail_window.focus()
            return
        
        occurrence_data = self.sheets_service.get_occurrence_by_id(occurrence_id)
        if occurrence_data:
            # Cria uma nova instância da janela de detalhes
            self.detail_window = OccurrenceDetailView(self, occurrence_data)
        else:
            messagebox.showerror("Erro", "Não foi possível encontrar os detalhes da ocorrência.")

    def check_initial_login(self):
        """Verifica se já existem credenciais de login salvas no sistema."""
        self.frames["LoginView"].set_loading_state("Verificando credenciais...")
        # Executa a verificação numa thread para não bloquear a interface
        threading.Thread(target=self._check_initial_login_thread, daemon=True).start()

    def _check_initial_login_thread(self):
        creds = self.auth_service.load_user_credentials()
        if creds:
            self.credentials = creds
            # Volta para a thread principal para atualizar a UI
            self.after(0, self._fetch_user_profile)
        else:
            # Se não houver credenciais, mostra a tela de login
            self.after(0, self.frames["LoginView"].set_default_state)
            self.after(0, self.show_frame, "LoginView")
            
    def load_secondary_data(self):
        """Carrega dados secundários (como a lista de operadoras) em background."""
        threading.Thread(target=self._load_operators_thread, daemon=True).start()

    def _load_operators_thread(self):
        """Busca a lista de operadoras e atualiza o widget de autocomplete."""
        self.operator_list = self.sheets_service.get_all_operators()
        if "RegistrationView" in self.frames:
            self.after(0, self.frames["RegistrationView"].set_operator_suggestions, self.operator_list)

    def perform_login(self):
        """Inicia o fluxo de login do Google."""
        self.frames["LoginView"].set_loading_state("Aguarde... Abrindo o navegador")
        threading.Thread(target=self._run_login_flow_in_thread, daemon=True).start()

    def _run_login_flow_in_thread(self):
        creds = self.auth_service.run_login_flow()
        if creds:
            self.auth_service.save_user_credentials(creds)
            self.credentials = creds
            self.after(0, self._fetch_user_profile)
        else:
            self.after(0, lambda: messagebox.showerror("Falha no Login", "O processo de login foi cancelado ou falhou."))
            self.after(0, self.frames["LoginView"].set_default_state)

    def _fetch_user_profile(self):
        """Após a autenticação, busca os dados do perfil do usuário na planilha."""
        self.user_email = self.auth_service.get_user_email(self.credentials)
        if "Erro" in self.user_email:
            self.after(0, lambda: messagebox.showerror("Erro de Autenticação", "Não foi possível obter o seu e-mail."))
            self.after(0, self.perform_logout)
            return
        
        self.user_profile = self.sheets_service.check_user_status(self.user_email)
        self.after(0, self.navigate_based_on_status)

    def navigate_based_on_status(self):
        """Navega para a tela correta com base no status do usuário ('approved', 'pending', etc.)."""
        status = self.user_profile.get("status")
        if status == "approved":
            self.load_secondary_data()
            main_menu = self.frames["MainMenuView"]
            main_menu.update_user_info(self.user_email, self.user_profile)
            self.show_frame("MainMenuView")
        elif status == "pending":
            self.show_frame("PendingApprovalView")
        else: # 'unregistered' ou outro status
            self.frames["RequestAccessView"].on_show()
            self.show_frame("RequestAccessView")

    def perform_logout(self):
        """Realiza o logout do usuário, limpando as credenciais e o estado."""
        self.auth_service.logout()
        self.credentials = None
        self.user_email = None
        self.user_profile = {}
        self.show_frame("LoginView")
        self.frames["LoginView"].set_default_state()

    def submit_access_request(self, full_name, username, main_group, sub_group, company_name=None):
        """Envia uma solicitação de acesso para um novo usuário."""
        if not all([full_name, username, main_group]):
            messagebox.showwarning("Campos Obrigatórios", "Por favor, preencha todos os campos.")
            return
        success, message = self.sheets_service.request_access(self.user_email, full_name, username, main_group, sub_group, company_name)
        messagebox.showinfo("Solicitação", message)
        if success:
            self.show_frame("PendingApprovalView")
    
    # --- Métodos de delegação para os serviços ---
    # Estes métodos simplesmente chamam as funções correspondentes nos serviços,
    # mantendo o 'app.py' como o único ponto de contacto para as views.
    
    def get_pending_requests(self):
        return self.sheets_service.get_pending_requests()
    
    def update_user_access(self, email, new_status):
        self.sheets_service.update_user_status(email, new_status)
        messagebox.showinfo("Sucesso", f"O acesso para {email} foi atualizado.")
        self.frames["AdminDashboardView"].load_access_requests()

    def get_all_occurrences(self, search_term=None):
        return self.sheets_service.get_all_occurrences(search_term=search_term)

    def save_occurrence_status_changes(self, changes):
        if not changes:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum status foi alterado.")
            return
        for occ_id, new_status in changes.items():
            self.sheets_service.update_occurrence_status(occ_id, new_status)
        messagebox.showinfo("Sucesso", f"{len(changes)} alterações foram salvas.")
        self.frames["AdminDashboardView"].load_all_occurrences()

    def get_all_users(self):
        return self.sheets_service.get_all_users()
    
    def update_user_profile(self, email, main_group, sub_group, company): 
        self.sheets_service.update_user_profile(email, main_group, sub_group, company)
        
    def get_user_occurrences(self, search_term=None): 
        return self.sheets_service.get_occurrences_by_user(self.user_email, search_term)

    def get_current_user_profile(self):
        # Busca o perfil mais recente para garantir que os dados estão atualizados
        return self.sheets_service.check_user_status(self.user_email)

    def submit_simple_call_occurrence(self, form_data):
        view = self.frames["SimpleCallView"]
        view.set_submitting_state(True)
        threading.Thread(target=self._submit_simple_call_thread, args=(form_data,), daemon=True).start()

    def _submit_simple_call_thread(self, form_data):
        success, message = self.sheets_service.register_simple_call_occurrence(self.user_email, form_data)
        self.after(0, self._on_submission_finished, "SimpleCallView", success, message)

    def submit_equipment_occurrence(self, data, attachment_paths=None):
        view = self.frames["EquipmentView"]
        view.set_submitting_state(True)
        threading.Thread(target=self._submit_equipment_thread, args=(data, attachment_paths), daemon=True).start()

    def _submit_equipment_thread(self, data, attachment_paths):
        success, message = self.sheets_service.register_equipment_occurrence(self.credentials, self.user_email, data, attachment_paths)
        self.after(0, self._on_submission_finished, "EquipmentView", success, message)

    def submit_full_occurrence(self, title):
        profile = self.get_current_user_profile()
        main_group = profile.get("main_group")

        if not title:
            messagebox.showwarning("Campo Obrigatório", "O título da ocorrência é obrigatório.")
            return
        if main_group == 'PARTNER' and len(self.testes_adicionados) < 3:
            messagebox.showwarning("Validação Falhou", "É necessário adicionar pelo menos 3 testes para parceiros.")
            return
        
        view = self.frames["RegistrationView"]
        view.set_submitting_state(True)
        threading.Thread(target=self._submit_full_occurrence_thread, args=(title, self.testes_adicionados.copy()), daemon=True).start()

    def _submit_full_occurrence_thread(self, title, testes):
        success, message = self.sheets_service.register_full_occurrence(self.user_email, title, testes)
        self.after(0, self._on_submission_finished, "RegistrationView", success, message)

    def _on_submission_finished(self, view_name, success, message):
        view = self.frames[view_name]
        if hasattr(view, 'set_submitting_state'):
            view.set_submitting_state(False)

        if success:
            messagebox.showinfo("Sucesso", message)
            if hasattr(view, 'on_show'):
                 view.on_show()
            self.show_frame("MainMenuView")
        else:
            messagebox.showerror("Falha no Registro", message)
