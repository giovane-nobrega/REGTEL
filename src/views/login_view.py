import customtkinter as ctk

class LoginView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Configuração da Responsividade ---
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)

        self.login_label = ctk.CTkLabel(center_frame, text="Plataforma de Registro de Ocorrências", font=ctk.CTkFont(size=24, weight="bold"))
        self.login_label.pack(pady=(50, 20), padx=20)
        
        self.login_button = ctk.CTkButton(center_frame, text="Fazer Login com Google", command=self.controller.perform_login, height=50, width=300, font=ctk.CTkFont(size=16))
        self.login_button.pack(pady=20, padx=50)

    def set_loading_state(self, message):
        self.login_label.configure(text=message)
        self.login_button.configure(state="disabled")
        self.update_idletasks()

    def set_default_state(self):
        self.login_label.configure(text="Plataforma de Registro de Ocorrências")
        self.login_button.configure(state="normal", text="Fazer Login com Google")
