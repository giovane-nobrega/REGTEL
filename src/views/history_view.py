# ==============================================================================
# FICHEIRO: src/views/history_view.py
# DESCRIÇÃO: Contém a classe de interface para a tela de histórico de
#            ocorrências, que exibe os registos visíveis ao utilizador.
# ==============================================================================

import customtkinter as ctk
import threading
from functools import partial
import json

class HistoryView(ctk.CTkFrame):
    """
    Tela para exibir o histórico de ocorrências do utilizador.
    O conteúdo exibido é filtrado com base nas permissões do perfil do utilizador.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # --- Configuração da Responsividade ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # A área de scroll expande
        
        self.title_label = ctk.CTkLabel(self, text="Histórico de Ocorrências", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")
        
        # --- Frame de Pesquisa ---
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Buscar em todas as ocorrências visíveis...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.search_button = ctk.CTkButton(search_frame, text="Buscar", width=100, command=self.load_history)
        self.search_button.pack(side="left")

        # --- Frame de Scroll para a Lista de Ocorrências ---
        self.history_scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Carregando histórico...")
        self.history_scrollable_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        # --- Botão de Voltar ---
        back_button = ctk.CTkButton(self, text="Voltar ao Menu", command=lambda: controller.show_frame("MainMenuView"), fg_color="gray50", hover_color="gray40")
        back_button.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

    def on_show(self):
        """Chamado sempre que a tela é exibida."""
        self.search_entry.delete(0, "end")
        self.load_history()

    def load_history(self):
        """Inicia o carregamento do histórico numa thread separada."""
        search_term = self.search_entry.get()
        self.history_scrollable_frame.configure(label_text="Carregando...")
        # Limpa a lista antiga antes de carregar a nova
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self._load_history_thread, args=(search_term,), daemon=True).start()

    def _load_history_thread(self, search_term):
        """Busca os dados no serviço e depois chama a função de atualização da UI."""
        occurrences = self.controller.get_user_occurrences(search_term)
        user_profile = self.controller.get_current_user_profile()
        # Volta para a thread principal para atualizar a interface
        self.after(0, self._populate_history, occurrences, user_profile)

    def _populate_history(self, occurrences, user_profile):
        """Preenche a lista de scroll com os cards das ocorrências."""
        # Atualiza o título da página com base no perfil do utilizador
        main_group = user_profile.get("main_group")
        if main_group == '67_TELECOM' and user_profile.get("sub_group") in ['SUPER_ADMIN', 'ADMIN', 'MANAGER']:
            self.title_label.configure(text="Histórico Geral de Ocorrências")
        elif main_group in ['PARTNER', 'PREFEITURA']:
            company = user_profile.get("company", "N/A")
            self.title_label.configure(text=f"Histórico de Ocorrências: {company}")
        else:
            self.title_label.configure(text="Meu Histórico de Ocorrências")

        if not occurrences:
            self.history_scrollable_frame.configure(label_text="Nenhuma ocorrência encontrada.")
            return
            
        self.history_scrollable_frame.configure(label_text="")
        
        # Cria um card para cada ocorrência
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
            except (json.JSONDecodeError, TypeError):
                pass 
            
            open_button = ctk.CTkButton(
                card_frame, text="Abrir", width=80, command=partial(self.controller.show_occurrence_details, item_id)
            )
            open_button.grid(row=0, column=1, padx=10, pady=10, sticky="e")
