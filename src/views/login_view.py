# ==============================================================================
# FICHEIRO: src/views/login_view.py
# DESCRIÇÃO: Contém a classe de interface para a tela inicial de login
#            da aplicação. (ATUALIZADA COM CORES, ESTILO, PROGRASSO E ÍCONE)
# ==============================================================================

import customtkinter as ctk
# Importar módulos para imagem se for usar ícone de imagem (ex: Google icon)
# from PIL import Image, ImageTk 
import os # Para carregamento de ícones se forem ficheiros

class LoginView(ctk.CTkFrame):
    """
    Tela inicial que solicita ao utilizador que faça login com a sua conta Google.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0)

        # --- Widgets da Interface ---
        self.login_label = ctk.CTkLabel(
            center_frame,
            text="Plataforma de Registro de Ocorrências",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.controller.TEXT_COLOR
        )
        self.login_label.pack(pady=(50, 20), padx=20)
        
        # Carregar ícone do Google (exemplo: usar um emoji para simplificar ou um ficheiro PNG/SVG)
        # Para ícone de ficheiro:
        # if hasattr(sys, '_MEIPASS'):
        #     base_path = sys._MEIPASS
        # else:
        #     base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        # google_icon_path = os.path.join(base_path, 'assets', 'google_icon.png') # Assumindo um subdiretório 'assets'
        # self.google_icon = ctk.CTkImage(Image.open(google_icon_path), size=(20, 20)) # Ajuste o tamanho conforme necessário

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
            # Se for usar imagem: image=self.google_icon, compound="left"
            compound="left", # Alinha o texto com o ícone (neste caso, o emoji)
            text_color_disabled="gray" # Cor do texto quando desativado
        )
        self.login_button.pack(pady=20, padx=50)

        # Barra de progresso para indicar atividade
        self.loading_progressbar = ctk.CTkProgressBar(
            center_frame,
            orientation="horizontal",
            mode="indeterminate", # Modo indeterminado para animação contínua
            height=8,
            width=300,
            fg_color="gray30",
            progress_color=self.controller.ACCENT_COLOR # Cor de progresso
        )
        # Inicialmente oculta
        # self.loading_progressbar.pack_forget() # Isso será feito pelo set_default_state
        
        self.set_default_state() # Define o estado inicial

    def set_loading_state(self, message):
        """
        Atualiza a UI para um estado de 'carregamento', desativando o botão
        e mostrando uma mensagem de status e a barra de progresso animada.
        """
        self.login_label.configure(text=message)
        self.login_button.configure(state="disabled")
        self.loading_progressbar.pack(pady=(10, 0)) # Adiciona padding para separação
        self.loading_progressbar.start() # Inicia a animação da barra de progresso
        self.update_idletasks()  # Força a atualização da UI

    def set_default_state(self):
        """
        Restaura a UI para o seu estado inicial, reativando o botão
        e mostrando a mensagem padrão, e parando/ocultando a barra de progresso.
        """
        self.login_label.configure(text="Plataforma de Registro de Ocorrências")
        self.login_button.configure(state="normal", text="Fazer Login com Google")
        self.loading_progressbar.stop() # Para a animação da barra de progresso
        self.loading_progressbar.pack_forget() # Oculta a barra de progresso
