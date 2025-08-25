# ==============================================================================
# FICHEIRO: src/app.py
# DESCRIÇÃO: Controlador principal da aplicação. (VERSÃO COM ÍCONE DA JANELA E POLIMENTO DE LOGIN)
#            ATUALIZADO para integrar as novas Views de Gerenciamento de Acessos e Usuários.
#            ATUALIZADO para suportar filtro de ocorrências por status.
# ==============================================================================

import customtkinter as ctk
import tkinter as tk  # NOVO: Importado para tk.TclError
from tkinter import messagebox
import threading
import os
import sys
import requests # NOVO: Para fazer requisições HTTP para verificar a versão
import subprocess # NOVO: Para executar o script de atualização
import time # NOVO: Para pausas no processo de atualização
from builtins import super, print, Exception, hasattr, len, max, range, int, str, dict, open # CORRIGIDO: Importa built-ins explicitamente para satisfazer o Pylance

# Importações dos módulos de serviço e das views
from services.auth_service import AuthService # Importado explicitamente
from services.sheets_service import SheetsService # Importado explicitamente
from views.access_views import RequestAccessView, PendingApprovalView # Importado explicitamente
from views.admin_dashboard_view import AdminDashboardView # Importado explicitamente
from views.equipment_view import EquipmentView # Importado explicitamente
from views.history_view import HistoryView # Importado explicitamente
from views.login_view import LoginView # Importado explicitamente
from views.main_menu_view import MainMenuView # Importado explicitamente
from views.occurrence_detail_view import OccurrenceDetailView # Importado explicitamente
from views.registration_view import RegistrationView # Importado explicitamente
from views.simple_call_view import SimpleCallView # Importado explicitamente
from views.notification_popup import NotificationPopup # Importado explicitamente

# NOVAS IMPORTAÇÕES PARA AS VIEWS DE GERENCIAMENTO
from views.access_management_view import AccessManagementView
from views.user_management_view import UserManagementView


