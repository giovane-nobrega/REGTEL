import customtkinter as ctk
import threading

class HistoryView(ctk.CTkFrame):
    """Tela para exibir o histórico de ocorrências do usuário."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.title_label = ctk.CTkLabel(self, text="Meu Histórico de Ocorrências", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(10, 10))
        
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Buscar por ID, Título, Data, E-mail...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.search_button = ctk.CTkButton(search_frame, text="Buscar", width=100, command=self.load_history)
        self.search_button.pack(side="left")

        self.history_scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Carregando histórico...")
        self.history_scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        back_button = ctk.CTkButton(self, text="Voltar ao Menu", command=lambda: controller.show_frame("MainMenuView"), fg_color="gray50", hover_color="gray40")
        back_button.pack(pady=(0, 10), padx=20, fill="x")

    def on_show(self):
        """Método chamado pelo controlador sempre que esta tela é exibida."""
        self.search_entry.delete(0, "end")
        self.load_history()

    def load_history(self):
        """Inicia o carregamento do histórico em segundo plano, usando o termo de busca."""
        search_term = self.search_entry.get()
        self.history_scrollable_frame.configure(label_text="Carregando...")
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self._load_history_thread, args=(search_term,), daemon=True).start()

    def _load_history_thread(self, search_term):
        """Busca os dados e agenda a atualização da UI."""
        user_role = self.controller.get_current_user_role()
        if user_role == 'admin':
            # Admin busca em todas as ocorrências
            occurrences = self.controller.get_all_occurrences(search_term=search_term)
        else:
            # Outros usuários buscam apenas nas suas
            occurrences = self.controller.get_user_occurrences(search_term)
        
        self.after(0, self._populate_history, occurrences, user_role)

    def _populate_history(self, occurrences, user_role):
        """Preenche a UI com o histórico."""
        if user_role == 'admin':
            self.title_label.configure(text="Histórico Geral de Ocorrências")
        else:
            self.title_label.configure(text="Meu Histórico de Ocorrências")

        if not occurrences:
            self.history_scrollable_frame.configure(label_text="Nenhuma ocorrência encontrada.")
            return
            
        self.history_scrollable_frame.configure(label_text="")
        for item in occurrences:
            card = ctk.CTkFrame(self.history_scrollable_frame)
            card.pack(fill="x", padx=5, pady=5)
            card.grid_columnconfigure(0, weight=1)
            card.grid_columnconfigure(1, weight=0)
            
            title = item.get('Título da Ocorrência', item.get('Tipo de Equipamento', 'N/A'))
            date = item.get('Data de Registro', 'N/A')
            status = item.get('Status', 'N/A')
            
            title_label = ctk.CTkLabel(card, text=f"ID: {item.get('ID', 'N/A')} - {title}", font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
            title_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 0))
            
            details_text = f"Registrado em: {date}"
            if user_role == 'admin':
                details_text += f" por: {item.get('Email do Registrador', 'N/A')}"

            details_label = ctk.CTkLabel(card, text=details_text, anchor="w", text_color="gray60")
            details_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0,5))
            
            status_label = ctk.CTkLabel(card, text=f"Status: {status}", anchor="e", font=ctk.CTkFont(weight="bold"))
            status_label.grid(row=1, column=1, sticky="e", padx=10, pady=(0,5))
