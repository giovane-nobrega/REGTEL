import customtkinter as ctk
import threading
from functools import partial
import json

class HistoryView(ctk.CTkFrame):
    """Tela para exibir o histórico de ocorrências do usuário."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text="Histórico de Ocorrências", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")
        
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Buscar em todas as ocorrências visíveis...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.search_button = ctk.CTkButton(search_frame, text="Buscar", width=100, command=self.load_history)
        self.search_button.pack(side="left")

        self.history_scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Carregando histórico...")
        self.history_scrollable_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        back_button = ctk.CTkButton(self, text="Voltar ao Menu", command=lambda: controller.show_frame("MainMenuView"), fg_color="gray50", hover_color="gray40")
        back_button.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

    def on_show(self):
        self.search_entry.delete(0, "end")
        self.load_history()

    def load_history(self):
        search_term = self.search_entry.get()
        self.history_scrollable_frame.configure(label_text="Carregando...")
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self._load_history_thread, args=(search_term,), daemon=True).start()

    def _load_history_thread(self, search_term):
        occurrences = self.controller.get_user_occurrences(search_term)
        user_role = self.controller.get_current_user_role()
        self.after(0, self._populate_history, occurrences, user_role)

    def _populate_history(self, occurrences, user_role):
        if user_role in ['admin', 'telecom_user']:
            self.title_label.configure(text="Histórico Geral de Ocorrências")
        elif user_role == 'prefeitura':
            self.title_label.configure(text="Histórico de Ocorrências da Prefeitura")
        elif user_role == 'partner':
            self.title_label.configure(text="Histórico de Ocorrências da Empresa")
        else:
            self.title_label.configure(text="Meu Histórico de Ocorrências")

        if not occurrences:
            self.history_scrollable_frame.configure(label_text="Nenhuma ocorrência encontrada.")
            return
            
        self.history_scrollable_frame.configure(label_text="")
        for item in occurrences:
            item_id = item.get('ID', 'N/A')
            
            card_frame = ctk.CTkFrame(self.history_scrollable_frame)
            card_frame.pack(fill="x", padx=5, pady=5)
            card_frame.grid_columnconfigure(0, weight=1)

            info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            info_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            title = item.get('Título da Ocorrência', item.get('Tipo de Equipamento', 'N/A'))
            date = item.get('Data de Registro', 'N/A')
            status = item.get('Status', 'N/A')
            
            ctk.CTkLabel(info_frame, text=f"ID: {item_id} - {title}", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(anchor="w")
            
            details_text = f"Registrado por: {item.get('Nome do Registrador', 'N/A')} (@{item.get('Username do Registrador', 'N/A')}) em {date}"
            ctk.CTkLabel(info_frame, text=details_text, anchor="w", text_color="gray60").pack(anchor="w")
            
            ctk.CTkLabel(info_frame, text=f"Status: {status}", anchor="w", font=ctk.CTkFont(weight="bold")).pack(anchor="w")

            try:
                anexos = json.loads(item.get('Anexos', '[]'))
                if anexos:
                    ctk.CTkLabel(info_frame, text="(Contém Anexos)", text_color="cyan", font=ctk.CTkFont(slant="italic")).pack(anchor="w")
            except:
                pass 
            
            open_button = ctk.CTkButton(
                card_frame, text="Abrir", width=80, command=partial(self.controller.show_occurrence_details, item_id)
            )
            open_button.grid(row=0, column=1, padx=10, pady=10, sticky="e")
