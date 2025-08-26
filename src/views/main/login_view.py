# ==============================================================================
# ARQUIVO: src/views/login_view.py
# DESCRIÇÃO: Contém a classe de interface para a tela inicial de login
#            da aplicação. (ATUALIZADA COM CORES, ESTILO, PROGRESSO E ÍCONE)
# ==============================================================================

import customtkinter as ctk
import os

class LoginView(ctk.CTkFrame):
    """
    Tela inicial que solicita ao usuário que faça login com a sua conta Google.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)

        self.login_label = ctk.CTkLabel(
            center_frame,
            text="Plataforma de Registro de Ocorrências",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.controller.TEXT_COLOR
        )
        self.login_label.pack(pady=(50, 20), padx=20)
        
        self.login_button = ctk.CTkButton(
            center_frame,
            text="Fazer Login com Google",
            command=self.controller.perform_login,
            height=50,
            width=300,
            font=ctk.CTkFont(size=16),
            fg_color=self.controller.PRIMARY_COLOR,
            text_color=self.controller.TEXT_COLOR,
            hover_color=self.controller.ACCENT_COLOR,
            compound="left",
            text_color_disabled="gray"
        )
        self.login_button.pack(pady=20, padx=50)

        self.loading_progressbar = ctk.CTkProgressBar(
            center_frame,
            orientation="horizontal",
            mode="indeterminate",
            height=8,
            width=300,
            fg_color="gray30",
            progress_color=self.controller.ACCENT_COLOR
        )
        
        self.set_default_state()

    def set_loading_state(self, message):
        """
        Atualiza a UI para um estado de 'carregamento', desativando o botão
        e mostrando uma mensagem de status e a barra de progresso animada.
        """
        self.login_label.configure(text=message)
        self.login_button.configure(state="disabled")
        self.loading_progressbar.pack(pady=(10, 0))
        self.loading_progressbar.start()
        self.update_idletasks()

    def set_default_state(self):
        """
        Restaura a UI para o seu estado inicial, reativando o botão
        e mostrando a mensagem padrão, e parando/ocultando a barra de progresso.
        """
        self.login_label.configure(text="Plataforma de Registro de Ocorrências")
        self.login_button.configure(state="normal", text="Fazer Login com Google")
        self.loading_progressbar.stop()
        self.loading_progressbar.pack_forget()