class App(ctk.CTk):
    def __init__(self):
        # --- Configuração do Logging para capturar saída de print ---
        # Define o diretório para salvar os logs (AppData\Local\REGTEL_Logs no Windows)
        log_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "REGTEL_Logs")
        os.makedirs(log_dir, exist_ok=True) # Cria o diretório se não existir
        self.log_file_path = os.path.join(log_dir, "app_debug.log")

        # Abre o ficheiro de log em modo de escrita, com encoding UTF-8.
        # Redireciona sys.stdout e sys.stderr para este ficheiro.
        try:
            self._log_file = open(self.log_file_path, 'w', encoding='utf-8')
            sys.stdout = self._log_file
            sys.stderr = self._log_file
            print(f"--- REGTEL Debug Log Iniciado em: {self.log_file_path} ---")
        except Exception as e:
            # Se não conseguir abrir o log, imprime no console original (se houver)
            # e exibe uma messagebox para o utilizador.
            sys.stdout = sys.__stdout__ # Restaura stdout para o original
            sys.stderr = sys.__stderr__ # Restaura stderr para o original
            print(f"ERRO: Não foi possível iniciar o log para o ficheiro: {self.log_file_path}. Detalhes: {e}")
            messagebox.showerror("Erro de Log", f"Não foi possível iniciar o log da aplicação. Detalhes: {e}")

        # Inicializa a classe pai CustomTkinter
        super().__init__()
        self.title("Plataforma de Registro de Ocorrências (REGTEL)") # Nome do programa atualizado para REGTEL
        self.geometry("900x750")
        self.minsize(800, 650)

        # --- Configurações de Aparência Global ---
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # --- DEFINIÇÃO DAS CORES CUSTOMIZADAS ---
        self.PRIMARY_COLOR = "#00BFFF"
        self.ACCENT_COLOR = "#00CED1"
        self.BASE_COLOR = "#0A0E1A"
        self.TEXT_COLOR = "#FFFFFF"
        self.DANGER_COLOR = "#D32F2F"
        self.DANGER_HOVER_COLOR = "#B71C1C"
        self.GRAY_BUTTON_COLOR = "gray50"
        self.GRAY_HOVER_COLOR = "gray40"

        # Definir a cor de fundo para a janela principal da aplicação
        self.configure(fg_color=self.BASE_COLOR)

        # --- CONFIGURAÇÃO DO ÍCONE DA JANELA ---
        # Caminho para o ficheiro do ícone.
        # Para PyInstaller, sys._MEIPASS é o caminho para os recursos empacotados.
        # Para desenvolvimento, é o diretório raiz do script.
        # CORREÇÃO: Usar getattr para acessar _MEIPASS de forma segura.
        if getattr(sys, '_MEIPASS', None):
            base_path = sys._MEIPASS # pyright: ignore[reportAttributeAccessIssue]
        else:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # Volta para a raiz do projeto

        icon_path = os.path.join(base_path, 'icon.ico') # Assumindo que o ícone é 'icon.ico' na raiz

        try:
            # Tenta definir o ícone. Use .ico para Windows, .png para outros sistemas ou se preferir.
            # CORREÇÃO: Capturar tk.TclError, que é a exceção padrão para problemas de Tkinter/ícone.
            self.iconbitmap(icon_path)
        except tk.TclError as e: # CORREÇÃO: Usar tk.TclError
            print(f"Aviso: Não foi possível carregar o ícone da janela em '{icon_path}'. Erro: {e}")
            # Pode optar por não mostrar messagebox aqui para evitar interrupção no startup
        except Exception as e:
            print(f"Aviso: Ocorreu um erro inesperado ao definir o ícone da janela: {e}")


        self.auth_service = AuthService()
        self.sheets_service = SheetsService(self.auth_service)

        self.credentials = None
        self.user_email = "Carregando..." # Valor inicial
        self.user_profile = {}
        self.detail_window = None
        self.testes_adicionados = []
        self.editing_index = None
        self.operator_list = []

        self.occurrences_cache = None
        self.users_cache = None

        container = ctk.CTkFrame(self, fg_color=self.BASE_COLOR)
        container.pack(fill="both", expand=True)

        self.frames = {}
        view_classes = (
            LoginView, RequestAccessView, PendingApprovalView, MainMenuView,
            AdminDashboardView, HistoryView, RegistrationView, SimpleCallView,
            EquipmentView, AccessManagementView, UserManagementView # Adicionadas as novas views
        )

        # NOVO: Adiciona um atributo para rastrear a tela atual e a tela anterior
        self.current_frame = None
        self.previous_frame_name = None # Armazenará o nome da tela anterior

        for F in view_classes:
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.place(relwidth=1.0, relheight=1.0)

        self.check_initial_login()

        # --- NOVO: Configurações de Atualização ---
        self.CURRENT_APP_VERSION = "1.0.2" # Versão atual da sua aplicação
        
        # URL para o ficheiro version.txt que contém a versão mais recente (ex: "1.0.2")
        # IMPORTANTE: Este URL DEVE ser para um ficheiro RAW content de um REPOSITÓRIO PÚBLICO, SEM TOKENS.
        self.REMOTE_VERSION_URL = "https://raw.githubusercontent.com/giovane-nobrega/REGTEL/master/updates/version.txt" # URL fornecida pelo utilizador
        
        # URL direta para o novo ficheiro do instalador (ex: REGTEL_Installer_1.0.2.exe)
        # Este URL também deve ser público (ex: de um GitHub Release Asset).
        self.NEW_INSTALLER_DOWNLOAD_URL = "https://github.com/giovane-nobrega/REGTEL/releases/download/v1.0.2/REGTEL_Installer_1.0.2.exe" # Exemplo de URL de Release do seu repositório

        # Inicia a verificação de atualização em uma thread separada após um pequeno atraso
        self.after(2000, lambda: threading.Thread(target=self.check_for_updates, daemon=True).start())


    def show_frame(self, page_name, from_view=None, mode="all"): # Adicionado 'mode' para HistoryView
        """
        Mostra uma tela específica da aplicação e guarda a tela anterior para navegação de "voltar".
        :param page_name: O nome da classe da tela a ser mostrada (ex: "MainMenuView").
        :param from_view: O nome da tela de onde a navegação foi iniciada, se aplicável.
        :param mode: O modo de exibição para HistoryView ("all" ou "pending").
        """
        # Se from_view for fornecido e for diferente da tela atual, atualiza previous_frame_name
        if from_view and self.current_frame and from_view != page_name:
            self.previous_frame_name = from_view
        elif not from_view: # Se não foi especificado de onde veio, limpa o previous_frame_name
            self.previous_frame_name = None


        frame = self.frames[page_name]
        if hasattr(frame, 'on_show'):
            # Se a tela for HistoryView, passe o nome da tela anterior E o modo
            if page_name == "HistoryView":
                frame.on_show(self.previous_frame_name, mode=mode)
            else:
                frame.on_show()

        frame.tkraise()
        self.current_frame = page_name # Atualiza a tela atual


    def show_occurrence_details(self, occurrence_id):
        if self.detail_window and self.detail_window.winfo_exists():
            self.detail_window.focus()
            return
        occurrence_data = self.sheets_service.get_occurrence_by_id(occurrence_id)
        if occurrence_data:
            self.detail_window = OccurrenceDetailView(self, occurrence_data)
        else:
            messagebox.showerror("Erro", "Não foi possível encontrar os detalhes da ocorrência.")

    def check_initial_login(self):
        # Aprimoramento da mensagem para guiar o utilizador
        self.frames["LoginView"].set_loading_state("Verificando credenciais...")
        threading.Thread(target=self._check_initial_login_thread, daemon=True).start()

    def _check_initial_login_thread(self):
        creds = self.auth_service.load_user_credentials()
        if creds:
            self.credentials = creds
            self.after(0, self._fetch_user_profile)
        else:
            self.after(0, self.frames["LoginView"].set_default_state)
            self.after(0, self.show_frame, "LoginView")

    def load_secondary_data(self):
        threading.Thread(target=self._load_operators_thread, daemon=True).start()

    def _load_operators_thread(self):
        self.operator_list = self.sheets_service.get_all_operators()
        if "RegistrationView" in self.frames:
            self.after(0, self.frames["RegistrationView"].set_operator_suggestions, self.operator_list)

    def perform_login(self):
        # Mensagem de feedback melhorada para o utilizador
        self.frames["LoginView"].set_loading_state("Aguarde... Uma janela do navegador foi aberta para autenticação. Por favor, complete o login e retorne ao aplicativo.")
        threading.Thread(target=self._run_login_flow_in_thread, daemon=True).start()

    def _run_login_flow_in_thread(self):
        creds = self.auth_service.run_login_flow()
        if creds:
            self.auth_service.save_user_credentials(creds)
            self.credentials = creds

            # --- NOVO: LÓGICA PARA TRAZER A APLICAÇÃO PARA O PRIMEIRO PLANO ---
            self.after(0, self.deiconify)   # Garante que a janela não está minimizada
            self.after(0, self.lift)        # Traz a janela para a frente de outras
            self.after(0, self.focus_force) # Força o foco para a janela
            # ------------------------------------------------------------------

            # Chama o próximo passo na thread principal
            self.after(0, self._fetch_user_profile)
        else:
            self.after(0, lambda: messagebox.showerror("Falha no Login", "O processo de login foi cancelado ou falhou. Por favor, tente novamente."))
            self.after(0, self.frames["LoginView"].set_default_state)

    def _fetch_user_profile(self):
        # Garante que self.user_email é sempre uma string
        self.user_email = str(self.auth_service.get_user_email(self.credentials))
        # print(f"DEBUG (App): Email obtido do auth_service: '{self.user_email}'") # DEBUG PRINT REMOVIDO

        if "Erro" in self.user_email or not self.user_email.strip(): # Verifica se há erro ou se está vazio
            self.after(0, lambda: messagebox.showerror("Erro de Autenticação", "Não foi possível obter o seu e-mail. Por favor, tente novamente ou contacte o o suporte."))
            self.after(0, self.perform_logout)
            return

        self.user_profile = self.sheets_service.check_user_status(self.user_email)
        self.after(0, self.navigate_based_on_status)

    def navigate_based_on_status(self):
        status = self.user_profile.get("status")
        main_group = self.user_profile.get("main_group")
        sub_group = self.user_profile.get("sub_group")

        if status == "approved":
            self.load_secondary_data()

            main_menu = self.frames["MainMenuView"]
            # Passa a versão da aplicação para o MainMenuView
            main_menu.update_user_info(self.user_email, self.user_profile, self.CURRENT_APP_VERSION) # Passando self.CURRENT_APP_VERSION

            if main_group == "67_TELECOM" and sub_group == "SUPER_ADMIN":
                self.show_frame("AdminDashboardView")
                return

            self.show_frame("MainMenuView")

        elif status == "pending":
            self.show_frame("PendingApprovalView")
        else:
            # Assegurar que RequestAccessView esteja no estado correto ao ser mostrada
            self.frames["RequestAccessView"].on_show()
            self.show_frame("RequestAccessView")

    def perform_logout(self):
        self.auth_service.logout()
        self.credentials = None
        self.user_email = None # Define como None ao fazer logout
        self.user_profile = {}
        self.show_frame("LoginView")
        self.frames["LoginView"].set_default_state()

    def submit_access_request(self, full_name, username, main_group, sub_group, company_name=None):
        # --- AQUI ESTÁ A VALIDAÇÃO ADICIONADA ---
        # print(f"DEBUG (App): User email before submitting access request: '{self.user_email}'") # DEBUG PRINT REMOVIDO
        if not self.user_email or self.user_email.strip() == "" or "Erro" in self.user_email:
            messagebox.showerror("Erro Crítico", "Não foi possível obter seu e-mail. Por favor, tente fazer login novamente.")
            self.perform_logout() # Força o logout para iniciar o fluxo de login
            return
        # ----------------------------------------

        success, message = self.sheets_service.request_access(self.user_email, full_name, username, main_group, sub_group, company_name)
        if success:
            # Passar as cores explicitamente
            NotificationPopup(self, message="Solicitação enviada com sucesso! Aguarde aprovação.", type="success",
                              bg_color_success="green", text_color_success="white", # Exemplo de cores para sucesso
                              bg_color_info="gray", text_color_info="white") # Exemplo de cores para info
            self.show_frame("PendingApprovalView")
        else:
            if "já existe para este e-mail" in message:
                messagebox.showerror("E-mail Já Registrado", "Este e-mail já está registado em nosso sistema. Por favor, utilize outro e-mail ou entre em contacto com o administrador para assistência.")
            else:
                messagebox.showerror("Erro ao Enviar Solicitação", f"Não foi possível enviar sua solicitação de acesso: {message}\nPor favor, verifique seus dados e tente novamente.")

    def get_all_occurrences(self, force_refresh=False, exclude_statuses=None): # NOVO: Adicionado exclude_statuses
        """
        Obtém as ocorrências visíveis para o utilizador logado,
        filtrando com base no seu perfil e excluindo status específicos, se fornecido.
        :param force_refresh: Se True, força o recarregamento dos dados do Google Sheets.
        :param exclude_statuses: Lista de status (strings) a serem excluídos da lista final.
        :return: Lista de ocorrências filtradas.
        """
        if force_refresh or self.occurrences_cache is None:
            # Chama a função de filtragem por utilizador do SheetsService
            self.occurrences_cache = self.sheets_service.get_occurrences_by_user(self.user_email)
        
        # Aplica o filtro de exclusão de status, se houver
        if exclude_statuses:
            # Garante que a comparação de status seja case-insensitive
            exclude_statuses_upper = [s.upper() for s in exclude_statuses]
            return [occ for occ in self.occurrences_cache if occ.get('Status', '').upper() not in exclude_statuses_upper]
        
        return self.occurrences_cache

    def get_all_users(self, force_refresh=False):
        if force_refresh or self.users_cache is None:
            self.users_cache = self.sheets_service.get_all_users()
        return self.users_cache

    def get_pending_requests(self): return self.sheets_service.get_pending_requests()

    def update_user_access(self, email, new_status):
        self.sheets_service.update_user_status(email, new_status)
        self.users_cache = None
        if new_status == 'approved':
            # Passar as cores explicitamente
            NotificationPopup(self, message=f"O acesso para {email} foi aprovado com sucesso.", type="success",
                              bg_color_success="green", text_color_success="white",
                              bg_color_info="gray", text_color_info="white")
        else:
            # Passar as cores explicitamente
            NotificationPopup(self, message=f"O acesso para {email} foi rejeitado.", type="info",
                              bg_color_success="green", text_color_success="white",
                              bg_color_info="gray", text_color_info="white")
        self.frames["AccessManagementView"].load_access_requests() # CORREÇÃO: Chamar load_access_requests diretamente na view
        # self.frames["AdminDashboardView"].load_access_requests() # REMOVIDO: Não é mais necessário aqui

    def save_occurrence_status_changes(self, changes):
        if not changes:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum status foi alterado.")
            return
        success, message = self.sheets_service.batch_update_occurrence_statuses(changes)
        if success:
            self.occurrences_cache = None
            # Passar as cores explicitamente
            NotificationPopup(self, message=f"Os status de {len(changes)} ocorrência(s) foram salvos com sucesso.", type="success",
                              bg_color_success="green", text_color_success="white",
                              bg_color_info="gray", text_color_info="white")
            # Força o recarregamento da aba de ocorrências no AdminDashboardView
            if "AdminDashboardView" in self.frames and self.frames["AdminDashboardView"]._occurrences_tab_initialized:
                self.frames["AdminDashboardView"].load_all_occurrences(force_refresh=True)
            # Também recarrega o histórico para consistência
            if "HistoryView" in self.frames:
                self.frames["HistoryView"].load_history()
        else:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar as alterações de status: {message}")

    def update_user_profile(self, changes: dict):
        if not changes:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum perfil foi alterado.")
            return
        success, message = self.sheets_service.batch_update_user_profiles(changes)
        if success:
            self.users_cache = None
            # Passar as cores explicitamente
            NotificationPopup(self, message=f"{len(changes)} perfil(is) de usuário foram atualizados com sucesso.", type="success",
                              bg_color_success="green", text_color_success="white",
                              bg_color_info="gray", text_color_info="white")
            self.frames["UserManagementView"].load_all_users(force_refresh=True) # CORREÇÃO: Chamar load_all_users diretamente na view
            # self.frames["AdminDashboardView"].load_all_users(force_refresh=True) # REMOVIDO: Não é mais necessário aqui
        else:
            messagebox.showerror("Erro ao Salvar", f"Ocorreu um erro ao atualizar os perfis: {message}")

    def get_user_occurrences(self):
        # Este método agora é redundante, pois get_all_occurrences já faz a filtragem por usuário.
        # No entanto, se for chamado, deve retornar o cache filtrado.
        return self.get_all_occurrences()

    def get_current_user_profile(self):
        # Sempre busca o perfil mais recente para garantir permissões atualizadas
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
            self.occurrences_cache = None
            # Passar as cores explicitamente
            NotificationPopup(self, message=message, type="success",
                              bg_color_success="green", text_color_success="white",
                              bg_color_info="gray", text_color_info="white")
            if hasattr(view, 'on_show'):
                 view.on_show()
            self.show_frame("MainMenuView")
        else:
            messagebox.showerror("Ocorreu um Erro", f"Não foi possível completar a operação: {message}\nPor favor, tente novamente.")

    def update_occurrence_status_from_history(self, occurrence_id, new_status):
        """
        Atualiza o status de uma ocorrência a partir da tela de histórico.
        """
        success, message = self.sheets_service.update_occurrence_status(occurrence_id, new_status)
        if success:
            self.occurrences_cache = None # Limpa o cache para forçar recarregamento
            NotificationPopup(self, message=f"Status da ocorrência {occurrence_id} atualizado para '{new_status}'.", type="success",
                              bg_color_success="green", text_color_success="white",
                              bg_color_info="gray", text_color_info="white")
            # Recarrega o histórico para refletir a mudança
            if "HistoryView" in self.frames:
                self.frames["HistoryView"].load_history()
            # Se o AdminDashboardView estiver aberto, força o recarregamento também
            if "AdminDashboardView" in self.frames and self.frames["AdminDashboardView"]._occurrences_tab_initialized:
                self.frames["AdminDashboardView"].load_all_occurrences(force_refresh=True)
        else:
            messagebox.showerror("Erro", f"Não foi possível atualizar o status da ocorrência: {message}")

    def check_for_updates(self):
        """
        Verifica se há uma nova versão da aplicação disponível online.
        """
        try:
            response = requests.get(self.REMOTE_VERSION_URL, timeout=5)
            response.raise_for_status() # Levanta um erro para códigos de status HTTP ruins (4xx ou 5xx)
            remote_version = response.text.strip()

            if remote_version and self._compare_versions(remote_version, self.CURRENT_APP_VERSION) > 0:
                # Nova versão disponível
                self.after(0, lambda: self._prompt_for_update(remote_version))
            else:
                print("REGTEL: Nenhuma atualização disponível ou já está na versão mais recente.")
        except requests.exceptions.RequestException as e:
            print(f"REGTEL: Erro ao verificar atualizações: {e}")
            # Não mostra erro ao utilizador para falhas de verificação de atualização silenciosas
        except Exception as e:
            print(f"REGTEL: Erro inesperado na verificação de atualização: {e}")

    def _compare_versions(self, version1, version2):
        """
        Compara duas strings de versão (ex: '1.0.1' vs '1.0.0').
        Retorna:
        > 0 se version1 > version2
        < 0 se version1 < version2
        = 0 se version1 == version2
        """
        v1_parts = [int(p) for p in version1.split('.')]
        v2_parts = [int(p) for p in version2.split('.')]

        for i in range(max(len(v1_parts), len(v2_parts))):
            p1 = v1_parts[i] if i < len(v1_parts) else 0
            p2 = v2_parts[i] if i < len(v2_parts) else 0
            if p1 > p2:
                return 1
            if p1 < p2:
                return -1
        return 0

    def _prompt_for_update(self, remote_version):
        """
        Pergunta ao utilizador se deseja atualizar a aplicação.
        """
        if messagebox.askyesno(
            "Atualização Disponível",
            f"Uma nova versão do REGTEL ({remote_version}) está disponível!\n"
            "Deseja descarregar e instalar a atualização agora?\n\n"
            "A aplicação será fechada para iniciar o processo de atualização."
        ):
            self.initiate_update()
        else:
            NotificationPopup(self, message="Atualização adiada. Pode verificar novamente mais tarde.", type="info",
                              bg_color_info="gray", text_color_info="white")

    def initiate_update(self):
        """
        Inicia o script de atualização e fecha a aplicação principal.
        """
        # Determina o caminho para o script updater.py
        # CORREÇÃO: Usar getattr para acessar _MEIPASS de forma segura.
        if getattr(sys, '_MEIPASS', None):
            # Se estiver num executável PyInstaller, o updater.py estará no diretório temporário
            updater_script_path = os.path.join(sys._MEIPASS, 'services', 'updater.py') # pyright: ignore[reportAttributeAccessIssue] # Ajustado o caminho para services/updater.py
        else:
            # Em ambiente de desenvolvimento, o updater.py está em src/services
            updater_script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'services', 'updater.py'))
        
        # O caminho para o executável atual da aplicação
        current_app_executable = sys.executable # sys.executable é o caminho para o executável atual (python.exe ou REGTEL.exe)
        
        # NOVO: Passa o caminho do diretório de instalação da aplicação para o updater
        # Se for um onefile, o path é o diretório do executável
        # Se for um onedir, é o diretório raiz da distribuição
        # CORREÇÃO: Usar getattr para acessar _MEIPASS de forma segura.
        if getattr(sys, '_MEIPASS', None):
            # Em PyInstaller onefile, sys._MEIPASS é o diretório temporário onde os ficheiros são extraídos
            # O executável real está em sys.executable. O diretório de instalação é o diretório do executável.
            app_install_dir = os.path.dirname(sys.executable)
        else:
            # Em desenvolvimento, o diretório de instalação é o diretório raiz do projeto
            app_install_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


        try:
            # Lança o script updater.py como um processo separado
            # Usamos 'pythonw.exe' no Windows para evitar uma janela de console
            # sys.executable aponta para o interpretador Python ou para o executável PyInstaller
            if sys.platform.startswith('win'):
                # Tenta usar pythonw.exe para evitar a janela de console
                python_exe = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
                if not os.path.exists(python_exe):
                    python_exe = sys.executable # Fallback para python.exe ou o próprio executável
                
                subprocess.Popen([
                    python_exe,
                    updater_script_path,
                    self.NEW_INSTALLER_DOWNLOAD_URL,
                    app_install_dir # Passa o diretório de instalação
                ], shell=False, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
            else:
                # Para Linux/macOS, executa diretamente com o interpretador
                subprocess.Popen([
                    sys.executable,
                    updater_script_path,
                    self.NEW_INSTALLER_DOWNLOAD_URL,
                    app_install_dir # Passa o diretório de instalação
                ], shell=False)

            print("REGTEL: Iniciando processo de atualização. A aplicação será fechada.")
            self.quit() # Fecha a aplicação principal
        except Exception as e:
            messagebox.showerror("Erro de Atualização", f"Não foi possível iniciar o processo de atualização: {e}")
            print(f"REGTEL: Erro ao iniciar o updater: {e}")

