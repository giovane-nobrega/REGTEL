# ==============================================================================
# FICHEIRO: src/views/admin_dashboard_view.py
# DESCRIÇÃO: Contém a classe de interface para o Dashboard de Gestão,
#            usado por administradores para gerir o sistema. (VERSÃO OTIMIZADA PARA CARREGAMENTO E LAYOUT)
# ==============================================================================

import customtkinter as ctk
from functools import partial
from tkinter import messagebox
import threading
import json
from datetime import datetime # Importação adicionada para validação de data
import re # Importação adicionada para validação de data

class AdminDashboardView(ctk.CTkFrame):
    """Dashboard de gestão para administradores, organizado em abas."""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.original_statuses = {}
        self.status_updaters = {}
        self.original_profiles = {}
        self.profile_updaters = {}

        self.partner_companies = ["M2 TELECOMUNICAÇÕES", "MDA FIBRA", "DISK SISTEMA TELECOM", "GMN TELECOM"]
        self.prefeitura_dept_list = ["SECRETARIA DE SAUDE", "SECRETARIA DE OBRAS", "DEPARTAMENTO DE TI", "GUARDA MUNICIPAL", "GABINETE DO PREFEITO", "OUTRO"]

        ctk.CTkLabel(self, text="Dashboard de Gestão",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")

        self.tabview = ctk.CTkTabview(self, command=self.on_tab_change,
                                      fg_color="gray15",
                                      segmented_button_fg_color=self.controller.PRIMARY_COLOR,
                                      segmented_button_selected_color=self.controller.ACCENT_COLOR,
                                      segmented_button_unselected_color="gray30",
                                      segmented_button_selected_hover_color=self.controller.ACCENT_COLOR,
                                      segmented_button_unselected_hover_color="gray25",
                                      text_color=self.controller.TEXT_COLOR)
        self.tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self.occurrences_tab = self.tabview.add("Ocorrências")
        self.access_tab = self.tabview.add("Gerenciar Acessos")
        self.users_tab = self.tabview.add("Gerenciar Usuários")

        self._occurrences_tab_initialized = False
        self._access_tab_initialized = False
        self._users_tab_initialized = False

        back_button = ctk.CTkButton(self, text="Voltar ao Menu",
                                    command=lambda: self.controller.show_frame("MainMenuView"),
                                    fg_color=self.controller.GRAY_BUTTON_COLOR,
                                    text_color=self.controller.TEXT_COLOR,
                                    hover_color=self.controller.GRAY_HOVER_COLOR)
        back_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

    def on_show(self):
        if not self._occurrences_tab_initialized:
            self.setup_occurrences_tab(self.occurrences_tab)
            self._occurrences_tab_initialized = True
            self.all_occurrences_frame.configure(label_text="Carregando ocorrências...")
            self.update_idletasks()
            self.load_all_occurrences(force_refresh=True)

        self.on_tab_change(self.tabview.get())

    def on_tab_change(self, selected_tab=None):
        if selected_tab is None:
            selected_tab = self.tabview.get()

        if selected_tab == "Ocorrências" and not self._occurrences_tab_initialized:
            self.setup_occurrences_tab(self.occurrences_tab)
            self._occurrences_tab_initialized = True
            self.all_occurrences_frame.configure(label_text="Carregando ocorrências...")
            self.update_idletasks()
            self.load_all_occurrences(force_refresh=True)
        elif selected_tab == "Gerenciar Acessos" and not self._access_tab_initialized:
            self.setup_access_tab(self.access_tab)
            self._access_tab_initialized = True
            self.pending_users_frame.configure(label_text="Carregando solicitações...")
            self.update_idletasks()
            self.load_access_requests()
        elif selected_tab == "Gerenciar Usuários" and not self._users_tab_initialized:
            self.setup_users_tab(self.users_tab)
            self._users_tab_initialized = True
            self.all_users_frame.configure(label_text="Carregando usuários...")
            self.update_idletasks()
            self.load_all_users(force_refresh=True)

    def setup_occurrences_tab(self, tab):
        ctk.CTkLabel(tab, text="Visão Geral de Todas as Ocorrências", text_color=self.controller.TEXT_COLOR).pack(pady=5)

        # Frame de Filtros e Busca (similar ao HistoryView)
        filter_frame = ctk.CTkFrame(tab, fg_color="gray15")
        filter_frame.pack(fill="x", pady=(0, 10), padx=5)
        filter_frame.grid_columnconfigure((1, 2, 3), weight=1) # Ajuste conforme layout

        ctk.CTkLabel(filter_frame, text="Painel de Filtros",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(5, 0))

        ctk.CTkLabel(filter_frame, text="Busca por Palavra-Chave:", text_color=self.controller.TEXT_COLOR).grid(row=1, column=0, sticky="w", padx=10, pady=(5, 0))
        self.search_entry_admin = ctk.CTkEntry(filter_frame, placeholder_text="ID, título, nome do usuário...",
                                               fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                               border_color="gray40")
        self.search_entry_admin.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

        ctk.CTkLabel(filter_frame, text="Filtrar por Status:", text_color=self.controller.TEXT_COLOR).grid(row=1, column=2, sticky="w", padx=10, pady=(5, 0))
        status_options = ["REGISTRADO", "EM ANÁLISE", "AGUARDANDO TERCEIROS", "PARCIALMENTE RESOLVIDO", "RESOLVIDO", "CANCELADO"]
        status_options_admin = ["TODOS"] + status_options # Inclui o novo status
        self.status_filter_admin = ctk.CTkComboBox(filter_frame, values=status_options_admin,
                                                   fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                   border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                   button_hover_color=self.controller.ACCENT_COLOR)
        self.status_filter_admin.grid(row=2, column=2, padx=10, pady=(0, 10), sticky="ew")
        self.status_filter_admin.set("TODOS")

        ctk.CTkLabel(filter_frame, text="Filtrar por Tipo:", text_color=self.controller.TEXT_COLOR).grid(row=1, column=3, sticky="w", padx=10, pady=(5, 0))
        type_options_admin = ["TODOS", "CHAMADA", "EQUIPAMENTO", "CHAMADA SIMPLES"]
        self.type_filter_admin = ctk.CTkComboBox(filter_frame, values=type_options_admin,
                                                 fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                 border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                 button_hover_color=self.controller.ACCENT_COLOR)
        self.type_filter_admin.grid(row=2, column=3, padx=10, pady=(0, 10), sticky="ew")
        self.type_filter_admin.set("TODOS")

        # Datas
        ctk.CTkLabel(filter_frame, text="Data de Início (DD-MM-AAAA):", text_color=self.controller.TEXT_COLOR).grid(row=3, column=0, sticky="w", padx=10, pady=(5, 0))
        self.start_date_entry_admin = ctk.CTkEntry(filter_frame, placeholder_text="DD-MM-AAAA",
                                                    fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                    border_color="gray40")
        self.start_date_entry_admin.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.start_date_entry_admin.bind("<KeyRelease>", partial(self._validate_date_live_admin, self.start_date_entry_admin))
        self.start_date_entry_admin.bind("<FocusOut>", partial(self._validate_date_live_admin, self.start_date_entry_admin, is_focus_out=True))

        ctk.CTkLabel(filter_frame, text="Data de Fim (DD-MM-AAAA):", text_color=self.controller.TEXT_COLOR).grid(row=3, column=1, sticky="w", padx=10, pady=(5, 0))
        self.end_date_entry_admin = ctk.CTkEntry(filter_frame, placeholder_text="DD-MM-AAAA",
                                                  fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                  border_color="gray40")
        self.end_date_entry_admin.grid(row=4, column=1, sticky="ew", padx=10, pady=(0, 10))
        self.end_date_entry_admin.bind("<KeyRelease>", partial(self._validate_date_live_admin, self.end_date_entry_admin))
        self.end_date_entry_admin.bind("<FocusOut>", partial(self._validate_date_live_admin, self.end_date_entry_admin, is_focus_out=True))
        self.default_border_color_admin = self.search_entry_admin.cget("border_color")


        button_frame_filters = ctk.CTkFrame(filter_frame, fg_color="transparent")
        # ALTERAÇÃO: Configura 3 colunas para distribuir o espaço igualmente
        button_frame_filters.grid(row=5, column=0, columnspan=4, sticky="ew", padx=10, pady=5)
        button_frame_filters.grid_columnconfigure((0, 1, 2), weight=1) # Adicionado weight para a 3ª coluna

        self.apply_filters_button_admin = ctk.CTkButton(button_frame_filters, text="Aplicar Filtros", command=self.filter_occurrences_admin,
                                                      fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                                      hover_color=self.controller.ACCENT_COLOR)
        self.apply_filters_button_admin.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.clear_filters_button_admin = ctk.CTkButton(button_frame_filters, text="Limpar Filtros", command=self.clear_filters_admin,
                                                      fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                                                      hover_color=self.controller.GRAY_HOVER_COLOR)
        self.clear_filters_button_admin.grid(row=0, column=1, padx=(5, 5), sticky="ew") # Ajustado padx

        # NOVO POSICIONAMENTO: Botão "Ir para Histórico"
        ctk.CTkButton(button_frame_filters, text="Ir para Histórico",
                      # ATUALIZAÇÃO: Passe o nome da tela atual como from_view
                      command=lambda: self.controller.show_frame("HistoryView", from_view="AdminDashboardView"),
                      fg_color=self.controller.PRIMARY_COLOR, # Pode ser outra cor se preferir
                      text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.ACCENT_COLOR).grid(row=0, column=2, padx=(5, 0), sticky="ew") # Nova coluna


        self.all_occurrences_frame = ctk.CTkScrollableFrame(tab, label_text="Carregando...",
                                                           fg_color="gray10",
                                                           label_text_color=self.controller.TEXT_COLOR)
        self.all_occurrences_frame.pack(fill="both", expand=True, pady=5, padx=5)

        # Frame inferior, agora sem o botão "Ir para Histórico"
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.pack(fill="x", pady=5, padx=5)
        button_frame.grid_columnconfigure((0, 1), weight=1) # Ajustado para 2 colunas

        ctk.CTkButton(button_frame, text="Salvar Alterações de Status", command=self.save_status_changes,
                      fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.ACCENT_COLOR).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ctk.CTkButton(button_frame, text="Atualizar Lista", command=lambda: self.load_all_occurrences(force_refresh=True),
                      fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.GRAY_HOVER_COLOR).grid(row=0, column=1, padx=(5, 0), sticky="ew")


    def setup_access_tab(self, tab):
        ctk.CTkLabel(tab, text="Gerenciar Solicitações de Acesso", text_color=self.controller.TEXT_COLOR).pack(pady=5)
        self.pending_users_frame = ctk.CTkScrollableFrame(tab, label_text="Carregando solicitações...",
                                                         fg_color="gray10",
                                                         label_text_color=self.controller.TEXT_COLOR)
        self.pending_users_frame.pack(fill="both", expand=True, pady=5, padx=5)

        ctk.CTkButton(tab, text="Atualizar Solicitações", command=self.load_access_requests,
                      fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.GRAY_HOVER_COLOR).pack(pady=10)

    def setup_users_tab(self, tab):
        ctk.CTkLabel(tab, text="Gerenciar Perfis de Usuários", text_color=self.controller.TEXT_COLOR).pack(pady=5)

        # Frame de busca e filtros para usuários
        user_filter_frame = ctk.CTkFrame(tab, fg_color="gray15")
        user_filter_frame.pack(fill="x", pady=(0, 10), padx=5)
        user_filter_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(user_filter_frame, text="Busca por Usuário:", text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))
        self.search_user_entry = ctk.CTkEntry(user_filter_frame, placeholder_text="Nome, e-mail ou username...",
                                               fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                               border_color="gray40")
        self.search_user_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.search_user_entry.bind("<KeyRelease>", self.filter_users_admin)


        self.all_users_frame = ctk.CTkScrollableFrame(tab, label_text="Carregando usuários...",
                                                      fg_color="gray10",
                                                      label_text_color=self.controller.TEXT_COLOR)
        self.all_users_frame.pack(fill="both", expand=True, pady=5, padx=5)

        # Frame para os botões de ação na aba de Usuários
        user_buttons_frame = ctk.CTkFrame(tab, fg_color="transparent")
        user_buttons_frame.pack(fill="x", pady=5, padx=5)
        user_buttons_frame.grid_columnconfigure((0, 1), weight=1) # Configura para duas colunas de peso igual

        # Botão "Salvar Alterações de Perfil"
        ctk.CTkButton(user_buttons_frame, text="Salvar Alterações de Perfil", command=self.save_profile_changes,
                      fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.ACCENT_COLOR).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        # Botão "Atualizar Lista de Usuários"
        ctk.CTkButton(user_buttons_frame, text="Atualizar Lista de Usuários", command=lambda: self.load_all_users(force_refresh=True),
                      fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.GRAY_HOVER_COLOR).grid(row=0, column=1, padx=(5, 0), sticky="ew")


    def _validate_date_live_admin(self, widget, event=None, is_focus_out=False):
        """
        Valida e formata o formato da data em tempo real e quando o campo perde o foco.
        """
        date_str = widget.get()
        # Se o campo estiver vazio, retorna para não validar
        if not date_str:
            widget.configure(border_color=self.default_border_color_admin)
            return True

        # Remove todos os caracteres que não sejam dígitos para processamento
        digits = re.sub(r'[^\d]', '', date_str)
        is_valid_format = False

        if len(digits) == 8:
            try:
                # Tenta converter a string de 8 dígitos para um objeto datetime
                # Assume o formato DDMMYYYY para digitação
                date_obj = datetime.strptime(digits, "%d%m%Y")

                # Formata de volta com hífens no formato DD-MM-AAAA
                formatted_date = date_obj.strftime("%d-%m-%Y")

                # Se a formatação for bem-sucedida, atualiza o widget e a flag
                widget.delete(0, 'end')
                widget.insert(0, formatted_date)
                is_valid_format = True

            except ValueError:
                # Se a conversão falhar (data inválida), marca como inválido
                is_valid_format = False

        # Validação final em caso de formato já com hífens
        if len(date_str) == 10 and re.fullmatch(r"^\d{2}-\d{2}-\d{4}$", date_str):
            try:
                datetime.strptime(date_str, "%d-%m-%Y")
                is_valid_format = True
            except ValueError:
                is_valid_format = False

        # Aplica o feedback visual
        if is_valid_format:
            widget.configure(border_color=self.default_border_color_admin)
        else:
            widget.configure(border_color="red")

        return is_valid_format

    def clear_filters_admin(self):
        """Reseta todos os campos de filtro para o estado padrão e re-aplica a filtragem."""
        self.search_entry_admin.delete(0, "end")
        self.status_filter_admin.set("TODOS")
        self.type_filter_admin.set("TODOS")
        self.start_date_entry_admin.delete(0, "end")
        self.end_date_entry_admin.delete(0, "end")

        self.start_date_entry_admin.configure(border_color=self.default_border_color_admin)
        self.end_date_entry_admin.configure(border_color=self.default_border_color_admin)

        self.load_all_occurrences(force_refresh=True) # Recarrega a lista completa de ativos

    def filter_occurrences_admin(self):
        """
        Filtra a lista de ocorrências com base nos termos de busca e nos filtros selecionados.
        Este método deve obter *todas* as ocorrências ativas do controller e aplicar os filtros na UI.
        """
        # Valida os campos de data antes de prosseguir com a filtragem completa
        start_date_valid = self._validate_date_live_admin(self.start_date_entry_admin, is_focus_out=True)
        end_date_valid = self._validate_date_live_admin(self.end_date_entry_admin, is_focus_out=True)

        if not start_date_valid or not end_date_valid:
            messagebox.showwarning("Formato de Data Inválido", "Por favor, corrija o formato das datas (DD-MM-AAAA) antes de aplicar os filtros.")
            return

        search_term = self.search_entry_admin.get().lower()
        selected_status = self.status_filter_admin.get().upper()
        selected_type = self.type_filter_admin.get().upper()

        start_date_str = self.start_date_entry_admin.get()
        end_date_str = self.end_date_entry_admin.get()

        # Obter a lista de ocorrências ativas do controller (já filtradas por status resolvido/cancelado)
        all_active_occurrences = self.controller.get_all_occurrences_for_admin()

        filtered_list = all_active_occurrences

        # 1. Filtrar por termo de busca
        if search_term:
            filtered_list = [
                occ for occ in filtered_list
                if any(search_term in str(v).lower() for v in occ.values())
            ]

        # 2. Filtrar por status (além do que já foi feito na camada de serviço, para filtros adicionais do usuário)
        if selected_status != "TODOS":
            filtered_list = [
                occ for occ in filtered_list
                if occ.get('Status', '').upper() == selected_status
            ]

        # 3. Filtrar por tipo de ocorrência
        if selected_type != "TODOS":
            if selected_type == "CHAMADA":
                filtered_list = [occ for occ in filtered_list if 'CALL' in occ.get('ID', '') and 'SCALL' not in occ.get('ID', '')]
            elif selected_type == "CHAMADA SIMPLES":
                filtered_list = [occ for occ in filtered_list if 'SCALL' in occ.get('ID', '')]
            elif selected_type == "EQUIPAMENTO":
                filtered_list = [occ for occ in filtered_list if 'EQUIP' in occ.get('ID', '')]

        # 4. Filtrar por intervalo de datas
        if start_date_str or end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%d-%m-%Y") if start_date_str else datetime.min
                end_date = datetime.strptime(end_date_str, "%d-%m-%Y").replace(hour=23, minute=59, second=59) if end_date_str else datetime.max

                filtered_list = [
                    occ for occ in filtered_list
                    if 'Data de Registro' in occ and \
                       start_date <= datetime.strptime(occ['Data de Registro'].split(' ')[0], "%Y-%m-%d") <= end_date
                ]

            except ValueError:
                messagebox.showwarning("Formato de Data Inválido", "Ocorreu um erro inesperado na validação da data. Por favor, verifique o formato DD-MM-AAAA.")
                return

        self._populate_all_occurrences(filtered_list) # Repopula com a lista filtrada


    def load_all_occurrences(self, force_refresh=False):
        occurrences_to_load = self.controller.get_all_occurrences_for_admin(force_refresh=force_refresh)
        threading.Thread(target=lambda: self.after(0, self._populate_all_occurrences, occurrences_to_load), daemon=True).start()

    def _populate_all_occurrences(self, all_occurrences_list):
        self.status_updaters.clear()
        self.original_statuses.clear()
        for widget in self.all_occurrences_frame.winfo_children(): widget.destroy()
        if not all_occurrences_list:
            self.all_occurrences_frame.configure(label_text="Nenhuma ocorrência encontrada.")
            return
        self.all_occurrences_frame.configure(label_text="")
        status_options = ["REGISTRADO", "EM ANÁLISE", "AGUARDANDO TERCEIROS", "PARCIALMENTE RESOLVIDO", "RESOLVIDO", "CANCELADO"]
        for item in all_occurrences_list:
            item_id = item.get('ID', 'N/A')
            self.original_statuses[item_id] = item.get('Status', 'N/A')
            card = ctk.CTkFrame(self.all_occurrences_frame, fg_color="gray20")
            card.pack(fill="x", padx=5, pady=5)
            card.grid_columnconfigure(0, weight=1)

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.grid(row=0, column=0, sticky="w", padx=10, pady=5)
            title = item.get('Título da Ocorrência', 'Ocorrência sem Título')

            ctk.CTkLabel(info_frame, text=f"ID: {item_id} - {title}",
                         font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
                         text_color=self.controller.TEXT_COLOR).pack(anchor="w")

            ctk.CTkLabel(info_frame, text=f"Registrado por: {item.get('Nome do Registrador', 'N/A')} em {item.get('Data de Registro', 'N/A')}",
                         anchor="w", text_color="gray60").pack(anchor="w")

            controls_frame = ctk.CTkFrame(card, fg_color="transparent")
            controls_frame.grid(row=0, column=1, sticky="e", padx=10, pady=5)

            status_combo = ctk.CTkComboBox(controls_frame, values=status_options, width=180,
                                           fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                           border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                           button_hover_color=self.controller.ACCENT_COLOR)
            status_combo.set(self.original_statuses[item_id])
            status_combo.pack(side="left", padx=(0, 10))
            self.status_updaters[item_id] = status_combo

            ctk.CTkButton(controls_frame, text="Abrir", width=80,
                          command=partial(self.controller.show_occurrence_details, item_id),
                          fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                          hover_color=self.controller.ACCENT_COLOR).pack(side="left")

    def save_status_changes(self):
        changes = {occ_id: combo.get() for occ_id, combo in self.status_updaters.items() if self.original_statuses.get(occ_id) != combo.get()}
        self.controller.save_occurrence_status_changes(changes)

    def setup_access_tab(self, tab):
        ctk.CTkLabel(tab, text="Solicitações de Acesso Pendentes", text_color=self.controller.TEXT_COLOR).pack(pady=5)
        self.pending_users_frame = ctk.CTkScrollableFrame(tab, label_text="Carregando solicitações...",
                                                          fg_color="gray10",
                                                          label_text_color=self.controller.TEXT_COLOR)
        self.pending_users_frame.pack(fill="both", expand=True, pady=5, padx=5)

        ctk.CTkButton(tab, text="Atualizar Lista", command=self.load_access_requests,
                      fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.GRAY_HOVER_COLOR).pack(pady=5, padx=5, fill="x")

    def load_access_requests(self):
        threading.Thread(target=lambda: self.after(0, self._populate_access_requests, self.controller.get_pending_requests()), daemon=True).start()

    def _populate_access_requests(self, pending_list):
        for widget in self.pending_users_frame.winfo_children(): widget.destroy()
        if not pending_list:
            self.pending_users_frame.configure(label_text="Nenhuma solicitação pendente.")
            return
        self.pending_users_frame.configure(label_text="")
        for user in pending_list:
            card = ctk.CTkFrame(self.pending_users_frame, fg_color="gray20")
            card.pack(fill="x", pady=5)
            card.grid_columnconfigure(0, weight=1)

            company_info = f" ({user.get('company')})" if user.get('company') else ""
            info_text = f"Nome: {user.get('name', 'N/A')} (@{user.get('username', 'N/A')})\n" \
                        f"E-mail: {user['email']}\nVínculo: {user['main_group']}{company_info}"

            ctk.CTkLabel(card, text=info_text, justify="left",
                         text_color=self.controller.TEXT_COLOR).pack(side="left", padx=10, pady=5)

            ctk.CTkButton(card, text="Rejeitar",
                          command=partial(self.controller.update_user_access, user['email'], 'rejected'),
                          fg_color=self.controller.DANGER_COLOR, text_color=self.controller.TEXT_COLOR,
                          hover_color=self.controller.DANGER_HOVER_COLOR).pack(side="right", padx=5, pady=5)

            ctk.CTkButton(card, text="Aprovar",
                          command=partial(self.controller.update_user_access, user['email'], 'approved'),
                          fg_color="green",
                          text_color=self.controller.TEXT_COLOR,
                          hover_color="darkgreen").pack(side="right", padx=5, pady=5)

    def save_profile_changes(self):
        changes = {}
        for email, widgets in self.profile_updaters.items():
            new_main = widgets['main_group'].get()
            new_sub = widgets['sub_group'].get()
            new_comp = widgets['company'].get() if new_main in ['PARTNER', 'PREFEITURA'] or (new_main == '67_TELECOM' and new_sub == '67_INTERNET_USER') else ""

            original = self.original_profiles.get(email, {})
            if original.get('main_group') != new_main or original.get('sub_group') != new_sub or original.get('company') != new_comp:
                changes[email] = {'main_group': new_main, 'sub_group': new_sub, 'company': new_comp}

        self.controller.update_user_profile(changes)

    def setup_users_tab(self, tab):
        ctk.CTkLabel(tab, text="Lista de Todos os Usuários", text_color=self.controller.TEXT_COLOR).pack(pady=5)
        self.all_users_frame = ctk.CTkScrollableFrame(tab, label_text="Carregando...",
                                                      fg_color="gray10",
                                                      label_text_color=self.controller.TEXT_COLOR)
        self.all_users_frame.pack(fill="both", expand=True, pady=5, padx=5)
        button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        button_frame.pack(fill="x", pady=5, padx=5)

        ctk.CTkButton(button_frame, text="Salvar Alterações de Perfil", command=self.save_profile_changes,
                      fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.ACCENT_COLOR).pack(side="left", padx=(0, 10), expand=True, fill="x")

        ctk.CTkButton(button_frame, text="Atualizar Lista", command=lambda: self.load_all_users(force_refresh=True),
                      fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                      hover_color=self.controller.GRAY_HOVER_COLOR).pack(side="left", expand=True, fill="x")

    def load_all_users(self, force_refresh=False):
        threading.Thread(target=lambda: self.after(0, self._populate_all_users, self.controller.get_all_users(force_refresh)), daemon=True).start()

    def _populate_all_users(self, all_users_list):
        self.profile_updaters.clear()
        self.original_profiles.clear()
        for widget in self.all_users_frame.winfo_children(): widget.destroy()
        if not all_users_list:
            self.all_users_frame.configure(label_text="Nenhuma usuário encontrado.")
            return
        self.all_users_frame.configure(label_text="")
        main_group_options = ["67_TELECOM", "PARTNER", "PREFEITURA"]
        sub_group_options = ["SUPER_ADMIN", "ADMIN", "MANAGER", "67_TELECOM_USER", "67_INTERNET_USER"] # Adicionado o novo subgrupo

        for user in all_users_list:
            email = user.get('email')
            self.original_profiles[email] = {'main_group': user.get('main_group'), 'sub_group': user.get('sub_group'), 'company': user.get('company')}

            card = ctk.CTkFrame(self.all_users_frame, fg_color="gray20")
            card.pack(fill="x", pady=5)
            card.grid_columnconfigure(0, weight=1)

            info_text = f"{user.get('name', 'N/A')} (@{user.get('username', 'N/A')})"
            ctk.CTkLabel(card, text=info_text, anchor="w", text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(card, text=email, anchor="w", text_color="gray60").grid(row=1, column=0, padx=10, pady=(0,5), sticky="w")

            controls_frame = ctk.CTkFrame(card, fg_color="transparent")
            # Configurar as colunas do controls_frame para usar grid
            controls_frame.grid_columnconfigure((0, 1, 2), weight=1) # Permite que as colunas se expandam
            controls_frame.grid_rowconfigure(0, weight=1) # Garante que a linha existe
            controls_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=5, sticky="nsew")

            main_group_combo = ctk.CTkComboBox(controls_frame, values=main_group_options, width=140,
                                               command=partial(self._on_main_group_change, email),
                                               fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                               border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                               button_hover_color=self.controller.ACCENT_COLOR)
            main_group_combo.set(user.get('main_group'))
            main_group_combo.grid(row=0, column=0, padx=(0, 5), sticky="ew") # Usar grid

            sub_group_combo = ctk.CTkComboBox(controls_frame, values=sub_group_options, width=140,
                                              fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                              border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                              button_hover_color=self.controller.ACCENT_COLOR)
            sub_group_combo.set(user.get('sub_group'))
            sub_group_combo.grid(row=0, column=1, padx=(0, 5), sticky="ew") # Usar grid

            company_combo = ctk.CTkComboBox(controls_frame, values=[], width=180,
                                            fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                            border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                            button_hover_color=self.controller.ACCENT_COLOR)
            company_combo.set(user.get('company', ''))
            company_combo.grid(row=0, column=2, padx=(0, 5), sticky="ew") # Usar grid

            self.profile_updaters[email] = {'main_group': main_group_combo, 'sub_group': sub_group_combo, 'company': company_combo}
            self._on_main_group_change(email, user.get('main_group'))

    def _on_main_group_change(self, email, selected_group):
        if self.profile_updaters.get(email, {}).get('company'):
            company_widget = self.profile_updaters[email]['company']
            sub_group_widget = self.profile_updaters[email]['sub_group'] # Obter o widget do subgrupo

            if selected_group == 'PARTNER':
                company_widget.configure(values=self.partner_companies)
                if company_widget.get() not in self.partner_companies:
                    company_widget.set(self.partner_companies[0] if self.partner_companies else "")
                company_widget.grid(row=0, column=2, padx=(0, 5), sticky="ew") # Usar grid
            elif selected_group == 'PREFEITURA':
                company_widget.configure(values=self.prefeitura_dept_list)
                if company_widget.get() not in self.prefeitura_dept_list:
                    company_widget.set(self.prefeitura_dept_list[0] if self.prefeitura_dept_list else "")
                company_widget.grid(row=0, column=2, padx=(0, 5), sticky="ew") # Usar grid
            elif selected_group == '67_TELECOM': # Se o grupo principal for 67_TELECOM
                current_sub_group = sub_group_widget.get()
                if current_sub_group == "67_INTERNET_USER":
                    company_widget.configure(values=["67 INTERNET"]) # Força a empresa
                    company_widget.set("67 INTERNET")
                    company_widget.grid(row=0, column=2, padx=(0, 5), sticky="ew")
                else:
                    company_widget.grid_forget() # Esconde para outros subgrupos 67_TELECOM
            else:
                company_widget.grid_forget()

    def save_profile_changes(self):
        changes = {}
        for email, widgets in self.profile_updaters.items():
            new_main = widgets['main_group'].get()
            new_sub = widgets['sub_group'].get()
            new_comp = widgets['company'].get() if new_main in ['PARTNER', 'PREFEITURA'] or (new_main == '67_TELECOM' and new_sub == '67_INTERNET_USER') else ""

            original = self.original_profiles.get(email, {})
            if original.get('main_group') != new_main or original.get('sub_group') != new_sub or original.get('company') != new_comp:
                changes[email] = {'main_group': new_main, 'sub_group': new_sub, 'company': new_comp}

        self.controller.update_user_profile(changes)
