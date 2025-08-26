# ==============================================================================
# ARQUIVO: src/views/history_view.py
# DESCRIÇÃO: Contém a classe de interface para a tela de histórico de
#            ocorrências, que exibe os registros visíveis ao usuário.
#            (VERSÃO OTIMIZADA COM CACHE, FILTROS AVANÇADOS, MELHORIAS DE USABILIDADE E CORES)
#            ATUALIZADO com badge de tipo de acesso, estatísticas contextuais e otimização de filtros.
#            CORRIGIDO: Lógica de carregamento para usar get_occurrences_by_user e navegação.
#            CORRIGIDO: Exibição de números de origem/destino em Chamada Simples.
# ==============================================================================

import customtkinter as ctk
import threading
from functools import partial
import json
from tkinter import messagebox
from datetime import datetime
import re

class HistoryView(ctk.CTkFrame):
    """
    Tela para exibir o histórico de ocorrências do usuário, com cache
    para otimizar a performance da busca e filtros avançados.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        self.cached_occurrences = []
        self.return_to_view = "MainMenuView"
        self.current_mode = "all"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(4, weight=0)


        title_and_button_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_and_button_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        title_and_button_frame.grid_columnconfigure(0, weight=1)
        title_and_button_frame.grid_columnconfigure(1, weight=0)

        self.title_label = ctk.CTkLabel(title_and_button_frame, text="Histórico de Ocorrências",
                                        font=ctk.CTkFont(size=24, weight="bold"),
                                        text_color=self.controller.TEXT_COLOR)
        self.title_label.grid(row=0, column=0, sticky="w")

        self.general_history_button = ctk.CTkButton(title_and_button_frame, text="Histórico Geral",
                                                    command=lambda: self.controller.show_frame("HistoryView", from_view="OcorrenciasPendentes", mode="all"),
                                                    fg_color=self.controller.ACCENT_COLOR, text_color=self.controller.TEXT_COLOR,
                                                    hover_color=self.controller.PRIMARY_COLOR, width=150)
        self.general_history_button.grid(row=0, column=1, padx=(10, 0), sticky="e")
        self.general_history_button.grid_forget()

        self.access_badge_label = ctk.CTkLabel(self, text="",
                                               font=ctk.CTkFont(size=12, weight="bold", slant="italic"),
                                               text_color="gray70")
        self.access_badge_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")


        filter_frame = ctk.CTkFrame(self, fg_color="gray15")
        filter_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        filter_frame.grid_columnconfigure((1, 2, 3), weight=1)

        ctk.CTkLabel(filter_frame, text="Painel de Filtros",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(5, 0))

        ctk.CTkLabel(filter_frame, text="Busca por Palavra-Chave:", text_color=self.controller.TEXT_COLOR).grid(row=1, column=0, sticky="w", padx=10, pady=(5, 0))
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="ID, título, nome do usuário...",
                                         fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                         border_color="gray40")
        self.search_entry.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

        ctk.CTkLabel(filter_frame, text="Filtrar por Status:", text_color=self.controller.TEXT_COLOR).grid(row=1, column=2, sticky="w", padx=10, pady=(5, 0))
        self.status_filter = ctk.CTkComboBox(filter_frame, values=[],
                                             fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                             border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                             button_hover_color=self.controller.ACCENT_COLOR)
        self.status_filter.grid(row=2, column=2, padx=10, pady=(0, 10), sticky="ew")
        self.status_filter.set("TODOS")

        ctk.CTkLabel(filter_frame, text="Filtrar por Tipo:", text_color=self.controller.TEXT_COLOR).grid(row=1, column=3, sticky="w", padx=10, pady=(5, 0))
        type_options = ["TODOS", "CHAMADA", "EQUIPAMENTO", "CHAMADA SIMPLES"]
        self.type_filter = ctk.CTkComboBox(filter_frame, values=type_options,
                                           fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                           border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                           button_hover_color=self.controller.ACCENT_COLOR)
        self.type_filter.grid(row=2, column=3, padx=10, pady=(0, 10), sticky="ew")
        self.type_filter.set("TODOS")

        ctk.CTkLabel(filter_frame, text="Filtrar por Data de Início:", text_color=self.controller.TEXT_COLOR).grid(row=3, column=0, sticky="w", padx=10, pady=(5, 0))
        self.start_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="DD-MM-AAAA",
                                             fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                             border_color="gray40")
        self.start_date_entry.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.start_date_entry.bind("<KeyRelease>", partial(self._validate_date_live, self.start_date_entry))
        self.start_date_entry.bind("<FocusOut>", partial(self._validate_date_live, self.start_date_entry, is_focus_out=True))

        ctk.CTkLabel(filter_frame, text="Filtrar por Data de Fim:", text_color=self.controller.TEXT_COLOR).grid(row=3, column=1, sticky="w", padx=10, pady=(5, 0))
        self.end_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="DD-MM-AAAA",
                                           fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                           border_color="gray40")
        self.end_date_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=(0, 10))
        self.end_date_entry.bind("<KeyRelease>", partial(self._validate_date_live, self.end_date_entry))
        self.end_date_entry.bind("<FocusOut>", partial(self._validate_date_live, self.end_date_entry, is_focus_out=True))

        self.default_border_color = self.start_date_entry.cget("border_color")

        button_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        button_frame.grid(row=5, column=0, columnspan=4, sticky="ew", padx=10, pady=5)
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.apply_filters_button = ctk.CTkButton(button_frame, text="Aplicar Filtros", command=self.filter_history,
                                                  fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                                  hover_color=self.controller.ACCENT_COLOR)
        self.apply_filters_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.clear_filters_button = ctk.CTkButton(button_frame, text="Limpar Filtros", command=self.clear_filters,
                                                  fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                                                  hover_color=self.controller.GRAY_HOVER_COLOR)
        self.clear_filters_button.grid(row=0, column=1, padx=(5, 5), sticky="ew")

        self.refresh_button = ctk.CTkButton(button_frame, text="Recarregar Dados", command=self.load_history,
                                            fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                                            hover_color=self.controller.GRAY_HOVER_COLOR)
        self.refresh_button.grid(row=0, column=2, padx=(5, 0), sticky="ew")

        self.history_scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Carregando histórico...",
                                                               fg_color="gray10",
                                                               label_text_color=self.controller.TEXT_COLOR)
        self.history_scrollable_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")

        self.stats_footer_label = ctk.CTkLabel(self, text="",
                                               font=ctk.CTkFont(size=12, weight="bold"),
                                               text_color="gray70")
        self.stats_footer_label.grid(row=4, column=0, padx=20, pady=(0, 5), sticky="ew")

        self.back_button = ctk.CTkButton(self, text="Voltar", command=self._go_back_to_previous_view,
                                    fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                                    hover_color=self.controller.GRAY_HOVER_COLOR)
        self.back_button.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")


    def _go_back_to_previous_view(self):
        pass


    def _validate_date_live(self, widget, event=None, is_focus_out=False):
        """
        Valida e formata o formato da data em tempo real e quando o campo perde o foco.
        """
        date_str = widget.get()
        if not date_str:
            widget.configure(border_color=self.default_border_color)
            return True

        digits = re.sub(r'[^\d]', '', date_str)
        is_valid_format = False

        if len(digits) == 8:
            try:
                date_obj = datetime.strptime(digits, "%d%m%Y")
                formatted_date = date_obj.strftime("%d-%m-%Y")
                widget.delete(0, 'end')
                widget.insert(0, formatted_date)
                is_valid_format = True
            except ValueError:
                is_valid_format = False

        if len(date_str) == 10 and re.fullmatch(r"^\d{2}-\d{2}-\d{4}$", date_str):
            try:
                datetime.strptime(date_str, "%d-%m-%Y")
                is_valid_format = True
            except ValueError:
                is_valid_format = False

        if is_valid_format:
            widget.configure(border_color=self.default_border_color)
        else:
            widget.configure(border_color="red")

        return is_valid_format

    def on_show(self, from_view=None, mode="all"):
        """
        Chamado sempre que a tela é exibida.
        :param from_view: A view de onde veio a navegação.
        :param mode: O modo de exibição ("all" para todas as ocorrências, "pending" para pendentes).
        """
        self.current_mode = mode

        self.search_entry.delete(0, "end")
        self.type_filter.set("TODOS")
        self.start_date_entry.delete(0, "end")
        self.end_date_entry.delete(0, "end")

        self.start_date_entry.configure(border_color=self.default_border_color)
        self.end_date_entry.configure(border_color=self.default_border_color)

        user_profile = self.controller.get_current_user_profile()
        main_group = user_profile.get("main_group")

        self._configure_access_badge_and_filters(main_group)

        if self.current_mode == "pending":
            self.title_label.configure(text="Ocorrências Pendentes")
            self.general_history_button.grid(row=0, column=1, padx=(10, 0), sticky="e")
            
            if from_view == "AdminDashboardView":
                self.back_button.configure(command=lambda: self.controller.show_frame("AdminDashboardView"))
            else:
                self.back_button.configure(command=lambda: self.controller.show_frame("MainMenuView"))

        else:
            self.title_label.configure(text="Histórico Geral de Ocorrências")
            self.general_history_button.grid_forget()
            
            if from_view == "OcorrenciasPendentes":
                self.back_button.configure(command=lambda: self.controller.show_frame("HistoryView", from_view="AdminDashboardView", mode="pending"))
            elif from_view == "AdminDashboardView":
                 self.back_button.configure(command=lambda: self.controller.show_frame("AdminDashboardView"))
            else:
                self.back_button.configure(command=lambda: self.controller.show_frame("MainMenuView"))


        self.history_scrollable_frame.configure(label_text="Carregando histórico...")
        self.update_idletasks()
        self.load_history()

    def _configure_access_badge_and_filters(self, main_group):
        """Configura o badge de acesso e as opções do filtro de status com base no grupo."""
        if main_group == '67_TELECOM':
            self.access_badge_label.configure(text="🔓 Acesso Completo", text_color="green")
        elif main_group == 'PARTNER':
            self.access_badge_label.configure(text="🔐 Acesso Restrito", text_color="orange")
        elif main_group == 'PREFEITURA':
            self.access_badge_label.configure(text="📋 Acesso Específico", text_color="blue")
        else:
            self.access_badge_label.configure(text="", text_color="gray70")

        if main_group != '67_TELECOM':
            limited_status_options = ["TODOS", "REGISTRADO", "EM ANÁLISE", "PARCIALMENTE RESOLVIDO", "RESOLVIDO", "CANCELADO"]
            self.status_filter.configure(values=limited_status_options)
        else:
            full_status_options = ["TODOS", "REGISTRADO", "EM ANÁLISE", "AGUARDANDO TERCEIROS", "PARCIALMENTE RESOLVIDO", "RESOLVIDO", "CANCELADO"]
            self.status_filter.configure(values=full_status_options)

        if self.current_mode == "pending":
            self.status_filter.set("REGISTRADO")
            self.status_filter.configure(state="disabled")
        else:
            self.status_filter.configure(state="normal")


    def load_history(self):
        """Inicia o carregamento FORÇADO do histórico a partir do Google Sheets."""
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self._load_history_thread, daemon=True).start()

    def _load_history_thread(self):
        """Busca os dados no serviço, armazena no cache e chama a atualização da UI."""
        user_email = self.controller.user_email
        all_user_visible_occurrences = self.controller.sheets_service.get_occurrences_by_user(user_email)

        if self.current_mode == "pending":
            self.cached_occurrences = [
                occ for occ in all_user_visible_occurrences
                if occ.get('Status', '').upper() not in ["RESOLVIDO", "CANCELADO"]
            ]
        else:
            self.cached_occurrences = all_user_visible_occurrences
        
        user_profile = self.controller.get_current_user_profile()
        self.after(0, self._populate_history, self.cached_occurrences, user_profile)

    def clear_filters(self):
        """Reseta todos os campos de filtro para o estado padrão e reaplica a filtragem."""
        self.search_entry.delete(0, "end")
        
        if self.current_mode == "all":
            self.status_filter.set("TODOS")
        
        self.type_filter.set("TODOS")
        self.start_date_entry.delete(0, "end")
        self.end_date_entry.delete(0, "end")

        self.start_date_entry.configure(border_color=self.default_border_color)
        self.end_date_entry.configure(border_color=self.default_border_color)

        self.filter_history()

    def filter_history(self):
        """
        Filtra a lista JÁ CARREGADA (cache) com base no termo de pesquisa e nos novos filtros.
        """
        start_date_valid = self._validate_date_live(self.start_date_entry, is_focus_out=True)
        end_date_valid = self._validate_date_live(self.end_date_entry, is_focus_out=True)

        if not start_date_valid or not end_date_valid:
            messagebox.showwarning("Formato de Data Inválido", "Por favor, corrija o formato das datas (DD-MM-AAAA) antes de aplicar os filtros.")
            return

        search_term = self.search_entry.get().lower()
        selected_status = self.status_filter.get().upper()
        selected_type = self.type_filter.get().upper()

        start_date_str = self.start_date_entry.get()
        end_date_str = self.end_date_entry.get()

        filtered_list = self.cached_occurrences

        if search_term:
            filtered_list = [
                occ for occ in filtered_list
                if any(search_term in str(v).lower() for v in occ.values())
            ]

        if self.current_mode == "all" and selected_status != "TODOS":
            filtered_list = [
                occ for occ in filtered_list
                if occ.get('Status', '').upper() == selected_status
            ]

        if selected_type != "TODOS":
            if selected_type == "CHAMADA":
                filtered_list = [occ for occ in filtered_list if 'CALL' in occ.get('ID', '') and 'SCALL' not in occ.get('ID', '')]
            elif selected_type == "CHAMADA SIMPLES":
                filtered_list = [occ for occ in filtered_list if 'SCALL' in occ.get('ID', '')]
            elif selected_type == "EQUIPAMENTO":
                filtered_list = [occ for occ in filtered_list if 'EQUIP' in occ.get('ID', '')]

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

        self._populate_history(filtered_list, self.controller.get_current_user_profile(),
                               search_term=search_term, selected_status=selected_status,
                               selected_type=selected_type,
                               start_date_str=start_date_str, end_date_str=end_date_str)

    def _populate_history(self, occurrences, user_profile, search_term="", selected_status="TODOS", selected_type="TODOS", start_date_str="", end_date_str=""):
        """Preenche a lista de scroll com os cards das ocorrências."""
        main_group = user_profile.get("main_group")
        sub_group = user_profile.get("sub_group")
        is_admin_or_super_admin = (main_group == "67_TELECOM" and (sub_group == "ADMIN" or sub_group == "SUPER_ADMIN"))

        if self.current_mode == "pending":
            self.title_label.configure(text="Ocorrências Pendentes")
        elif main_group == '67_TELECOM':
            self.title_label.configure(text="Histórico Geral de Ocorrências")
        elif main_group in ['PARTNER', 'PREFEITURA']:
            company = user_profile.get("company", "N/A")
            self.title_label.configure(text=f"Histórico de Ocorrências: {company}")


        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()

        if not occurrences:
            self.history_scrollable_frame.configure(label_text="Nenhuma ocorrência encontrada para os filtros aplicados.",
                                                    label_text_color=self.controller.TEXT_COLOR)
            self.stats_footer_label.configure(text="")
            return

        filter_summary = []
        if search_term:
            filter_summary.append(f"Busca: '{search_term}'")
        
        if self.current_mode == "pending":
            filter_summary.append("Status: Pendentes")
        elif selected_status != "TODOS":
            filter_summary.append(f"Status: '{selected_status}'")
        
        if selected_type != "TODOS":
            filter_summary.append(f"Tipo: '{selected_type}'")
        if start_date_str and end_date_str:
            filter_summary.append(f"De: {start_date_str} até: {end_date_str}")
        elif start_date_str:
            filter_summary.append(f"A partir de: {start_date_str}")
        elif end_date_str:
            filter_summary.append(f"Até: {end_date_str}")


        if filter_summary:
            label_text = f"Resultados ({len(occurrences)}): {', '.join(filter_summary)}"
        else:
            label_text = f"Todas as Ocorrências ({len(occurrences)})"

        self.history_scrollable_frame.configure(label_text=label_text, label_text_color=self.controller.TEXT_COLOR)

        status_options_for_editing = ["REGISTRADO", "EM ANÁLISE", "AGUARDANDO TERCEIROS", "PARCIALMENTE RESOLVIDO", "RESOLVIDO", "CANCELADO"]

        for item in occurrences:
            item_id = item.get('ID', 'N/A')

            card_frame = ctk.CTkFrame(self.history_scrollable_frame, fg_color="gray20")
            card_frame.pack(fill="x", padx=5, pady=5)
            card_frame.grid_columnconfigure(0, weight=1)

            info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            info_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            title = item.get('Título da Ocorrência')

            if not title or str(title).strip() == "":
                item_id_prefix = item_id.split('-')[0] if '-' in item_id else item_id

                if item_id_prefix == 'SCALL':
                    title = f"Chamada Simples de {item.get('origem', 'N/A')} para {item.get('destino', 'N/A')}"
                elif item_id_prefix == 'EQUIP':
                    title = item.get('tipo', f"Equipamento {item_id}")
                elif item_id_prefix == 'CALL':
                    title = f"Chamada Detalhada {item_id}"
                else:
                    title = 'Ocorrência sem Título'

            date_str = item.get('Data de Registro', 'N/A')
            status = item.get('Status', 'N/A')

            formatted_date = 'N/A'
            if date_str != 'N/A':
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    formatted_date = date_obj.strftime("%d-%m-%Y")
                except ValueError:
                    formatted_date = date_str

            ctk.CTkLabel(info_frame, text=f"ID: {item_id} - {title}",
                         font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
                         text_color=self.controller.TEXT_COLOR).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Registrado por: {item.get('Nome do Registrador', 'N/A')} em {formatted_date}",
                         anchor="w", text_color="gray60").pack(anchor="w")

            controls_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            controls_frame.grid(row=0, column=1, padx=10, pady=10, sticky="e")

            if is_admin_or_super_admin:
                status_combo = ctk.CTkComboBox(controls_frame, values=status_options_for_editing, width=180,
                                               fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                               border_color=self.controller.PRIMARY_COLOR,
                                               button_color=self.controller.PRIMARY_COLOR,
                                               button_hover_color=self.controller.ACCENT_COLOR,
                                               command=partial(self._on_status_change_from_history, item_id))
                status_combo.set(status)
                status_combo.pack(side="left", padx=(0, 10))
            else:
                ctk.CTkLabel(info_frame, text=f"Status: {status}", anchor="w",
                             font=ctk.CTkFont(weight="bold"), text_color=self.controller.TEXT_COLOR).pack(anchor="w")


            open_button = ctk.CTkButton(controls_frame, text="Abrir", width=80,
                                        command=partial(self.controller.show_occurrence_details, item_id),
                                        fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                        hover_color=self.controller.ACCENT_COLOR)
            open_button.pack(side="left")

        stats_text = ""
        if main_group == 'PARTNER':
            company_name = user_profile.get("company", "N/A")
            stats_text = f"Estatística: {len(occurrences)} chamadas da {company_name}"
        elif main_group == 'PREFEITURA':
            own_occurrences = [occ for occ in occurrences if occ.get('registradormaingroup', '').upper() == 'PREFEITURA']
            own_count = len(own_occurrences)
            external_count = len(occurrences) - own_count
            stats_text = f"Estatística: {own_count} suas + {external_count} da 67 Telecom"
        elif main_group == '67_TELECOM':
            stats_text = f"Estatística: {len(occurrences)} ocorrências no total"
        
        self.stats_footer_label.configure(text=stats_text)


    def _on_status_change_from_history(self, occurrence_id, new_status):
        """
        Chamado quando o status de uma ocorrência é alterado no ComboBox do histórico.
        """
        if messagebox.askyesno("Confirmar Alteração de Status",
                               f"Tem certeza que deseja alterar o status da ocorrência {occurrence_id} para '{new_status}'?"):
            self.controller.update_occurrence_status_from_history(occurrence_id, new_status)
        else:
            self.load_history()
