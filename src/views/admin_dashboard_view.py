# ==============================================================================
# ARQUIVO: src/views/admin_dashboard_view.py
# DESCRIÇÃO: Contém a classe de interface para o Dashboard de Gestão,
#            agora baseado em cards dinâmicos para uma visão geral rápida.
#            ATUALIZADO para navegar para as novas Views de gestão.
#            CORRIGIDO para usar 'grid()' consistentemente.
#            ATUALIZADO: Layout dos cards para formato de lista vertical.
# ==============================================================================

import customtkinter as ctk
from functools import partial
from tkinter import messagebox
import threading
from datetime import datetime
import re
from builtins import super, list, Exception, print, str, hasattr, len, any, ValueError, sum


class AdminDashboardView(ctk.CTkFrame):
    """
    Dashboard de gestão para administradores, organizado em cards dinâmicos.
    Proporciona uma visão geral rápida de métricas importantes e navegação para detalhes.
    """
    def __init__(self, parent, controller):
        """
        Inicializa o AdminDashboardView com um layout baseado em cards.
        :param parent: O widget pai.
        :param controller: A instância da classe App, que atua como controlador.
        """
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Dashboard de Gestão",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")

        self.cards_container_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_container_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        self.cards_container_frame.grid_columnconfigure(0, weight=1)
        self.cards_container_frame.grid_rowconfigure((0, 1, 2), weight=0) 

        self.pending_occurrences_card_label = self._create_dashboard_card(
            parent_frame=self.cards_container_frame,
            title="Ocorrências Pendentes",
            initial_value="...",
            row=0, column=0,
            pady=(0, 15), # pyright: ignore[reportArgumentType]
            command=lambda: self.controller.show_frame("HistoryView", from_view="AdminDashboardView", mode="pending")
        )

        self.pending_access_card_label = self._create_dashboard_card(
            parent_frame=self.cards_container_frame,
            title="Solicitações de Acesso",
            initial_value="...",
            row=1, column=0,
            pady=(0, 15), # pyright: ignore[reportArgumentType]
            command=lambda: self.controller.show_frame("AccessManagementView") 
        )

        self.active_users_card_label = self._create_dashboard_card(
            parent_frame=self.cards_container_frame,
            title="Usuários Ativos",
            initial_value="...",
            row=2, column=0,
            pady=(0, 15), # pyright: ignore[reportArgumentType]
            command=lambda: self.controller.show_frame("UserManagementView") 
        )

        back_button = ctk.CTkButton(self, text="Voltar ao Menu",
                                    command=lambda: self.controller.show_frame("MainMenuView"),
                                    fg_color=self.controller.GRAY_BUTTON_COLOR,
                                    text_color=self.controller.TEXT_COLOR,
                                    hover_color=self.controller.GRAY_HOVER_COLOR,
                                    height=40) 
        back_button.grid(row=2, column=0, pady=(0, 10), padx=20, sticky="ew")

    def _create_dashboard_card(self, parent_frame, title, initial_value, row, column, command=None, pady=10):
        """
        Cria um card padrão para o dashboard com título, valor dinâmico e um botão de ação.
        :param parent_frame: O frame pai onde o card será colocado.
        :param title: O título do card.
        :param initial_value: O valor inicial a ser exibido no card.
        :param row: A linha no grid do parent_frame.
        :param column: A coluna no grid do parent_frame.
        :param command: A função a ser chamada quando o botão do card é clicado.
        :param pady: Preenchimento vertical para o card.
        :return: O widget CTkLabel que exibe o valor, para que possa ser atualizado dinamicamente.
        """
        card_frame = ctk.CTkFrame(parent_frame, fg_color="gray15", corner_radius=10)
        card_frame.grid(row=row, column=column, padx=10, pady=pady, sticky="ew")
        card_frame.grid_columnconfigure(0, weight=1)
        card_frame.grid_rowconfigure(2, weight=0)

        ctk.CTkLabel(card_frame, text=title, font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, pady=(10, 5))
        
        value_label = ctk.CTkLabel(card_frame, text=initial_value, font=ctk.CTkFont(size=28, weight="bold"),
                                     text_color=self.controller.ACCENT_COLOR)
        value_label.grid(row=1, column=0, pady=5)

        if command:
            action_button = ctk.CTkButton(card_frame, text="Ver Detalhes", command=command,
                                          fg_color=self.controller.PRIMARY_COLOR,
                                          text_color=self.controller.TEXT_COLOR,
                                          hover_color=self.controller.ACCENT_COLOR)
            action_button.grid(row=2, column=0, pady=(5, 10), padx=10, sticky="ew")
        
        return value_label

    def on_show(self):
        """
        Chamado sempre que a tela AdminDashboardView é exibida.
        Carrega os dados para os cards dinâmicos.
        """
        print("DEBUG: AdminDashboardView exibida. Carregando dados para os cards...")
        self.update_idletasks()

        threading.Thread(target=self._load_pending_occurrences_count, daemon=True).start()
        threading.Thread(target=self._load_pending_access_requests_count, daemon=True).start()
        threading.Thread(target=self._load_active_users_count, daemon=True).start()
        print("DEBUG: Carregamento de dados para cards iniciado.")

    def _load_pending_occurrences_count(self):
        """
        Busca a contagem de ocorrências pendentes e atualiza o card correspondente.
        """
        print("DEBUG: Buscando contagem de ocorrências pendentes...")
        all_occurrences = self.controller.get_all_occurrences(force_refresh=True)
        pending_count = sum(1 for occ in all_occurrences if occ.get('Status', '').upper() in ['REGISTRADO', 'EM ANÁLISE', 'AGUARDANDO TERCEIROS', 'PARCIALMENTE RESOLVIDO'])
        self.after(0, lambda: self.pending_occurrences_card_label.configure(text=f"{pending_count}"))
        print(f"DEBUG: Ocorrências pendentes: {pending_count}")

    def _load_pending_access_requests_count(self):
        """
        Busca a contagem de solicitações de acesso pendentes e atualiza o card correspondente.
        """
        print("DEBUG: Buscando contagem de solicitações de acesso...")
        pending_requests = self.controller.get_pending_requests()
        self.after(0, lambda: self.pending_access_card_label.configure(text=f"{len(pending_requests)}"))
        print(f"DEBUG: Solicitações de acesso pendentes: {len(pending_requests)}")

    def _load_active_users_count(self):
        """
        Busca a contagem de usuários ativos (aprovados) e atualiza o card correspondente.
        """
        print("DEBUG: Buscando contagem de usuários ativos...")
        all_users = self.controller.get_all_users(force_refresh=True)
        active_count = sum(1 for user in all_users if user.get('status', '').upper() == 'APPROVED')
        self.after(0, lambda: self.active_users_card_label.configure(text=f"{active_count}"))
        print(f"DEBUG: Usuários ativos: {active_count}")

    def save_profile_changes(self):
        """
        Coleta as alterações de perfil dos usuários e as envia para o controlador para salvamento em lote.
        """
        messagebox.showinfo("Funcionalidade", "Esta função seria ativada a partir de uma tela de gestão de usuários mais detalhada.")
        print("DEBUG: save_profile_changes chamado (simulado).")

    def save_status_changes(self):
        """
        Salva as alterações de status das ocorrências que foram modificadas no dashboard.
        """
        messagebox.showinfo("Funcionalidade", "Esta função seria ativada a partir de uma tela de gestão de ocorrências mais detalhada.")
        print("DEBUG: save_status_changes chamado (simulado).")
