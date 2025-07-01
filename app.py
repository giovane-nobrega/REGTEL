import customtkinter as ctk
import threading
import auth  # Importamos nosso módulo de autenticação
import sheets_service  # Módulo para interagir com a planilha (não fornecido)
from tkinter import messagebox
from functools import partial
from gspread.exceptions import WorksheetNotFound

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Central de Controle de Telefonia")
        self.geometry("800x750")
        self.minsize(700, 600) # Define um tamanho mínimo para a janela
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # --- Variáveis de Estado ---
        self.credentials = None
        self.testes_adicionados = []
        self.user_email = "Carregando..."
        self.editing_index = None

        # --- Frames Principais ---
        self.login_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_menu_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.registration_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.history_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        # --- Configuração da UI ---
        self.setup_login_screen()
        self.setup_main_menu()
        self.setup_registration_form()
        self.setup_history_screen()

        # --- Inicialização ---
        self.check_initial_login()

    # --- LÓGICA DE LOGIN E INICIALIZAÇÃO ---

    def check_initial_login(self):
        """Verifica credenciais e, se existirem, busca o e-mail em segundo plano."""
        self.credentials = auth.load_credentials()
        if self.credentials:
            self.show_main_menu()
            self.status_label.configure(text="Logado. Carregando informações do usuário...")
            threading.Thread(target=self._fetch_user_email, daemon=True).start()
        else:
            self.show_login_screen()

    def perform_login(self):
        """Inicia o fluxo de login em uma thread para não travar a UI."""
        self.login_button.configure(state="disabled", text="Aguarde... Abrindo o navegador")
        login_thread = threading.Thread(target=self._run_login_flow_in_thread, daemon=True)
        login_thread.start()

    def _run_login_flow_in_thread(self):
        """Executa o login e agenda a atualização da UI na thread principal."""
        creds = auth.run_login_flow()
        if creds:
            auth.save_credentials(creds)
            self.credentials = creds
            self.after(0, self._login_successful)
        else:
            self.after(0, self._login_failed)

    def _login_successful(self):
        """Após o login, busca o e-mail do usuário e atualiza a UI."""
        self.show_main_menu()
        self.status_label.configure(text="Login bem-sucedido! Carregando e-mail...")
        threading.Thread(target=self._fetch_user_email, daemon=True).start()

    def _login_failed(self):
        """Reativa o botão de login em caso de falha."""
        messagebox.showerror("Falha no Login", "O processo de login foi cancelado ou falhou. Por favor, tente novamente.")
        self.login_button.configure(state="normal", text="Fazer Login com Google")

    def _fetch_user_email(self):
        """Busca o e-mail e agenda a atualização do label de status."""
        email = auth.get_user_email(self.credentials)
        self.user_email = email
        self.after(0, self._update_status_label)

    def _update_status_label(self):
        """Atualiza o texto do label de status com o e-mail do usuário."""
        if self.user_email and "Erro" not in self.user_email:
            self.status_label.configure(text=f"Logado como: {self.user_email}")
        else:
            self.status_label.configure(text="Logado, mas não foi possível obter o e-mail.", text_color="orange")
        self.login_button.configure(state="normal", text="Fazer Login com Google")

    def perform_logout(self):
        """Chama a função de logout e reseta a interface."""
        auth.logout()
        self.user_email = None
        self.credentials = None
        self.show_login_screen()

    # --- CONFIGURAÇÃO DAS TELAS (UI SETUP) ---

    def setup_login_screen(self):
        center_frame = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        center_frame.pack(expand=True)
        login_label = ctk.CTkLabel(center_frame, text="Autenticação Necessária", font=ctk.CTkFont(size=24, weight="bold"))
        login_label.pack(pady=(50, 20))
        self.login_button = ctk.CTkButton(center_frame, text="Fazer Login com Google", command=self.perform_login, height=50, width=300, font=ctk.CTkFont(size=16))
        self.login_button.pack(pady=20, padx=50)

    def setup_main_menu(self):
        center_frame = ctk.CTkFrame(self.main_menu_frame, fg_color="transparent")
        center_frame.pack(expand=True)
        title_label = ctk.CTkLabel(center_frame, text="Menu Principal", font=ctk.CTkFont(size=28, weight="bold"))
        title_label.pack(pady=(0, 40))
        
        buttons_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        buttons_frame.pack()
        
        register_button = ctk.CTkButton(buttons_frame, text="Registrar Ocorrência", command=self.show_registration_form, height=45, width=300, font=ctk.CTkFont(size=14))
        register_button.pack(pady=8, padx=20, fill="x")
        history_button = ctk.CTkButton(buttons_frame, text="Ver Histórico de Ocorrências", command=self.show_history_screen, height=45, width=300, font=ctk.CTkFont(size=14))
        history_button.pack(pady=8, padx=20, fill="x")
        logout_button = ctk.CTkButton(buttons_frame, text="Logout (Trocar de usuário)", command=self.perform_logout, height=45, width=300, font=ctk.CTkFont(size=14), fg_color="#D32F2F", hover_color="#B71C1C")
        logout_button.pack(pady=(20, 8), padx=20, fill="x")
        exit_button = ctk.CTkButton(buttons_frame, text="Fechar Aplicação", command=self.quit, height=45, width=300, font=ctk.CTkFont(size=14), fg_color="gray50", hover_color="gray40")
        exit_button.pack(pady=8, padx=20, fill="x")
        
        self.status_label = ctk.CTkLabel(self.main_menu_frame, text="", font=ctk.CTkFont(size=12))
        self.status_label.pack(side="bottom", fill="x", pady=10, padx=20)

    def setup_registration_form(self):
        # --- CORREÇÃO DE LAYOUT: Reordenado o 'pack' para evitar que os botões sejam cortados ---

        # Frame 4: Botões Finais (Empacotado no final da tela PRIMEIRO)
        final_buttons_frame = ctk.CTkFrame(self.registration_frame, fg_color="transparent")
        final_buttons_frame.pack(side="bottom", fill="x", padx=10, pady=(5, 10))
        final_buttons_frame.grid_columnconfigure((0, 1), weight=1)
        self.back_button = ctk.CTkButton(final_buttons_frame, text="Voltar ao Menu", command=self.show_main_menu, fg_color="gray50", hover_color="gray40")
        self.back_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.submit_button = ctk.CTkButton(final_buttons_frame, text="Registrar Ocorrência Completa", command=self.submit_full_occurrence, height=40)
        self.submit_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # Frame 1: Detalhes da Ocorrência (Empacotado no topo)
        main_occurrence_frame = ctk.CTkFrame(self.registration_frame)
        main_occurrence_frame.pack(side="top", fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(main_occurrence_frame, text="1. Detalhes da Ocorrência Principal", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.entry_ocorrencia_titulo = ctk.CTkEntry(main_occurrence_frame, placeholder_text="Título Resumido da Ocorrência (ex: Falha em chamadas para TIM)")
        self.entry_ocorrencia_titulo.pack(fill="x", padx=10, pady=(0, 10))

        # Frame 2: Adicionar Testes (Empacotado no topo, abaixo do anterior)
        test_entry_frame = ctk.CTkFrame(self.registration_frame)
        test_entry_frame.pack(side="top", fill="x", padx=10, pady=5)
        test_entry_frame.grid_columnconfigure((0, 1, 2), weight=1)
        test_entry_frame.grid_columnconfigure(3, weight=0)
        ctk.CTkLabel(test_entry_frame, text="2. Adicionar Testes de Ligação (Evidências)", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(10, 10))
        ctk.CTkLabel(test_entry_frame, text="Horário do Teste").grid(row=1, column=0, sticky="w", padx=10, pady=(5,0))
        self.entry_teste_horario = ctk.CTkEntry(test_entry_frame, placeholder_text="Ex: 16:05")
        self.entry_teste_horario.grid(row=2, column=0, padx=10, pady=(0,10), sticky="ew")
        ctk.CTkLabel(test_entry_frame, text="Número de Origem (A)").grid(row=1, column=1, sticky="w", padx=10, pady=(5,0))
        self.entry_teste_num_a = ctk.CTkEntry(test_entry_frame, placeholder_text="Ex: 11987654321")
        self.entry_teste_num_a.grid(row=2, column=1, padx=10, pady=(0,10), sticky="ew")
        ctk.CTkLabel(test_entry_frame, text="Operadora de Origem (A)").grid(row=1, column=2, sticky="w", padx=10, pady=(5,0))
        self.combo_teste_op_a = ctk.CTkComboBox(test_entry_frame, values=["Vivo Fixo", "Claro Fixo", "Oi Fixo", "Embratel", "Algar Telecom", "Outra"])
        self.combo_teste_op_a.grid(row=2, column=2, padx=10, pady=(0,10), sticky="ew")
        ctk.CTkLabel(test_entry_frame, text="Número de Destino (B)").grid(row=3, column=0, sticky="w", padx=10, pady=(5,0))
        self.entry_teste_num_b = ctk.CTkEntry(test_entry_frame, placeholder_text="Ex: 21912345678")
        self.entry_teste_num_b.grid(row=4, column=0, padx=10, pady=(0,10), sticky="ew")
        ctk.CTkLabel(test_entry_frame, text="Operadora de Destino (B)").grid(row=3, column=1, sticky="w", padx=10, pady=(5,0))
        self.combo_teste_op_b = ctk.CTkComboBox(test_entry_frame, values=["Vivo Fixo", "Claro Fixo", "Oi Fixo", "Embratel", "Algar Telecom", "Outra"])
        self.combo_teste_op_b.grid(row=4, column=1, padx=10, pady=(0,10), sticky="ew")
        ctk.CTkLabel(test_entry_frame, text="Status da Chamada").grid(row=3, column=2, sticky="w", padx=10, pady=(5,0))
        self.combo_teste_status = ctk.CTkComboBox(test_entry_frame, values=["Falha", "Muda", "Não Completa", "Chiado", "Completou com Sucesso"])
        self.combo_teste_status.grid(row=4, column=2, padx=10, pady=(0,10), sticky="ew")
        ctk.CTkLabel(test_entry_frame, text="Observações (opcional)").grid(row=5, column=0, columnspan=3, sticky="w", padx=10, pady=(5,0))
        self.entry_teste_obs = ctk.CTkEntry(test_entry_frame, placeholder_text="Ex: A ligação caiu após 5 segundos")
        self.entry_teste_obs.grid(row=6, column=0, columnspan=3, padx=10, pady=(0,10), sticky="ew")
        self.add_test_button = ctk.CTkButton(test_entry_frame, text="+ Adicionar Teste", command=self.add_or_update_test, height=36)
        self.add_test_button.grid(row=2, column=3, rowspan=5, padx=10, pady=(0,10), sticky="nsew")

        # Frame 3: Lista de Testes (Empacotado por último para preencher o espaço restante)
        test_list_frame = ctk.CTkFrame(self.registration_frame)
        test_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkLabel(test_list_frame, text="3. Testes a Serem Registrados (mínimo 2)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10,5))
        self.scrollable_test_list = ctk.CTkScrollableFrame(test_list_frame, label_text="Nenhum teste adicionado ainda.")
        self.scrollable_test_list.pack(fill="both", expand=True, padx=10, pady=5)

    def setup_history_screen(self):
        history_title = ctk.CTkLabel(self.history_frame, text="Histórico de Ocorrências", font=ctk.CTkFont(size=24, weight="bold"))
        history_title.pack(pady=(0, 10))
        self.history_scrollable_frame = ctk.CTkScrollableFrame(self.history_frame, label_text="Carregando histórico...")
        self.history_scrollable_frame.pack(fill="both", expand=True, padx=0, pady=10)
        back_button = ctk.CTkButton(self.history_frame, text="Voltar ao Menu", command=self.show_main_menu, fg_color="gray50", hover_color="gray40")
        back_button.pack(pady=(10, 0), padx=0, fill="x")

    # --- LÓGICA DE NAVEGAÇÃO E MANIPULAÇÃO DE DADOS ---

    def _clear_test_fields(self):
        """Limpa todos os campos de entrada do formulário de teste."""
        self.entry_teste_horario.delete(0, 'end')
        self.entry_teste_num_a.delete(0, 'end')
        self.entry_teste_num_b.delete(0, 'end')
        self.entry_teste_obs.delete(0, 'end')
        self.combo_teste_op_a.set("")
        self.combo_teste_op_b.set("")
        self.combo_teste_status.set("")

    def add_or_update_test(self):
        """Adiciona um novo teste à lista ou atualiza um existente."""
        horario = self.entry_teste_horario.get()
        num_a = self.entry_teste_num_a.get()
        op_a = self.combo_teste_op_a.get()
        num_b = self.entry_teste_num_b.get()
        op_b = self.combo_teste_op_b.get()
        status = self.combo_teste_status.get()
        obs = self.entry_teste_obs.get()
        
        # Validação para garantir que todos os campos (exceto obs) estão preenchidos
        if not all([horario, num_a, op_a, num_b, op_b, status]):
            messagebox.showerror("Erro de Validação", "Todos os campos do teste de ligação (exceto Observações) são obrigatórios.")
            return
        
        teste_data = {"horario": horario, "num_a": num_a, "op_a": op_a, "num_b": num_b, "op_b": op_b, "status": status, "obs": obs}
        
        if self.editing_index is not None:
            self.testes_adicionados[self.editing_index] = teste_data
            self.editing_index = None
            self.add_test_button.configure(text="+ Adicionar Teste", fg_color=("#3B8ED0", "#1F6AA5"))
        else:
            self.testes_adicionados.append(teste_data)
        
        self._clear_test_fields()
        self._update_test_display_list()

    def _update_test_display_list(self):
        """Redesenha a lista de testes na UI com um layout de cards aprimorado."""
        for widget in self.scrollable_test_list.winfo_children():
            widget.destroy()

        if not self.testes_adicionados:
            self.scrollable_test_list.configure(label_text="Nenhum teste adicionado ainda.")
            return

        self.scrollable_test_list.configure(label_text="")
        for index, teste in enumerate(self.testes_adicionados):
            card_frame = ctk.CTkFrame(self.scrollable_test_list, fg_color=("gray90", "gray25"))
            card_frame.pack(fill="x", pady=5, padx=5)
            card_frame.grid_columnconfigure(0, weight=1)
            card_frame.grid_columnconfigure(1, weight=0)

            info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
            de_para_text = f"De: {teste['num_a']} ({teste['op_a']})  ->  Para: {teste['num_b']} ({teste['op_b']})"
            ctk.CTkLabel(info_frame, text=de_para_text, anchor="w").pack(fill="x")
            status_text = f"Horário: {teste['horario']}  |  Status: {teste['status']}"
            ctk.CTkLabel(info_frame, text=status_text, anchor="w", text_color="gray60").pack(fill="x")
            if teste['obs']:
                ctk.CTkLabel(info_frame, text=f"Obs: {teste['obs']}", anchor="w", font=ctk.CTkFont(slant="italic")).pack(fill="x")

            button_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            button_frame.grid(row=0, column=1, padx=(0, 10), pady=5)
            edit_button = ctk.CTkButton(button_frame, text="Editar", width=60, command=partial(self.edit_test, index))
            edit_button.pack(side="left", padx=(0, 5))
            delete_button = ctk.CTkButton(button_frame, text="Excluir", width=60, fg_color="#D32F2F", hover_color="#B71C1C", command=partial(self.delete_test, index))
            delete_button.pack(side="left")

    def delete_test(self, index):
        """Remove um teste da lista após confirmação."""
        if messagebox.askyesno("Confirmar Exclusão", "Você tem certeza que deseja excluir este teste?"):
            self.testes_adicionados.pop(index)
            self._update_test_display_list()

    def edit_test(self, index):
        """Preenche o formulário com os dados de um teste para edição."""
        self.editing_index = index
        teste_para_editar = self.testes_adicionados[index]
        self._clear_test_fields()
        self.entry_teste_horario.insert(0, teste_para_editar['horario'])
        self.entry_teste_num_a.insert(0, teste_para_editar['num_a'])
        self.combo_teste_op_a.set(teste_para_editar['op_a'])
        self.entry_teste_num_b.insert(0, teste_para_editar['num_b'])
        self.combo_teste_op_b.set(teste_para_editar['op_b'])
        self.combo_teste_status.set(teste_para_editar['status'])
        self.entry_teste_obs.insert(0, teste_para_editar['obs'])
        self.add_test_button.configure(text="✔ Atualizar Teste", fg_color="green", hover_color="darkgreen")

    def submit_full_occurrence(self):
        """Valida e submete a ocorrência completa para o Google Sheets."""
        if len(self.testes_adicionados) < 2:
            messagebox.showwarning("Validação Falhou", "É necessário adicionar pelo menos 2 testes de ligação para registrar a ocorrência.")
            return
        titulo_ocorrencia = self.entry_ocorrencia_titulo.get()
        if not titulo_ocorrencia:
            messagebox.showwarning("Validação Falhou", "Por favor, preencha o Título da Ocorrência.")
            return

        self.submit_button.configure(state="disabled", text="Enviando...")
        self.update_idletasks()
        
        try:
            sheets_service.save_occurrence_with_tests(
                self.credentials,
                self.user_email,
                titulo_ocorrencia,
                self.testes_adicionados
            )
            messagebox.showinfo("Sucesso", "Ocorrência e todos os testes foram registrados com sucesso!")
            self.entry_ocorrencia_titulo.delete(0, 'end')
            self.testes_adicionados = []
            self._update_test_display_list()
            self.show_main_menu()
        except WorksheetNotFound as e:
            messagebox.showerror("Erro de Planilha", str(e))
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro ao submeter a ocorrência: {e}")
        finally:
            self.submit_button.configure(state="normal", text="Registrar Ocorrência Completa")

    def forget_all_frames(self):
        """Oculta todos os frames principais."""
        self.login_frame.pack_forget()
        self.main_menu_frame.pack_forget()
        self.registration_frame.pack_forget()
        self.history_frame.pack_forget()

    def show_login_screen(self):
        self.forget_all_frames()
        self.login_frame.pack(fill="both", expand=True)

    def show_main_menu(self):
        self.forget_all_frames()
        self.main_menu_frame.pack(fill="both", expand=True, padx=20, pady=20)

    def show_registration_form(self):
        self.forget_all_frames()
        self.entry_ocorrencia_titulo.delete(0, 'end')
        self.testes_adicionados = []
        self._update_test_display_list()
        self.editing_index = None
        self.add_test_button.configure(text="+ Adicionar Teste", fg_color=("#3B8ED0", "#1F6AA5"))
        self._clear_test_fields()
        self.registration_frame.pack(fill="both", expand=True, padx=20, pady=20)

    def show_history_screen(self):
        self.forget_all_frames()
        self.history_frame.pack(fill="both", expand=True, padx=20, pady=20)
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        self.history_scrollable_frame.configure(label_text="Carregando...")
        self.update_idletasks()
        threading.Thread(target=self._load_history_data, daemon=True).start()

    def _load_history_data(self):
        """Busca os dados do histórico em uma thread e agenda a atualização da UI."""
        try:
            occurrences = sheets_service.get_all_occurrences(self.credentials)
            self.after(0, self._populate_history_list, occurrences)
        except Exception as e:
            print(f"Erro ao carregar histórico: {e}")
            self.after(0, self._show_history_error, str(e))

    def _populate_history_list(self, occurrences):
        """Preenche a lista de histórico na UI com um layout de cards."""
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        
        if not occurrences:
            self.history_scrollable_frame.configure(label_text="Nenhuma ocorrência encontrada.")
            return

        self.history_scrollable_frame.configure(label_text="")
        for item in reversed(occurrences):
            card = ctk.CTkFrame(self.history_scrollable_frame)
            card.pack(fill="x", padx=5, pady=5)
            card.grid_columnconfigure(0, weight=1)
            card.grid_columnconfigure(1, weight=0)

            title = item.get('Título da Ocorrência', 'N/A')
            date = item.get('Data de Registro', 'N/A')
            email = item.get('Email do Registrador', 'N/A')
            status = item.get('Status', 'N/A')

            title_label = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
            title_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 0))
            details_label = ctk.CTkLabel(card, text=f"Registrado por: {email} em {date}", anchor="w", text_color="gray60")
            details_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0,5))
            status_label = ctk.CTkLabel(card, text=f"Status: {status}", anchor="e", font=ctk.CTkFont(weight="bold"))
            status_label.grid(row=1, column=1, sticky="e", padx=10, pady=(0,5))

    def _show_history_error(self, error_message):
        """Exibe uma mensagem de erro na tela de histórico."""
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        self.history_scrollable_frame.configure(label_text=f"Falha ao carregar o histórico.\nVerifique sua conexão ou a planilha.\nErro: {error_message}")


if __name__ == '__main__':
    app = App()
    app.mainloop()
