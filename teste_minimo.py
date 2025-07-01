import os
import sys
import gspread
import customtkinter as ctk
import json
import httplib2
import threading  # Importamos a biblioteca de threads
from google.auth.transport.httplib2 import AuthorizedHttp
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
CLIENT_SECRET_FILE = resource_path('client_secrets.json')
TOKEN_FILE = resource_path('token.json')
NOME_DA_PLANILHA = "Dados_da_Telefonia"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Central de Controle de Telefonia Fixa")
        self.geometry("700x550")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.credentials = None
        self.login_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_menu_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.registration_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.setup_login_screen()
        self.setup_main_menu()
        self.setup_registration_form()
        self.check_initial_login()

    def check_initial_login(self):
        if os.path.exists(TOKEN_FILE):
            try:
                self.credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                if self.credentials and self.credentials.valid:
                    self.show_main_menu()
                    return
                elif self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(self.credentials.to_json())
                    self.show_main_menu()
                    return
            except Exception as e:
                print(f"Erro ao carregar token, solicitando novo login: {e}")
        self.show_login_screen()
        
    def perform_login(self):
        """Inicia a THREAD de autenticação para não congelar a interface."""
        self.login_button.configure(state="disabled", text="Aguarde... Abrindo o navegador")
        # Cria e inicia a thread que fará o trabalho pesado
        login_thread = threading.Thread(target=self._run_login_flow_in_thread)
        login_thread.start()

    def _run_login_flow_in_thread(self):
        """Esta função roda em uma thread separada para fazer o login."""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            self.credentials = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as token:
                token.write(self.credentials.to_json())
            # Quando o login termina, agenda a atualização da UI na thread principal
            self.after(0, self._login_successful)
        except Exception as e:
            print(f"O fluxo de autenticação falhou ou foi cancelado: {e}")
            # Se der erro, agenda a reativação do botão na thread principal
            self.after(0, self._login_failed)

    def _login_successful(self):
        """Chamado na thread principal após o sucesso do login."""
        self.show_main_menu()

    def _login_failed(self):
        """Chamado na thread principal após a falha do login."""
        self.login_button.configure(state="normal", text="Fazer Login com Google")

    def setup_login_screen(self):
        login_label = ctk.CTkLabel(self.login_frame, text="Autenticação Necessária", font=ctk.CTkFont(size=24, weight="bold"))
        login_label.pack(pady=(50, 20))
        self.login_button = ctk.CTkButton(self.login_frame, text="Fazer Login com Google", command=self.perform_login, height=50, font=ctk.CTkFont(size=16))
        self.login_button.pack(pady=20, padx=50, fill="x")

    def setup_main_menu(self):
        title_label = ctk.CTkLabel(self.main_menu_frame, text="Menu Principal", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(40, 20))
        register_button = ctk.CTkButton(self.main_menu_frame, text="Registrar Ocorrência de Chamada", command=self.show_registration_form, height=40)
        register_button.pack(pady=10, padx=50, fill="x")
        exit_button = ctk.CTkButton(self.main_menu_frame, text="Sair", command=self.quit, height=40, fg_color="gray")
        exit_button.pack(pady=10, padx=50, fill="x")

    def setup_registration_form(self):
        self.registration_frame.grid_columnconfigure((0, 1), weight=1)
        form_title = ctk.CTkLabel(self.registration_frame, text="Registro de Ocorrência de Chamada (Telefonia Fixa)", font=ctk.CTkFont(size=18, weight="bold"))
        form_title.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 20))
        label_num_a = ctk.CTkLabel(self.registration_frame, text="Número A (Origem)")
        label_num_a.grid(row=1, column=0, padx=10, pady=(0,5), sticky="w")
        self.entry_num_a = ctk.CTkEntry(self.registration_frame, placeholder_text="Ex: (11) 2345-6789")
        self.entry_num_a.grid(row=2, column=0, padx=10, sticky="ew")
        label_op_a = ctk.CTkLabel(self.registration_frame, text="Operadora A")
        label_op_a.grid(row=3, column=0, padx=10, pady=(10,5), sticky="w")
        self.combo_op_a = ctk.CTkComboBox(self.registration_frame, values=["Vivo Fixo", "Claro Fixo", "Oi Fixo", "Embratel", "Algar Telecom", "Outra"])
        self.combo_op_a.grid(row=4, column=0, padx=10, sticky="ew")
        label_num_b = ctk.CTkLabel(self.registration_frame, text="Número B (Destino)")
        label_num_b.grid(row=1, column=1, padx=10, pady=(0,5), sticky="w")
        self.entry_num_b = ctk.CTkEntry(self.registration_frame, placeholder_text="Ex: (21) 9876-5432")
        self.entry_num_b.grid(row=2, column=1, padx=10, sticky="ew")
        label_op_b = ctk.CTkLabel(self.registration_frame, text="Operadora B")
        label_op_b.grid(row=3, column=1, padx=10, pady=(10,5), sticky="w")
        self.combo_op_b = ctk.CTkComboBox(self.registration_frame, values=["Vivo Fixo", "Claro Fixo", "Oi Fixo", "Embratel", "Algar Telecom", "Outra"])
        self.combo_op_b.grid(row=4, column=1, padx=10, sticky="ew")
        label_problema = ctk.CTkLabel(self.registration_frame, text="Tipo de Problema")
        label_problema.grid(row=5, column=0, columnspan=2, padx=10, pady=(10,5), sticky="w")
        self.combo_problema = ctk.CTkComboBox(self.registration_frame, values=["Linha Muda", "Chiado / Ruído", "Não Completa Chamada", "Não Recebe Chamada", "Linha Cruzada", "Sem Sinal (Linha Morta)", "Outro"])
        self.combo_problema.grid(row=6, column=0, columnspan=2, padx=10, sticky="ew")
        label_desc = ctk.CTkLabel(self.registration_frame, text="Descrição Detalhada")
        label_desc.grid(row=7, column=0, columnspan=2, padx=10, pady=(10,5), sticky="w")
        self.textbox_desc = ctk.CTkTextbox(self.registration_frame, height=80)
        self.textbox_desc.grid(row=8, column=0, columnspan=2, padx=10, sticky="ew")
        self.save_button = ctk.CTkButton(self.registration_frame, text="Salvar Ocorrência", command=self.salvar_dados, height=40)
        self.save_button.grid(row=9, column=0, columnspan=2, padx=10, pady=(20, 10))
        self.back_button = ctk.CTkButton(self.registration_frame, text="Voltar ao Menu", command=self.show_main_menu, fg_color="gray")
        self.back_button.grid(row=10, column=0, columnspan=2, padx=10, pady=5)
        self.feedback_label = ctk.CTkLabel(self.registration_frame, text="")
        self.feedback_label.grid(row=11, column=0, columnspan=2, padx=10, pady=10)

    def forget_all_frames(self):
        self.login_frame.pack_forget()
        self.main_menu_frame.pack_forget()
        self.registration_frame.pack_forget()

    def show_login_screen(self):
        self.forget_all_frames()
        self.login_frame.pack(pady=20, padx=20, fill="both", expand=True)

    def show_main_menu(self):
        self.forget_all_frames()
        self.main_menu_frame.pack(pady=20, padx=20, fill="both", expand=True)

    def show_registration_form(self):
        self.forget_all_frames()
        self.registration_frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.feedback_label.configure(text="")

    def salvar_dados(self):
        self.feedback_label.configure(text="Salvando...", text_color="gray")
        try:
            if not self.credentials or not self.credentials.valid:
                self.show_login_screen()
                self.feedback_label.configure(text="Sessão expirada. Por favor, faça o login novamente.", text_color="orange")
                return
            hora_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            num_a = self.entry_num_a.get()
            op_a = self.combo_op_a.get()
            num_b = self.entry_num_b.get()
            op_b = self.combo_op_b.get()
            tipo_problema = self.combo_problema.get()
            descricao = self.textbox_desc.get("1.0", "end-1c")
            if not num_a or not num_b or not tipo_problema:
                self.feedback_label.configure(text="Erro: Preencha todos os campos obrigatórios!", text_color="red")
                return
            authed_http = AuthorizedHttp(self.credentials)
            response, content = authed_http.request('https://www.googleapis.com/oauth2/v3/userinfo')
            if response.status != 200:
                raise Exception(f"Erro ao buscar informações do usuário: {response.status}")
            user_info = json.loads(content.decode('utf-8'))
            email_usuario = user_info.get('email', 'Não identificado')
            nova_linha = [hora_registro, num_a, op_a, num_b, op_b, tipo_problema, descricao, email_usuario]
            gc = gspread.authorize(self.credentials)
            planilha = gc.open(NOME_DA_PLANILHA).sheet1
            planilha.append_row(nova_linha)
            self.entry_num_a.delete(0, 'end')
            self.entry_num_b.delete(0, 'end')
            self.textbox_desc.delete("1.0", "end")
            self.feedback_label.configure(text="Ocorrência salva com sucesso!", text_color="green")
        except gspread.exceptions.SpreadsheetNotFound:
            self.feedback_label.configure(text=f"Erro: Planilha '{NOME_DA_PLANILHA}' não encontrada!", text_color="red")
        except Exception as e:
            import traceback
            self.feedback_label.configure(text="Erro ao salvar. Verifique o terminal.", text_color="red")
            print("\n--- ERRO CAPTURADO EM salvar_dados ---")
            traceback.print_exc()

if __name__ == '__main__':
    app = App()
    app.mainloop()