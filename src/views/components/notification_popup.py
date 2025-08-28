# ==============================================================================
# FICHEIRO: src/views/components/notification_popup.py
# DESCRIÇÃO: Implementa um pop-up de notificação temporário e não-bloqueante.
# DATA DA ATUALIZAÇÃO: 27/08/2025
# NOTAS: Ficheiro movido para a nova subpasta 'components'. Nenhuma alteração
#        de código foi necessária.
# ==============================================================================

import customtkinter as ctk
from builtins import super, float

class NotificationPopup(ctk.CTkToplevel):
    """
    Um pop-up de notificação temporário e não-bloqueante que desaparece após um tempo.
    """
    def __init__(self, master, message, type="info", duration_ms=3000, 
                 bg_color_success="green", text_color_success="white",
                 bg_color_warning="orange", text_color_warning="white",
                 bg_color_error="red", text_color_error="white",
                 bg_color_info="#0A0E1A", text_color_info="#FFFFFF"):
        super().__init__(master)
        self.master = master
        self.overrideredirect(True)

        self.wm_attributes("-topmost", True)
        self.wm_attributes("-alpha", 0.0)

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
        
        master_x = master.winfo_x()
        master_y = master.winfo_y()
        master_width = master.winfo_width()

        self.x = master_x + master_width - self.winfo_width() - 20
        self.y = master_y + 20
        
        self.geometry(f"+{self.x}+{self.y}")
        
        self.deiconify()
        self.fade_in()

        self.after(duration_ms, self.fade_out)

    def fade_in(self):
        """Faz a notificação aparecer gradualmente."""
        alpha = self.wm_attributes("-alpha")
        if float(alpha) < 0.9:
            alpha = float(alpha) + 0.1
            self.wm_attributes("-alpha", alpha)
            self.after(50, self.fade_in)
        else:
            self.wm_attributes("-alpha", 0.9)

    def fade_out(self):
        """Faz a notificação desaparecer gradualmente."""
        alpha = self.wm_attributes("-alpha")
        if float(alpha) > 0:
            alpha = float(alpha) - 0.1
            self.wm_attributes("-alpha", alpha)
            self.after(50, self.fade_out)
        else:
            self.destroy()
