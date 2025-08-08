# ==============================================================================
# FICHEIRO: src/views/simple_call_view.py
# DESCRIÇÃO: Contém a classe de interface para o formulário de registo
#            simplificado de ocorrências de chamada, para a Prefeitura.
#            (VERSÃO COM VALIDAÇÃO PROATIVA)
# ==============================================================================
import customtkinter as ctk
from tkinter import messagebox
import re

class SimpleCallView(ctk.CTkFrame):
    """
    Tela para o registro simplificado de chamadas, utilizada por utilizadores
    do grupo Prefeitura, com validação proativa.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Configuração da Responsividade ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Registrar Ocorrência de Chamada (Simplificado)",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 20), sticky="ew")

        # --- Frame Principal do Formulário ---
        form_frame = ctk.CTkFrame(self)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_rowconfigure(2, weight=1) # Linha da descrição expande

        # --- Campos do Formulário ---
        ctk.CTkLabel(form_frame, text="Número de Origem:").grid(
            row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_num_origem = ctk.CTkEntry(
            form_frame, placeholder_text="Apenas 11 dígitos, ex: 67999991234")
        self.entry_num_origem.grid(
            row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Número de Destino:").grid(
            row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_num_destino = ctk.CTkEntry(
            form_frame, placeholder_text="Apenas 11 dígitos, ex: 6734215678")
        self.entry_num_destino.grid(
            row=1, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Descrição do Problema:").grid(
            row=2, column=0, padx=10, pady=10, sticky="nw")
        self.description_textbox = ctk.CTkTextbox(form_frame, height=150)
        self.description_textbox.grid(
            row=2, column=1, padx=10, pady=10, sticky="nsew")

        # --- Botões de Ação ---
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=20, pady=(10, 10), sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.back_button = ctk.CTkButton(button_frame, text="Voltar ao Menu", command=lambda: self.controller.show_frame(
            "MainMenuView"), fg_color="gray50", hover_color="gray40")
        self.back_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.submit_button = ctk.CTkButton(
            button_frame, text="Registrar Ocorrência", command=self.submit, height=40)
        self.submit_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # --- Configuração da Lógica de Validação ---
        self.default_border_color = self.entry_num_origem.cget("border_color")
        self.entry_num_origem.bind("<FocusOut>", lambda event: self._validate_phone_field(self.entry_num_origem))
        self.entry_num_destino.bind("<FocusOut>", lambda event: self._validate_phone_field(self.entry_num_destino))
        self.description_textbox.bind("<FocusOut>", lambda event: self._validate_required_field(self.description_textbox))


    def _validate_phone_field(self, widget):
        """Valida se um campo de telefone contém 11 dígitos numéricos."""
        phone_number = widget.get()
        # Se o campo estiver vazio, não consideramos um erro ainda (apenas na submissão)
        if not phone_number:
            widget.configure(border_color=self.default_border_color)
            return True

        if not re.fullmatch(r'\d{11}', phone_number):
            widget.configure(border_color="red")
            return False
        else:
            widget.configure(border_color=self.default_border_color)
            return True

    def _validate_required_field(self, widget):
        """Valida se um campo de texto (ou Textbox) não está vazio."""
        content = ""
        # CTkTextbox e CTkEntry têm métodos diferentes para obter todo o texto
        if isinstance(widget, ctk.CTkTextbox):
            content = widget.get("1.0", "end-1c")
        else:
            content = widget.get()

        if not content.strip(): # .strip() remove espaços em branco
            widget.configure(border_color="red")
            return False
        else:
            widget.configure(border_color=self.default_border_color)
            return True

    def on_show(self):
        """Limpa o formulário sempre que a tela é exibida."""
        self.entry_num_origem.delete(0, "end")
        self.entry_num_destino.delete(0, "end")
        self.description_textbox.delete("1.0", "end")
        
        # Restaura as bordas para o padrão
        self.entry_num_origem.configure(border_color=self.default_border_color)
        self.entry_num_destino.configure(border_color=self.default_border_color)
        self.description_textbox.configure(border_color=self.default_border_color)

        self.set_submitting_state(False)

    def submit(self):
        """Coleta os dados, VALIDA TUDO, e os envia para o controlador."""
        # Executa todas as validações novamente antes de submeter
        is_origem_valid = self._validate_phone_field(self.entry_num_origem)
        is_destino_valid = self._validate_phone_field(self.entry_num_destino)
        is_desc_valid = self._validate_required_field(self.description_textbox)

        if not all([is_origem_valid, is_destino_valid, is_desc_valid]):
            messagebox.showwarning("Campos Inválidos", "Por favor, corrija os campos destacados em vermelho antes de registrar a ocorrência.")
            return

        form_data = {
            "origem": self.entry_num_origem.get().upper(),
            "destino": self.entry_num_destino.get().upper(),
            "descricao": self.description_textbox.get("1.0", "end-1c").upper()
        }
        self.controller.submit_simple_call_occurrence(form_data)

    def set_submitting_state(self, is_submitting):
        """Ativa/desativa os botões durante o processo de envio."""
        if is_submitting:
            self.submit_button.configure(state="disabled", text="A Enviar...")
        else:
            self.submit_button.configure(
                state="normal", text="Registrar Ocorrência")
