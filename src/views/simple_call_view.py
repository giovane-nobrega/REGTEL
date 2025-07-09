import customtkinter as ctk


class SimpleCallView(ctk.CTkFrame):
    """Tela para o registro simplificado de chamadas (Prefeitura)."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ctk.CTkLabel(self, text="Registrar Ocorrência de Chamada (Simplificado)",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))

        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=20, pady=10)
        form_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form_frame, text="Número de Origem:").grid(
            row=0, column=0, padx=10, pady=10, sticky="w")
        self.entry_num_origem = ctk.CTkEntry(
            form_frame, placeholder_text="Ex: (67) 99999-1234")
        self.entry_num_origem.grid(
            row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Número de Destino:").grid(
            row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_num_destino = ctk.CTkEntry(
            form_frame, placeholder_text="Ex: (67) 3421-5678")
        self.entry_num_destino.grid(
            row=1, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Descrição do Problema:").grid(
            row=2, column=0, padx=10, pady=10, sticky="nw")
        self.description_textbox = ctk.CTkTextbox(form_frame, height=150)
        self.description_textbox.grid(
            row=2, column=1, padx=10, pady=10, sticky="ew")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(10, 0))
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.back_button = ctk.CTkButton(button_frame, text="Voltar ao Menu", command=lambda: self.controller.show_frame(
            "MainMenuView"), fg_color="gray50", hover_color="gray40")
        self.back_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.submit_button = ctk.CTkButton(
            button_frame, text="Registrar Ocorrência", command=self.submit, height=40)
        self.submit_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def on_show(self):
        """Limpa o formulário sempre que a tela é exibida."""
        self.entry_num_origem.delete(0, "end")
        self.entry_num_destino.delete(0, "end")
        self.description_textbox.delete("1.0", "end")
        self.set_submitting_state(False)

    def submit(self):
        """Chama o controlador para submeter a ocorrência."""
        # ALTERAÇÃO AQUI: Convertendo todos os campos para maiúsculas
        form_data = {
            "origem": self.entry_num_origem.get().upper(),
            "destino": self.entry_num_destino.get().upper(),
            "descricao": self.description_textbox.get("1.0", "end-1c").upper()
        }
        self.controller.submit_simple_call_occurrence(form_data)


    def set_submitting_state(self, is_submitting):
        """Ativa/desativa os botões durante o envio."""
        if is_submitting:
            self.submit_button.configure(state="disabled", text="Enviando...")
        else:
            self.submit_button.configure(
                state="normal", text="Registrar Ocorrência")
