import customtkinter as ctk
import threading
import gspread
import auth
from datetime import datetime

NOME_DA_PLANILHA = "Dados_da_Telefonia"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Central de Controle de Telefonia")
        self.geometry("800x750")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.credentials = None
        self.testes_adicionados = []

        self.login_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_menu_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.registration_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        self.setup_login_screen()
        self.setup_main_menu()
        self.setup_registration_form()
        self.check_initial_login()

    def check_initial_login(self):
        self.credentials = auth.load_credentials()
        if self.credentials:
            self.show_main_menu()
        else:
            self.show_login_screen()

    def perform_login(self):
        self.login_button.configure(state="disabled", text="Aguarde... Abrindo o navegador")
        login_thread = threading.Thread(target=self._run_login_flow_in_thread)
        login_thread.start()

    def _run_login_flow_in_thread(self):
        try:
            creds = auth.run_login_flow()
            if creds:
                auth.save_credentials(creds)
                self.credentials = creds
                self.after(0, self._login_successful)
            else:
                self.after(0, self._login_failed)
        except Exception as e:
            print(f"Erro na autenticação: {e}")
            self.after(0, self._login_failed)

    def _login_successful(self):
        self.show_main_menu()

    def _login_failed(self):
        self.login_button.configure(state="normal", text="Fazer Login com Google")

    def setup_login_screen(self):
        login_label = ctk.CTkLabel(self.login_frame, text="Autenticação Necessária", font=ctk.CTkFont(size=24, weight="bold"))
        login_label.pack(pady=(50, 20))
        self.login_button = ctk.CTkButton(self.login_frame, text="Fazer Login com Google", command=self.perform_login, height=50)
        self.login_button.pack(pady=20, padx=50, fill="x")

    def setup_main_menu(self):
        title_label = ctk.CTkLabel(self.main_menu_frame, text="Menu Principal", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(40, 20))
        register_button = ctk.CTkButton(self.main_menu_frame, text="Registrar Ocorrência (Parceiro)", command=self.show_registration_form, height=40)
        register_button.pack(pady=10, padx=50, fill="x")
        exit_button = ctk.CTkButton(self.main_menu_frame, text="Sair", command=self.quit, height=40, fg_color="gray")
        exit_button.pack(pady=10, padx=50, fill="x")

    def setup_registration_form(self):
        main_occurrence_frame = ctk.CTkFrame(self.registration_frame)
        main_occurrence_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(main_occurrence_frame, text="1. Detalhes da Ocorrência Principal", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.entry_ocorrencia_titulo = ctk.CTkEntry(main_occurrence_frame, placeholder_text="Título Resumido da Ocorrência (ex: Falha em chamadas para TIM)")
        self.entry_ocorrencia_titulo.pack(fill="x", padx=10, pady=5)

        test_entry_frame = ctk.CTkFrame(self.registration_frame)
        test_entry_frame.pack(fill="x", padx=10, pady=10)
        test_entry_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(test_entry_frame, text="2. Adicionar Testes de Ligação (Evidências)", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(10, 5))

        ctk.CTkLabel(test_entry_frame, text="Horário do Teste").grid(row=1, column=0, padx=5, pady=(0,0), sticky="w")
        self.entry_teste_horario = ctk.CTkEntry(test_entry_frame, placeholder_text="Ex: 16:05")
        self.entry_teste_horario.grid(row=2, column=0, padx=5, pady=(0,10), sticky="ew")

        ctk.CTkLabel(test_entry_frame, text="Número A").grid(row=1, column=1, padx=5, pady=(0,0), sticky="w")
        self.entry_teste_num_a = ctk.CTkEntry(test_entry_frame, placeholder_text="(11) 2345-6789")
        self.entry_teste_num_a.grid(row=2, column=1, padx=5, pady=(0,10), sticky="ew")

        ctk.CTkLabel(test_entry_frame, text="Operadora A").grid(row=1, column=2, padx=5, pady=(0,0), sticky="w")
        self.combo_teste_op_a = ctk.CTkComboBox(test_entry_frame, values=["Vivo Fixo", "Claro Fixo", "Oi Fixo", "Embratel", "Algar Telecom", "Outra"])
        self.combo_teste_op_a.grid(row=2, column=2, padx=5, pady=(0,10), sticky="ew")

        ctk.CTkLabel(test_entry_frame, text="Número B").grid(row=3, column=0, padx=5, pady=(0,0), sticky="w")
        self.entry_teste_num_b = ctk.CTkEntry(test_entry_frame, placeholder_text="(21) 9876-5432")
        self.entry_teste_num_b.grid(row=4, column=0, padx=5, pady=(0,10), sticky="ew")

        ctk.CTkLabel(test_entry_frame, text="Operadora B").grid(row=3, column=1, padx=5, pady=(0,0), sticky="w")
        self.combo_teste_op_b = ctk.CTkComboBox(test_entry_frame, values=["Vivo Fixo", "Claro Fixo", "Oi Fixo", "Embratel", "Algar Telecom", "Outra"])
        self.combo_teste_op_b.grid(row=4, column=1, padx=5, pady=(0,10), sticky="ew")

        ctk.CTkLabel(test_entry_frame, text="Status da Chamada").grid(row=3, column=2, padx=5, pady=(0,0), sticky="w")
        self.combo_teste_status = ctk.CTkComboBox(test_entry_frame, values=["Falha", "Muda", "Não Completa", "Chiado", "Completou com Sucesso"])
        self.combo_teste_status.grid(row=4, column=2, padx=5, pady=(0,10), sticky="ew")

        self.entry_teste_obs = ctk.CTkEntry(test_entry_frame, placeholder_text="Observações (opcional)")
        self.entry_teste_obs.grid(row=5, column=0, columnspan=3, padx=5, pady=(10,10), sticky="ew")

        self.add_test_button = ctk.CTkButton(test_entry_frame, text="+ Adicionar Teste", command=self.add_test_to_list)
        self.add_test_button.grid(row=5, column=3, padx=5, pady=(10,10), sticky="ew")

        test_list_frame = ctk.CTkFrame(self.registration_frame)
        test_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(test_list_frame, text="3. Testes a Serem Registrados (mínimo 2)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10,5))
        self.scrollable_test_list = ctk.CTkScrollableFrame(test_list_frame, label_text="Nenhum teste adicionado ainda.")
        self.scrollable_test_list.pack(fill="both", expand=True, padx=10, pady=5)

        final_buttons_frame = ctk.CTkFrame(self.registration_frame, fg_color="transparent")
        final_buttons_frame.pack(fill="x", padx=10, pady=10)
        final_buttons_frame.grid_columnconfigure((0, 1), weight=1)
        self.back_button = ctk.CTkButton(final_buttons_frame, text="Voltar ao Menu", command=self.show_main_menu, fg_color="gray")
        self.back_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.submit_button = ctk.CTkButton(final_buttons_frame, text="Registrar Ocorrência Completa", command=self.submit_full_occurrence, height=40)
        self.submit_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def add_test_to_list(self):
        horario = self.entry_teste_horario.get()
        num_a = self.entry_teste_num_a.get()
        op_a = self.combo_teste_op_a.get()
        num_b = self.entry_teste_num_b.get()
        op_b = self.combo_teste_op_b.get()
        status = self.combo_teste_status.get()
        obs = self.entry_teste_obs.get()
        if not horario or not num_a or not num_b or not status:
            return
        self.testes_adicionados.append({"horario": horario, "num_a": num_a, "op_a": op_a, "num_b": num_b, "op_b": op_b, "status": status, "obs": obs})
        self.entry_teste_horario.delete(0, 'end')
        self.entry_teste_num_a.delete(0, 'end')
        self.entry_teste_num_b.delete(0, 'end')
        self.entry_teste_obs.delete(0, 'end')
        self._update_test_display_list()

    def _update_test_display_list(self):
        for widget in self.scrollable_test_list.winfo_children():
            widget.destroy()
        if not self.testes_adicionados:
            self.scrollable_test_list.configure(label_text="Nenhum teste adicionado ainda.")
            return
        self.scrollable_test_list.configure(label_text="")
        for index, teste in enumerate(self.testes_adicionados):
            card_frame = ctk.CTkFrame(self.scrollable_test_list)
            card_frame.pack(fill="x", pady=5, padx=5)
            card_frame.grid_columnconfigure(0, weight=1)
            info_text = f"{teste['horario']} | De: {teste['num_a']} Para: {teste['num_b']} | Status: {teste['status']}"
            ctk.CTkLabel(card_frame, text=info_text, anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=5)
            ctk.CTkButton(card_frame, text="Editar", width=60, command=lambda i=index: self.edit_test(i)).grid(row=0, column=1, padx=5)
            ctk.CTkButton(card_frame, text="Excluir", width=60, fg_color="red", command=lambda i=index: self.delete_test(i)).grid(row=0, column=2, padx=(5, 10))

    def delete_test(self, index):
        self.testes_adicionados.pop(index)
        self._update_test_display_list()

    def edit_test(self, index):
        print(f"Edição do teste {index} não implementada.")

    def submit_full_occurrence(self):
        if len(self.testes_adicionados) < 2:
            print("Erro: Mínimo de 2 testes necessários.")
            return
        try:
            email_usuario = auth.get_user_email(self.credentials)
            print(f"Submetendo dados como {email_usuario}")
            # (Salvar na planilha com gspread...)
        except Exception as e:
            print(f"Erro ao enviar: {e}")

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
        self.testes_adicionados = []
        self._update_test_display_list()
        self.registration_frame.pack(pady=10, padx=10, fill="both", expand=True)

if __name__ == '__main__':
    app = App()
    app.mainloop()
