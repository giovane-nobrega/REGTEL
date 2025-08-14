# ==============================================================================
# FICHEIRO: src/views/registration_view.py
# DESCRIÇÃO: Contém a classe de interface para o formulário de registo
#            detalhado de ocorrências de chamada. (DESTAQUE DE EDIÇÃO E CORES)
# ==============================================================================
import customtkinter as ctk
from tkinter import messagebox
from functools import partial
from .autocomplete_widget import AutocompleteEntry
import re

class RegistrationView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent) # Removido fg_color do super().__init__
        self.controller = controller

        # Definir a cor de fundo após a inicialização do super
        self.configure(fg_color=self.controller.BASE_COLOR)

        # --- ESTRUTURA DE LAYOUT PRINCIPAL ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) 

        main_occurrence_frame = ctk.CTkFrame(self, fg_color="gray15") # Fundo do frame de ocorrência principal
        main_occurrence_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        # --- ALTERAÇÃO AQUI: Frame de teste agora é uma variável de instância ---
        self.test_entry_frame = ctk.CTkFrame(self, fg_color="gray15") # Fundo do frame de entrada de teste
        self.test_entry_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        test_list_frame = ctk.CTkFrame(self, fg_color="gray15") # Fundo do frame da lista de testes
        test_list_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        test_list_frame.grid_rowconfigure(1, weight=1)
        test_list_frame.grid_columnconfigure(0, weight=1)

        final_buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        final_buttons_frame.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")
        final_buttons_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(main_occurrence_frame, text="1. Detalhes da Ocorrência de Chamada",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).pack(anchor="w", padx=10, pady=(10, 5))
        self.entry_ocorrencia_titulo = ctk.CTkEntry(main_occurrence_frame, placeholder_text="Título Resumido da Ocorrência (ex: Falha em chamadas para TIM)",
                                                    fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                    border_color="gray40")
        self.entry_ocorrencia_titulo.pack(fill="x", padx=10, pady=(0, 10))

        self.test_entry_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.test_entry_frame.grid_columnconfigure(3, weight=0)
        ctk.CTkLabel(self.test_entry_frame, text="2. Adicionar Testes de Ligação (Evidências)",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(10, 10))
        
        ctk.CTkLabel(self.test_entry_frame, text="Horário do Teste (HHMM)", text_color=self.controller.TEXT_COLOR).grid(row=1, column=0, sticky="w", padx=10, pady=(5, 0))
        self.entry_teste_horario = ctk.CTkEntry(self.test_entry_frame, placeholder_text="Ex: 1605",
                                                fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                border_color="gray40")
        self.entry_teste_horario.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.entry_teste_horario.bind("<KeyRelease>", self._validate_horario_live)

        ctk.CTkLabel(self.test_entry_frame, text="Número de Origem (A)", text_color=self.controller.TEXT_COLOR).grid(row=1, column=1, sticky="w", padx=10, pady=(5, 0))
        self.entry_teste_num_a = ctk.CTkEntry(self.test_entry_frame, placeholder_text="Ex: 11987654321",
                                              fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                              border_color="gray40")
        self.entry_teste_num_a.grid(row=2, column=1, padx=10, pady=(0, 10), sticky="ew")
        
        ctk.CTkLabel(self.test_entry_frame, text="Operadora de Origem (A)", text_color=self.controller.TEXT_COLOR).grid(row=1, column=2, sticky="w", padx=10, pady=(5, 0))
        self.entry_op_a = AutocompleteEntry(self.test_entry_frame, placeholder_text="Digite para buscar...",
                                            fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                            border_color="gray40")
        self.entry_op_a.grid(row=2, column=2, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(self.test_entry_frame, text="Número de Destino (B)", text_color=self.controller.TEXT_COLOR).grid(row=3, column=0, sticky="w", padx=10, pady=(5, 0))
        self.entry_teste_num_b = ctk.CTkEntry(self.test_entry_frame, placeholder_text="Ex: 21912345678",
                                              fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                              border_color="gray40")
        self.entry_teste_num_b.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(self.test_entry_frame, text="Operadora de Destino (B)", text_color=self.controller.TEXT_COLOR).grid(row=3, column=1, sticky="w", padx=10, pady=(5, 0))
        self.entry_op_b = AutocompleteEntry(self.test_entry_frame, placeholder_text="Digite para buscar...",
                                            fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                            border_color="gray40")
        self.entry_op_b.grid(row=4, column=1, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(self.test_entry_frame, text="Status da Chamada", text_color=self.controller.TEXT_COLOR).grid(row=3, column=2, sticky="w", padx=10, pady=(5, 0))
        self.combo_teste_status = ctk.CTkComboBox(self.test_entry_frame, values=["FALHA", "MUDA", "NÃO COMPLETA", "COMPLETOU COM SUCESSO"],
                                                  fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                  border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                  button_hover_color=self.controller.ACCENT_COLOR)
        self.combo_teste_status.grid(row=4, column=2, padx=10, pady=(0, 10), sticky="ew")
        
        ctk.CTkLabel(self.test_entry_frame, text="Descrição do Problema (obrigatório)", text_color=self.controller.TEXT_COLOR).grid(row=5, column=0, columnspan=3, sticky="w", padx=10, pady=(5, 0))
        self.entry_teste_obs = ctk.CTkEntry(self.test_entry_frame, placeholder_text="Descreva o problema detalhadamente (ex: a ligação caiu após 5 segundos)",
                                            fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                            border_color="gray40")
        self.entry_teste_obs.grid(row=6, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")
        
        self.add_test_button = ctk.CTkButton(self.test_entry_frame, text="+ Adicionar Teste", command=self.add_or_update_test, height=36,
                                             fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                             hover_color=self.controller.ACCENT_COLOR)
        self.add_test_button.grid(row=2, column=3, rowspan=5, padx=10, pady=(0, 10), sticky="nsew")

        self.test_list_label = ctk.CTkLabel(test_list_frame, text="3. Testes a Serem Registrados",
                                            font=ctk.CTkFont(size=16, weight="bold"),
                                            text_color=self.controller.TEXT_COLOR)
        self.test_list_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        self.scrollable_test_list = ctk.CTkScrollableFrame(test_list_frame, label_text="Nenhum teste adicionado ainda.",
                                                          fg_color="gray10", label_text_color=self.controller.TEXT_COLOR)
        self.scrollable_test_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        self.back_button = ctk.CTkButton(final_buttons_frame, text="Voltar ao Menu", command=lambda: self.controller.show_frame("MainMenuView"),
                                         fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                                         hover_color=self.controller.GRAY_HOVER_COLOR)
        self.back_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.submit_button = ctk.CTkButton(final_buttons_frame, text="Registrar Ocorrência Completa", command=self.submit, height=40,
                                           fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                           hover_color=self.controller.ACCENT_COLOR)
        self.submit_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        self.horario_valido = True
        self.default_border_color = self.entry_teste_horario.cget("border_color")

        self.entry_teste_num_a.bind("<FocusOut>", lambda event: self._validate_phone_number(self.entry_teste_num_a))
        self.entry_teste_num_b.bind("<FocusOut>", lambda event: self._validate_phone_number(self.entry_teste_num_b))
        self.entry_teste_obs.bind("<FocusOut>", lambda event: self._validate_required_field(self.entry_teste_obs)) # Added validation for obs
        self.entry_op_a.bind("<FocusOut>", lambda event: self._validate_required_field(self.entry_op_a)) # Added validation for op_a
        self.entry_op_b.bind("<FocusOut>", lambda event: self._validate_required_field(self.entry_op_b)) # Added validation for op_b
        self.combo_teste_status.configure(command=lambda choice: self._validate_required_field(self.combo_teste_status)) # Added validation for status combo

    def _validate_required_field(self, widget):
        """Valida se um campo (Entry/ComboBox/Textbox) não está vazio."""
        content = ""
        if isinstance(widget, ctk.CTkTextbox):
            content = widget.get("1.0", "end-1c")
        else:
            content = widget.get()

        if not content.strip():
            widget.configure(border_color="red")
            return False
        else:
            widget.configure(border_color=self.default_border_color)
            return True

    def _validate_phone_number(self, widget):
        phone_number = widget.get()
        # Permite campo vazio para validação, mas deve ser checado no add_or_update_test
        if not phone_number.strip():
            widget.configure(border_color=self.default_border_color)
            return True
            
        if not re.fullmatch(r'\d{11}', phone_number):
            widget.configure(border_color="red")
            # messagebox.showwarning("Formato Inválido", "O número de telefone deve conter 11 dígitos (apenas números, incluindo DDD).")
            return False
        else:
            widget.configure(border_color=self.default_border_color)
            return True

    def set_operator_suggestions(self, operators):
        self.entry_op_a.set_suggestions(operators)
        self.entry_op_b.set_suggestions(operators)

    def on_show(self):
        profile = self.controller.get_current_user_profile()
        main_group = profile.get("main_group")
        
        if main_group == 'PARTNER':
            self.test_list_label.configure(text="3. Testes a Serem Registrados (mínimo 3)")
        else:
            self.test_list_label.configure(text="3. Testes a Serem Registrados")

        self.controller.testes_adicionados = []
        self.controller.editing_index = None
        self.entry_ocorrencia_titulo.delete(0, 'end')
        self._clear_test_fields()
        self._update_test_display_list()
        self.add_test_button.configure(text="+ Adicionar Teste", fg_color=self.controller.PRIMARY_COLOR, hover_color=self.controller.ACCENT_COLOR)
        self.set_operator_suggestions(self.controller.operator_list)
        self.set_submitting_state(False)
        self.entry_ocorrencia_titulo.focus()

    def _clear_test_fields(self):
        self.entry_teste_horario.delete(0, 'end')
        self.entry_teste_num_a.delete(0, 'end')
        self.entry_teste_num_b.delete(0, 'end')
        self.entry_teste_obs.delete(0, 'end')
        self.entry_op_a.delete(0, 'end')
        self.entry_op_b.delete(0, 'end')
        self.combo_teste_status.set("")
        
        self.horario_valido = True
        self.add_test_button.configure(state="normal")
        self.entry_teste_horario.configure(border_color=self.default_border_color)
        self.entry_teste_num_a.configure(border_color=self.default_border_color)
        self.entry_teste_num_b.configure(border_color=self.default_border_color)
        self.entry_teste_obs.configure(border_color=self.default_border_color)
        self.entry_op_a.configure(border_color=self.default_border_color)
        self.entry_op_b.configure(border_color=self.default_border_color)
        self.combo_teste_status.configure(border_color=self.default_border_color)
        # --- ALTERAÇÃO AQUI: Remove o destaque ao limpar ---
        self.test_entry_frame.configure(border_width=0)

    def add_or_update_test(self):
        # Re-validar todos os campos do teste antes de adicionar/atualizar
        is_horario_valid = self._validate_horario_live()
        is_num_a_valid = self._validate_phone_number(self.entry_teste_num_a)
        is_op_a_valid = self._validate_required_field(self.entry_op_a)
        is_num_b_valid = self._validate_phone_number(self.entry_teste_num_b)
        is_op_b_valid = self._validate_required_field(self.entry_op_b)
        is_status_valid = self._validate_required_field(self.combo_teste_status)
        is_obs_valid = self._validate_required_field(self.entry_teste_obs)

        if not all([is_horario_valid, is_num_a_valid, is_op_a_valid, is_num_b_valid, is_op_b_valid, is_status_valid, is_obs_valid]):
            messagebox.showerror("Erro de Validação", "Todos os campos do teste são obrigatórios e devem estar corretos. Por favor, corrija os campos destacados em vermelho.")
            return

        horario = self.entry_teste_horario.get().upper()
        num_a = self.entry_teste_num_a.get().upper()
        op_a = self.entry_op_a.get().upper()
        num_b = self.entry_teste_num_b.get().upper()
        op_b = self.entry_op_b.get().upper()
        status = self.combo_teste_status.get().upper()
        obs = self.entry_teste_obs.get().upper()

        teste_data = {"horario": horario, "num_a": num_a, "op_a": op_a,
                      "num_b": num_b, "op_b": op_b, "status": status, "obs": obs}
        
        if self.controller.editing_index is None and teste_data in self.controller.testes_adicionados:
            messagebox.showwarning("Teste Duplicado", "Este teste exato já foi adicionado à lista.")
            return

        if self.controller.editing_index is not None:
            self.controller.testes_adicionados[self.controller.editing_index] = teste_data
            self.controller.editing_index = None
            self.add_test_button.configure(text="+ Adicionar Teste",
                                           fg_color=self.controller.PRIMARY_COLOR,
                                           hover_color=self.controller.ACCENT_COLOR)
        else:
            self.controller.testes_adicionados.append(teste_data)

        self._clear_test_fields()
        self._update_test_display_list()

    def _update_test_display_list(self):
        for widget in self.scrollable_test_list.winfo_children():
            widget.destroy()

        if not self.controller.testes_adicionados:
            self.scrollable_test_list.configure(label_text="Nenhum teste adicionado ainda.",
                                                label_text_color=self.controller.TEXT_COLOR)
            return

        self.scrollable_test_list.configure(label_text="", label_text_color=self.controller.TEXT_COLOR)
        for index, teste in enumerate(self.controller.testes_adicionados):
            card_frame = ctk.CTkFrame(self.scrollable_test_list, fg_color="gray20") # Fundo dos cards
            card_frame.pack(fill="x", pady=5, padx=5)
            card_frame.grid_columnconfigure(0, weight=1)

            info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
            de_para_text = f"De: {teste['num_a']} ({teste['op_a']})  ->  Para: {teste['num_b']} ({teste['op_b']})"
            ctk.CTkLabel(info_frame, text=de_para_text, anchor="w",
                         text_color=self.controller.TEXT_COLOR).pack(fill="x")
            status_text = f"Horário: {teste['horario']}  |  Status: {teste['status']}"
            ctk.CTkLabel(info_frame, text=status_text, anchor="w", text_color="gray60").pack(fill="x")
            if teste['obs']:
                ctk.CTkLabel(info_frame, text=f"Descrição: {teste['obs']}", anchor="w",
                             font=ctk.CTkFont(slant="italic"), text_color="gray70").pack(fill="x")

            button_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            button_frame.grid(row=0, column=1, padx=(0, 10), pady=5)
            edit_button = ctk.CTkButton(button_frame, text="Editar", width=60,
                                        command=partial(self.edit_test, index),
                                        fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                        hover_color=self.controller.ACCENT_COLOR)
            edit_button.pack(side="left", padx=(0, 5))
            delete_button = ctk.CTkButton(button_frame, text="Excluir", width=60,
                                          fg_color=self.controller.DANGER_COLOR, text_color=self.controller.TEXT_COLOR,
                                          hover_color=self.controller.DANGER_HOVER_COLOR,
                                          command=partial(self.delete_test, index))
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
        self.add_test_button.configure(text="✔ Atualizar Teste",
                                       fg_color="green", hover_color="darkgreen") # Cor de sucesso para o botão
        # --- ALTERAÇÃO AQUI: Adiciona o destaque visual ---
        self.test_entry_frame.configure(border_color="green", border_width=2)

    def submit(self):
        title = self.entry_ocorrencia_titulo.get().upper()
        # Validação do título da ocorrência
        if not title.strip():
            messagebox.showwarning("Campo Obrigatório", "O título da ocorrência é obrigatório.")
            self.entry_ocorrencia_titulo.configure(border_color="red")
            return
        else:
            self.entry_ocorrencia_titulo.configure(border_color=self.default_border_color)

        # Validação de que há pelo menos 1 teste adicionado (e 3 para Parceiros)
        if not self.controller.testes_adicionados:
            messagebox.showwarning("Testes Obrigatórios", "É necessário adicionar pelo menos um teste para registrar a ocorrência.")
            return

        profile = self.controller.get_current_user_profile()
        main_group = profile.get("main_group")
        if main_group == 'PARTNER' and len(self.controller.testes_adicionados) < 3:
            messagebox.showwarning("Validação Falhou", "Para o perfil de Parceiro, é necessário adicionar pelo menos 3 testes.")
            return

        self.controller.submit_full_occurrence(title)

    def set_submitting_state(self, is_submitting):
        if is_submitting:
            self.submit_button.configure(state="disabled", text="A Enviar...")
        else:
            self.submit_button.configure(state="normal", text="Registrar Ocorrência Completa")

    def _validate_horario_live(self, event=None):
        horario_str = self.entry_teste_horario.get()
        
        if not horario_str:
            self.horario_valido = True
            self.entry_teste_horario.configure(border_color=self.default_border_color)
            # A ativação/desativação do botão de adicionar teste depende de todas as validações de campo
            # então não vamos habilitar/desabilitar aqui isoladamente
            return True # Retorna True para não bloquear outras validações apenas por estar vazio

        digits = "".join(filter(str.isdigit, horario_str))
        is_error = False

        if not digits.isdigit() or len(digits) > 4:
            is_error = True
        
        elif len(digits) == 4:
            try:
                hora = int(digits[0:2])
                minuto = int(digits[2:4])
                if not (0 <= hora <= 23 and 0 <= minuto <= 59):
                    is_error = True
                else:
                    formatted_time = f"{hora:02d}:{minuto:02d}"
                    if self.entry_teste_horario.get() != formatted_time:
                        cursor_pos = self.entry_teste_horario.index(ctk.INSERT)
                        self.entry_teste_horario.delete(0, 'end')
                        self.entry_teste_horario.insert(0, formatted_time)
                        self.entry_teste_horario.icursor(cursor_pos)
            except (ValueError, IndexError):
                is_error = True
        
        if is_error:
            self.horario_valido = False
            self.entry_teste_horario.configure(border_color="red")
            return False
        else:
            self.horario_valido = True
            self.entry_teste_horario.configure(border_color=self.default_border_color)
            return True

