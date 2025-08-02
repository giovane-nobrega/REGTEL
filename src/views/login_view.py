# ==============================================================================
# FICHEIRO: src/views/login_view.py
# DESCRIÇÃO: Contém a classe de interface para a tela inicial de login
#            da aplicação.
# ==============================================================================

import customtkinter as ctk

class LoginView(ctk.CTkFrame):
    """
    Tela inicial que solicita ao utilizador que faça login com a sua conta Google.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Configuração da Responsividade (centraliza o conteúdo) ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)

        # --- Widgets da Interface ---
        self.login_label = ctk.CTkLabel(
            center_frame,
            text="Plataforma de Registro de Ocorrências",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.login_label.pack(pady=(50, 20), padx=20)
        
        self.login_button = ctk.CTkButton(
            center_frame,
            text="Fazer Login com Google",
            command=self.controller.perform_login,
            height=50,
            width=300,
            font=ctk.CTkFont(size=16)
        )
        self.login_button.pack(pady=20, padx=50)

    def set_loading_state(self, message):
        """
        Atualiza a UI para um estado de 'carregamento', desativando o botão
        e mostrando uma mensagem de status.
        """
        self.login_label.configure(text=message)
        self.login_button.configure(state="disabled")
        self.update_idletasks()  # Força a atualização da UI

    def set_default_state(self):
        """
        Restaura a UI para o seu estado inicial, reativando o botão
        e mostrando a mensagem padrão.
        """
        self.login_label.configure(text="Plataforma de Registro de Ocorrências")
        self.login_button.configure(state="normal", text="Fazer Login com Google")
