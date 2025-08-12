# ==============================================================================
# FICHEIRO: src/views/notification_popup.py
# DESCRIÇÃO: Implementa um pop-up de notificação temporário e não-bloqueante.
#            (VERSÃO CORRIGIDA PARA DEPENDÊNCIA DE CORES)
# ==============================================================================

import customtkinter as ctk

class NotificationPopup(ctk.CTkToplevel):
    """
    Um pop-up de notificação temporário e não-bloqueante que desaparece após um tempo.
    Pode ser usado para mensagens de sucesso ou informação.
    """
    def __init__(self, master, message, type="info", duration_ms=3000, 
                 bg_color_success="green", text_color_success="white",
                 bg_color_warning="orange", text_color_warning="white",
                 bg_color_error="red", text_color_error="white",
                 bg_color_info="#0A0E1A", text_color_info="#FFFFFF"): # Cores padrão
        super().__init__(master)
        self.master = master
        self.overrideredirect(True) # Remove a borda da janela e os botões de fechar

        self.wm_attributes("-topmost", True) # Garante que a janela fique no topo
        self.wm_attributes("-alpha", 0.0) # Começa invisível para fade-in

        # Definir a cor de fundo e do texto com base no tipo de notificação
        # Agora as cores são passadas como argumentos, eliminando a dependência do controller
        bg_color = bg_color_info
        text_color = text_color_info

        if type == "success":
            bg_color = bg_color_success
            text_color = text_color_success
        elif type == "warning":
            bg_color = bg_color_warning
            text_color = text_color_warning
        elif type == "error":
            bg_color = bg_color_error
            text_color = text_color_error
        
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
        # Correção: Usar wm_attributes em vez de winfo_attributes
        alpha = self.wm_attributes("-alpha")
        if float(alpha) < 0.9: # Converter para float para comparação
            alpha = float(alpha) + 0.1
            self.wm_attributes("-alpha", alpha)
            self.after(50, self.fade_in)
        else:
            self.wm_attributes("-alpha", 0.9) # Garante que atinge a opacidade total

    def fade_out(self):
        """Faz a notificação desaparecer gradualmente."""
        # Correção: Usar wm_attributes em vez de winfo_attributes
        alpha = self.wm_attributes("-alpha")
        if float(alpha) > 0: # Converter para float para comparação
            alpha = float(alpha) - 0.1 # Reduz a transparência em 0.1
            self.wm_attributes("-alpha", alpha)
            self.after(50, self.fade_out) # Repete a cada 50ms
        else:
            self.destroy() # Destrói a janela quando a transparência for 0
