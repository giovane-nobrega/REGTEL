# ==============================================================================
# FICHEIRO: src/views/admin_dashboard_view.py
# DESCRIÇÃO: Contém a classe de interface para o Dashboard de Gestão,
#            agora baseado em cards dinâmicos para uma visão geral rápida.
#            ATUALIZADO para navegar para as novas Views de gestão.
# ==============================================================================

import customtkinter as ctk
from functools import partial
from tkinter import messagebox
import threading
from datetime import datetime
import re
# Importa built-ins explicitamente para satisfazer o Pylance
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

        # Configuração da cor de fundo da tela
        self.configure(fg_color=self.controller.BASE_COLOR)

        # Configuração de responsividade do grid principal
        self.grid_rowconfigure(1, weight=1)  # Linha para os cards
        self.grid_columnconfigure(0, weight=1) # Coluna principal

        # Título principal do dashboard
        ctk.CTkLabel(self, text="Dashboard de Gestão",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")

        # Frame para conter os cards dinâmicos
        self.cards_container_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_container_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Configura o grid do container de cards para ter 2 colunas e expandir
        self.cards_container_frame.grid_columnconfigure((0, 1), weight=1)
        self.cards_container_frame.grid_rowconfigure((0, 1), weight=1) # Duas linhas para 4 cards (se necessário)

        # --- Criação dos Cards Dinâmicos ---
        # Card de Ocorrências Pendentes
        self.pending_occurrences_card_label = self._create_dashboard_card(
            parent_frame=self.cards_container_frame,
            title="Ocorrências Pendentes",
            initial_value="...",
            row=0, column=0,
            command=lambda: self.controller.show_frame("HistoryView", from_view="AdminDashboardView")
        )

        # Card de Solicitações de Acesso Pendentes
        self.pending_access_card_label = self._create_dashboard_card(
            parent_frame=self.cards_container_frame,
            title="Solicitações de Acesso",
            initial_value="...",
            row=0, column=1,
            # AGORA NAVEGA PARA A NOVA TELA DE GERENCIAMENTO DE ACESSOS
            command=lambda: self.controller.show_frame("AccessManagementView") 
        )

        # Card de Utilizadores Ativos
        self.active_users_card_label = self._create_dashboard_card(
            parent_frame=self.cards_container_frame,
            title="Utilizadores Ativos",
            initial_value="...",
            row=1, column=0,
            # AGORA NAVEGA PARA A NOVA TELA DE GERENCIAMENTO DE USUÁRIOS
            command=lambda: self.controller.show_frame("UserManagementView") 
        )

        # Card para Navegar para o Histórico Completo
        self.full_history_card_label = self._create_dashboard_card(
            parent_frame=self.cards_container_frame,
            title="Ver Histórico Completo",
            initial_value="Ir para",
            row=1, column=1,
            command=lambda: self.controller.show_frame("HistoryView", from_view="AdminDashboardView")
        )

        # Botão para voltar ao menu principal (mantido na parte inferior)
        back_button = ctk.CTkButton(self, text="Voltar ao Menu",
                                    command=lambda: self.controller.show_frame("MainMenuView"),
                                    fg_color=self.controller.GRAY_BUTTON_COLOR,
                                    text_color=self.controller.TEXT_COLOR,
                                    hover_color=self.controller.GRAY_HOVER_COLOR)
        back_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

    def _create_dashboard_card(self, parent_frame, title, initial_value, row, column, command=None):
        """
        Cria um card padrão para o dashboard com título, valor dinâmico e um botão de ação.
        :param parent_frame: O frame pai onde o card será colocado.
        :param title: O título do card.
        :param initial_value: O valor inicial a ser exibido no card.
        :param row: A linha no grid do parent_frame.
        :param column: A coluna no grid do parent_frame.
        :param command: A função a ser chamada quando o botão do card é clicado.
        :return: O widget CTkLabel que exibe o valor, para que possa ser atualizado dinamicamente.
        """
        card_frame = ctk.CTkFrame(parent_frame, fg_color="gray15", corner_radius=10)
        card_frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")
        card_frame.grid_columnconfigure(0, weight=1) # Permite que o conteúdo do card se expanda
        card_frame.grid_rowconfigure(2, weight=0) # Adiciona uma linha para o botão

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
            # CORREÇÃO: Usar grid() em vez de pack() para o botão dentro do card_frame
            # E usar sticky="ew" para preencher a largura
            action_button.grid(row=2, column=0, pady=(5, 10), padx=10, sticky="ew")
        
        return value_label # Retorna o label para que seu texto possa ser atualizado

    def on_show(self):
        """
        Chamado sempre que a tela AdminDashboardView é exibida.
        Carrega os dados para os cards dinâmicos.
        """
        print("DEBUG: AdminDashboardView exibida. Carregando dados para os cards...")
        self.update_idletasks() # Força a atualização da UI para mostrar "..."

        # Inicia o carregamento de dados para cada card em threads separadas
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
        Busca a contagem de utilizadores ativos (aprovados) e atualiza o card correspondente.
        """
        print("DEBUG: Buscando contagem de utilizadores ativos...")
        all_users = self.controller.get_all_users(force_refresh=True)
        active_count = sum(1 for user in all_users if user.get('status', '').upper() == 'APPROVED')
        self.after(0, lambda: self.active_users_card_label.configure(text=f"{active_count}"))
        print(f"DEBUG: Utilizadores ativos: {active_count}")

    # --- Métodos de Salvamento (mantidos, mas acessados via navegação ou botões dedicados) ---
    # Estes métodos não são diretamente chamados pelos cards de resumo,
    # mas seriam chamados por uma tela de detalhe ou gestão específica.

    def save_profile_changes(self):
        """
        Coleta as alterações de perfil dos utilizadores e as envia para o controlador para salvamento em lote.
        Implementa lógica para garantir a consistência de main_group, sub_group e company.
        """
        # Esta lógica seria chamada de uma tela de "Gerenciar Usuários" mais detalhada.
        messagebox.showinfo("Funcionalidade", "Esta função seria ativada a partir de uma tela de gestão de utilizadores mais detalhada.")
        print("DEBUG: save_profile_changes chamado (simulado).")
        # Exemplo de como a lógica de salvamento seria:
        # changes = {}
        # # ... (lógica de coleta de mudanças dos widgets de edição) ...
        # if changes:
        #     self.controller.update_user_profile(changes)
        # else:
        #     messagebox.showinfo("Nenhuma Alteração", "Nenhum perfil foi alterado.")

    def save_status_changes(self):
        """
        Salva as alterações de status das ocorrências que foram modificadas no dashboard.
        """
        # Esta lógica seria chamada de uma tela de "Gerenciar Ocorrências" mais detalhada.
        messagebox.showinfo("Funcionalidade", "Esta função seria ativada a partir de uma tela de gestão de ocorrências mais detalhada.")
        print("DEBUG: save_status_changes chamado (simulado).")