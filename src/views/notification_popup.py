# ==============================================================================
# FICHEIRO: src/views/notification_popup.py
# DESCRIÇÃO: Implementa um pop-up de notificação temporário e não-bloqueante.
# ==============================================================================

import customtkinter as ctk

class NotificationPopup(ctk.CTkToplevel):
    """
    Um pop-up de notificação temporário e não-bloqueante que desaparece após um tempo.
    Pode ser usado para mensagens de sucesso ou informação.
    """
    def __init__(self, master, message, type="info", duration_ms=3000):
        super().__init__(master)
        self.master = master
        self.overrideredirect(True) # Remove a borda da janela e os botões de fechar

        self.wm_attributes("-topmost", True) # Garante que a janela fique no topo
        self.wm_attributes("-alpha", 0.0) # Começa invisível para fade-in

        # Acessar as cores do controller (App)
        self.controller = master # Master é a instância de App

        # Definir a cor de fundo e do texto com base no tipo de notificação
        bg_color = self.controller.BASE_COLOR # Cor padrão
        text_color = self.controller.TEXT_COLOR

        if type == "success":
            bg_color = "green" # Ou uma cor de sucesso definida no controller
            text_color = "white"
        elif type == "warning":
            bg_color = "orange"
            text_color = "white"
        elif type == "error":
            bg_color = "red"
            text_color = "white"
        # Para "info", usa as cores padrão definidas acima

        self.frame = ctk.CTkFrame(self, fg_color=bg_color, corner_radius=10)
        self.frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.label = ctk.CTkLabel(self.frame, text=message, font=ctk.CTkFont(size=14, weight="bold"), text_color=text_color)
        self.label.pack(padx=15, pady=10)

        self.update_idletasks()
        
        # Posicionar a notificação no canto superior direito da janela principal
        master_x = master.winfo_x()
        master_y = master.winfo_y()
        master_width = master.winfo_width()

        self.x = master_x + master_width - self.winfo_width() - 20 # 20px de padding
        self.y = master_y + 20 # 20px de padding
        
        self.geometry(f"+{self.x}+{self.y}")
        
        self.deiconify() # Mostra a janela
        self.fade_in() # Inicia a animação de fade-in

        self.after(duration_ms, self.fade_out)

    def fade_in(self):
        """Faz a notificação aparecer gradualmente."""
        alpha = self.winfo_attributes("-alpha")
        if alpha < 0.9: # Fade in até 0.9 de opacidade
            alpha += 0.1
            self.wm_attributes("-alpha", alpha)
            self.after(50, self.fade_in)
        else:
            self.wm_attributes("-alpha", 0.9) # Garante que atinge a opacidade total

    def fade_out(self):
        """Faz a notificação desaparecer gradualmente."""
        alpha = self.winfo_attributes("-alpha")
        if alpha > 0:
            alpha -= 0.1 # Reduz a transparência em 0.1
            self.wm_attributes("-alpha", alpha)
            self.after(50, self.fade_out) # Repete a cada 50ms
        else:
            self.destroy() # Destrói a janela quando a transparência for 0
