# ==============================================================================
# ARQUIVO: src/views/management/admin_dashboard_view.py
# ==============================================================================

import customtkinter as ctk
import threading

class AdminDashboardView(ctk.CTkFrame):
    """ Dashboard de gestão para administradores. """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(fg_color=controller.BASE_COLOR)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Dashboard de Gestão", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        cards_container.grid_columnconfigure(0, weight=1)

        self.pending_occurrences_card = self._create_card(cards_container, "Ocorrências Pendentes", "...", 0, lambda: controller.show_frame("HistoryView", from_view="AdminDashboardView", mode="pending"))
        self.pending_access_card = self._create_card(cards_container, "Solicitações de Acesso", "...", 1, lambda: controller.show_frame("AccessManagementView"))
        self.active_users_card = self._create_card(cards_container, "Usuários Ativos", "...", 2, lambda: controller.show_frame("UserManagementView"))

        ctk.CTkButton(self, text="Voltar ao Menu", command=lambda: controller.show_frame("MainMenuView"), height=40).grid(row=2, column=0, pady=10, padx=20, sticky="ew")

    def _create_card(self, parent, title, value, row, command):
        """ Cria um card de informação para o dashboard. """
        card_frame = ctk.CTkFrame(parent, fg_color="gray15", corner_radius=10)
        card_frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
        card_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(card_frame, text=title, font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=(10, 5))
        value_label = ctk.CTkLabel(card_frame, text=value, font=ctk.CTkFont(size=28, weight="bold"), text_color=self.controller.ACCENT_COLOR)
        value_label.grid(row=1, column=0, pady=5)
        ctk.CTkButton(card_frame, text="Ver Detalhes", command=command).grid(row=2, column=0, pady=(5, 10), padx=10, sticky="ew")
        
        return value_label

    def on_show(self):
        """ Carrega os dados para os cards. """
        threading.Thread(target=self._load_card_data, daemon=True).start()

    def _load_card_data(self):
        """ Busca os dados para os cards em segundo plano. """
        try:
            pending_req_count = len(self.controller.get_pending_requests())
            self.after(0, lambda: self.pending_access_card.configure(text=str(pending_req_count)))
            
            active_users_count = len([u for u in self.controller.get_all_users(True) if u.get('status') == 'approved'])
            self.after(0, lambda: self.active_users_card.configure(text=str(active_users_count)))
            
            # Usa o método específico para admin que retorna todas as ocorrências
            all_occurrences = self.controller.get_all_occurrences_for_admin(True)
            pending_occ_count = len([o for o in all_occurrences if o.get('Status') not in ['RESOLVIDO', 'CANCELADO']])
            self.after(0, lambda: self.pending_occurrences_card.configure(text=str(pending_occ_count)))
        except Exception as e:
            print(f"Erro ao carregar dados do dashboard: {e}")
            # Define valores padrão em caso de erro
            self.after(0, lambda: self.pending_access_card.configure(text="0"))
            self.after(0, lambda: self.active_users_card.configure(text="0"))
            self.after(0, lambda: self.pending_occurrences_card.configure(text="0"))