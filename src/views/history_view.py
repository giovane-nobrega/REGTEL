import customtkinter as ctk
import threading

class HistoryView(ctk.CTkFrame):
    """Tela para exibir o histórico de ocorrências do utilizador."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ctk.CTkLabel(self, text="O Meu Histórico de Ocorrências", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 10))
        
        self.history_scrollable_frame = ctk.CTkScrollableFrame(self, label_text="A carregar histórico...")
        self.history_scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        refresh_button = ctk.CTkButton(button_frame, text="Atualizar Histórico", command=self.load_history)
        refresh_button.pack(side="left", padx=(0, 10))
        
        back_button = ctk.CTkButton(button_frame, text="Voltar ao Menu", command=lambda: controller.show_frame("MainMenuView"), fg_color="gray50", hover_color="gray40")
        back_button.pack(side="left")

    def on_show(self):
        """Método chamado pelo controlador sempre que esta tela é exibida."""
        self.load_history()

    def load_history(self):
        """Inicia o carregamento do histórico em segundo plano."""
        self.history_scrollable_frame.configure(label_text="A carregar...")
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self._load_history_thread, daemon=True).start()

    def _load_history_thread(self):
        """Busca os dados e agenda a atualização da UI."""
        occurrences = self.controller.get_user_occurrences()
        self.after(0, self._populate_history, occurrences)

    def _populate_history(self, occurrences):
        """Preenche a UI com o histórico do utilizador."""
        if not occurrences:
            self.history_scrollable_frame.configure(label_text="Nenhuma ocorrência registrada.")
            return
            
        self.history_scrollable_frame.configure(label_text="")
        for item in reversed(occurrences):
            card = ctk.CTkFrame(self.history_scrollable_frame)
            card.pack(fill="x", padx=5, pady=5)
            card.grid_columnconfigure(0, weight=1)
            card.grid_columnconfigure(1, weight=0)
            
            title = item.get('Título da Ocorrência', item.get('Tipo de Equipamento', 'N/A'))
            date = item.get('Data de Registro', 'N/A')
            status = item.get('Status', 'N/A')
            
            title_label = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
            title_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 0))
            
            details_label = ctk.CTkLabel(card, text=f"Registrado em: {date}", anchor="w", text_color="gray60")
            details_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0,5))
            
            status_label = ctk.CTkLabel(card, text=f"Status: {status}", anchor="e", font=ctk.CTkFont(weight="bold"))
            status_label.grid(row=1, column=1, sticky="e", padx=10, pady=(0,5))
