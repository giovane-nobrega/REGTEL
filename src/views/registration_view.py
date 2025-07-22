import customtkinter as ctk
from tkinter import messagebox
from functools import partial
from .autocomplete_widget import AutocompleteEntry


class RegistrationView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Configuração da Responsividade ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # A linha 2 (lista de testes) expande

        # --- Widgets ---
        main_occurrence_frame = ctk.CTkFrame(self)
        main_occurrence_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        test_entry_frame = ctk.CTkFrame(self)
        test_entry_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        test_list_frame = ctk.CTkFrame(self)
        test_list_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        test_list_frame.grid_rowconfigure(1, weight=1)
        test_list_frame.grid_columnconfigure(0, weight=1)

        final_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        final_buttons_frame.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")
        final_buttons_frame.grid_columnconfigure((0, 1), weight=1)

        # Frame 1: Detalhes da Ocorrência
        ctk.CTkLabel(main_occurrence_frame, text="1. Detalhes da Ocorrência de Chamada",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.entry_ocorrencia_titulo = ctk.CTkEntry(
            main_occurrence_frame, placeholder_text="Título Resumido da Ocorrência (ex: Falha em chamadas para TIM)")
        self.entry_ocorrencia_titulo.pack(fill="x", padx=10, pady=(0, 10))

        # Frame 2: Adicionar Testes
        test_entry_frame.grid_columnconfigure((0, 1, 2), weight=1)
        test_entry_frame.grid_columnconfigure(3, weight=0)
        ctk.CTkLabel(test_entry_frame, text="2. Adicionar Testes de Ligação (Evidências)", font=ctk.CTkFont(
            size=16, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(10, 10))
        
        ctk.CTkLabel(test_entry_frame, text="Horário do Teste (HHMM)").grid(
            row=1, column=0, sticky="w", padx=10, pady=(5, 0))
        self.entry_teste_horario = ctk.CTkEntry(
            test_entry_frame, placeholder_text="Ex: 1605")
        self.entry_teste_horario.grid(
            row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.entry_teste_horario.bind("<FocusOut>", self._validate_and_format_horario)

        ctk.CTkLabel(test_entry_frame, text="Número de Origem (A)").grid(
            row=1, column=1, sticky="w", padx=10, pady=(5, 0))
        self.entry_teste_num_a = ctk.CTkEntry(
            test_entry_frame, placeholder_text="Ex: 11987654321")
        self.entry_teste_num_a.grid(
            row=2, column=1, padx=10, pady=(0, 10), sticky="ew")
        
        ctk.CTkLabel(test_entry_frame, text="Operadora de Origem (A)").grid(
            row=1, column=2, sticky="w", padx=10, pady=(5, 0))
        self.entry_op_a = AutocompleteEntry(test_entry_frame, placeholder_text="Digite para buscar...")
        self.entry_op_a.grid(
            row=2, column=2, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(test_entry_frame, text="Número de Destino (B)").grid(
            row=3, column=0, sticky="w", padx=10, pady=(5, 0))
        self.entry_teste_num_b = ctk.CTkEntry(
            test_entry_frame, placeholder_text="Ex: 21912345678")
        self.entry_teste_num_b.grid(
            row=4, column=0, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(test_entry_frame, text="Operadora de Destino (B)").grid(
            row=3, column=1, sticky="w", padx=10, pady=(5, 0))
        self.entry_op_b = AutocompleteEntry(test_entry_frame, placeholder_text="Digite para buscar...")
        self.entry_op_b.grid(
            row=4, column=1, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(test_entry_frame, text="Status da Chamada").grid(
            row=3, column=2, sticky="w", padx=10, pady=(5, 0))
        self.combo_teste_status = ctk.CTkComboBox(test_entry_frame, values=[
                                                  "FALHA", "MUDA", "NÃO COMPLETA", "CHIADO", "COMPLETOU COM SUCESSO"])
        self.combo_teste_status.grid(
            row=4, column=2, padx=10, pady=(0, 10), sticky="ew")
        
        ctk.CTkLabel(test_entry_frame, text="Observações (obrigatório)").grid(
            row=5, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 0))
        self.entry_teste_obs = ctk.CTkEntry(
            test_entry_frame, placeholder_text="Ex: A ligação caiu após 5 segundos")
        self.entry_teste_obs.grid(
            row=6, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")
        
        self.add_test_button = ctk.CTkButton(
            test_entry_frame, text="+ Adicionar Teste", command=self.add_or_update_test, height=36)
        self.add_test_button.grid(
            row=2, column=3, rowspan=5, padx=10, pady=(0, 10), sticky="nsew")

        # Frame 3: Lista de Testes
        ctk.CTkLabel(test_list_frame, text="3. Testes a Serem Registrados", font=ctk.CTkFont(
            size=16, weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        self.scrollable_test_list = ctk.CTkScrollableFrame(
            test_list_frame, label_text="Nenhum teste adicionado ainda.")
        self.scrollable_test_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Frame 4: Botões Finais
        self.back_button = ctk.CTkButton(final_buttons_frame, text="Voltar ao Menu", command=lambda: self.controller.show_frame(
            "MainMenuView"), fg_color="gray50", hover_color="gray40")
        self.back_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.submit_button = ctk.CTkButton(
            final_buttons_frame, text="Registrar Ocorrência Completa", command=self.submit, height=40)
        self.submit_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def set_operator_suggestions(self, operators):
        self.entry_op_a.set_suggestions(operators)
        self.entry_op_b.set_suggestions(operators)

    def on_show(self):
        self.controller.testes_adicionados = []
        self.controller.editing_index = None
        self.entry_ocorrencia_titulo.delete(0, 'end')
        self._clear_test_fields()
        self._update_test_display_list()
        self.add_test_button.configure(
            text="+ Adicionar Teste", fg_color=("#3B8ED0", "#1F6AA5"))
        self.set_operator_suggestions(self.controller.operator_list)

    def _clear_test_fields(self):
        self.entry_teste_horario.delete(0, 'end')
        self.entry_teste_num_a.delete(0, 'end')
        self.entry_teste_num_b.delete(0, 'end')
        self.entry_teste_obs.delete(0, 'end')
        self.entry_op_a.delete(0, 'end')
        self.entry_op_b.delete(0, 'end')
        self.combo_teste_status.set("")

    def add_or_update_test(self):
        horario = self.entry_teste_horario.get().upper()
        num_a = self.entry_teste_num_a.get().upper()
        op_a = self.entry_op_a.get().upper()
        num_b = self.entry_teste_num_b.get().upper()
        op_b = self.entry_op_b.get().upper()
        status = self.combo_teste_status.get().upper()
        obs = self.entry_teste_obs.get().upper()
        
        if not all([horario, num_a, op_a, num_b, op_b, status, obs]):
            messagebox.showerror(
                "Erro de Validação", "Todos os campos do teste de ligação, incluindo Observações, são obrigatórios.")
            return

        teste_data = {"horario": horario, "num_a": num_a, "op_a": op_a,
                      "num_b": num_b, "op_b": op_b, "status": status, "obs": obs}

        if self.controller.editing_index is not None:
            self.controller.testes_adicionados[self.controller.editing_index] = teste_data
            self.controller.editing_index = None
            self.add_test_button.configure(
                text="+ Adicionar Teste", fg_color=("#3B8ED0", "#1F6AA5"))
        else:
            self.controller.testes_adicionados.append(teste_data)

        self._clear_test_fields()
        self._update_test_display_list()

    def _update_test_display_list(self):
        for widget in self.scrollable_test_list.winfo_children():
            widget.destroy()

        if not self.controller.testes_adicionados:
            self.scrollable_test_list.configure(
                label_text="Nenhum teste adicionado ainda.")
            return

        self.scrollable_test_list.configure(label_text="")
        for index, teste in enumerate(self.controller.testes_adicionados):
            card_frame = ctk.CTkFrame(
                self.scrollable_test_list, fg_color=("gray90", "gray25"))
            card_frame.pack(fill="x", pady=5, padx=5)
            card_frame.grid_columnconfigure(0, weight=1)
            
            info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
            de_para_text = f"De: {teste['num_a']} ({teste['op_a']})  ->  Para: {teste['num_b']} ({teste['op_b']})"
            ctk.CTkLabel(info_frame, text=de_para_text,
                         anchor="w").pack(fill="x")
            status_text = f"Horário: {teste['horario']}  |  Status: {teste['status']}"
            ctk.CTkLabel(info_frame, text=status_text, anchor="w",
                         text_color="gray60").pack(fill="x")
            if teste['obs']:
                ctk.CTkLabel(info_frame, text=f"Obs: {teste['obs']}", anchor="w", font=ctk.CTkFont(
                    slant="italic")).pack(fill="x")

            button_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            button_frame.grid(row=0, column=1, padx=(0, 10), pady=5)
            edit_button = ctk.CTkButton(
                button_frame, text="Editar", width=60, command=partial(self.edit_test, index))
            edit_button.pack(side="left", padx=(0, 5))
            delete_button = ctk.CTkButton(button_frame, text="Excluir", width=60, fg_color="#D32F2F",
                                          hover_color="#B71C1C", command=partial(self.delete_test, index))
            delete_button.pack(side="left")

    def delete_test(self, index):
        if messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir este teste?"):
            self.controller.testes_adicionados.pop(index)
            self._update_test_display_list()

    def edit_test(self, index):
        self.controller.editing_index = index
        teste_para_editar = self.controller.testes_adicionados[index]
        self._clear_test_fields()
        self.entry_teste_horario.insert(0, teste_para_editar['horario'])
        self.entry_teste_num_a.insert(0, teste_para_editar['num_a'])
        self.entry_op_a.insert(0, teste_para_editar['op_a'])
        self.entry_teste_num_b.insert(0, teste_para_editar['num_b'])
        self.entry_op_b.insert(0, teste_para_editar['op_b'])
        self.combo_teste_status.set(teste_para_editar['status'])
        self.entry_teste_obs.insert(0, teste_para_editar['obs'])
        self.add_test_button.configure(
            text="✔ Atualizar Teste", fg_color="green", hover_color="darkgreen")

    def submit(self):
        title = self.entry_ocorrencia_titulo.get().upper()
        self.controller.submit_full_occurrence(title)

    def set_submitting_state(self, is_submitting):
        if is_submitting:
            self.submit_button.configure(state="disabled", text="Enviando...")
        else:
            self.submit_button.configure(
                state="normal", text="Registrar Ocorrência Completa")

    def _validate_and_format_horario(self, event=None):
        horario_str = self.entry_teste_horario.get()
        if not horario_str:
            return

        digits = horario_str.replace(":", "")
        if not digits.isdigit() or len(digits) != 4:
            messagebox.showerror("Formato Inválido", "Por favor, insira o horário com 4 dígitos no formato HHMM (ex: 1430).")
            self.entry_teste_horario.after(0, lambda: self.entry_teste_horario.delete(0, 'end'))
            return
        try:
            hora = int(digits[0:2])
            minuto = int(digits[2:4])
            if not (0 <= hora <= 23 and 0 <= minuto <= 59):
                raise ValueError("Horário fora do intervalo válido")
            formatted_time = f"{hora:02d}:{minuto:02d}"
            self.entry_teste_horario.delete(0, 'end')
            self.entry_teste_horario.insert(0, formatted_time)
        except (ValueError, IndexError):
            messagebox.showerror("Horário Inválido", f"O horário '{horario_str}' não é válido. Use o formato HHMM.")
            self.entry_teste_horario.after(0, lambda: self.entry_teste_horario.delete(0, 'end'))
            return
