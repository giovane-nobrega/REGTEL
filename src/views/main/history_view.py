# ==============================================================================
# ARQUIVO: src/views/history_view.py
# DESCRIÇÃO: Contém a classe de interface para a tela de histórico de
#            ocorrências, que exibe os registros visíveis ao usuário.
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
        self.grid_rowconfigure(3, weight=1) # Linha do scrollable frame expande

        # --- Frame de Título e Badge ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(header_frame, text="Histórico de Ocorrências",
                                        font=ctk.CTkFont(size=24, weight="bold"),
                                        text_color=self.controller.TEXT_COLOR)
        self.title_label.grid(row=0, column=0, sticky="w")

        self.access_badge_label = ctk.CTkLabel(self, text="",
                                               font=ctk.CTkFont(size=12, weight="bold", slant="italic"),
                                               text_color="gray70")
        self.access_badge_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")
        
        # --- Frame de Filtros ---
        filter_frame = ctk.CTkFrame(self, fg_color="gray15")
        filter_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        filter_frame.grid_columnconfigure((1, 2, 3), weight=1)

        ctk.CTkLabel(filter_frame, text="Busca por Palavra-Chave:", text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="ID, título, nome do usuário...")
        self.search_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda event: self.filter_history())

        ctk.CTkLabel(filter_frame, text="Filtrar por Status:", text_color=self.controller.TEXT_COLOR).grid(row=0, column=2, sticky="w", padx=10, pady=(5, 0))
        self.status_filter = ctk.CTkComboBox(filter_frame, values=[], command=lambda choice: self.filter_history())
        self.status_filter.grid(row=1, column=2, padx=10, pady=(0, 10), sticky="ew")
        self.status_filter.set("TODOS")

        ctk.CTkLabel(filter_frame, text="Filtrar por Tipo:", text_color=self.controller.TEXT_COLOR).grid(row=0, column=3, sticky="w", padx=10, pady=(5, 0))
        type_options = ["TODOS", "CHAMADA", "EQUIPAMENTO", "CHAMADA SIMPLES"]
        self.type_filter = ctk.CTkComboBox(filter_frame, values=type_options, command=lambda choice: self.filter_history())
        self.type_filter.grid(row=1, column=3, padx=10, pady=(0, 10), sticky="ew")
        self.type_filter.set("TODOS")

        ctk.CTkLabel(filter_frame, text="Data de Início:", text_color=self.controller.TEXT_COLOR).grid(row=2, column=0, sticky="w", padx=10, pady=(5, 0))
        self.start_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="DD-MM-AAAA")
        self.start_date_entry.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

        ctk.CTkLabel(filter_frame, text="Data de Fim:", text_color=self.controller.TEXT_COLOR).grid(row=2, column=1, sticky="w", padx=10, pady=(5, 0))
        self.end_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="DD-MM-AAAA")
        self.end_date_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=(0, 10))

        button_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        button_frame.grid(row=3, column=2, columnspan=2, sticky="ew", padx=10, pady=5)
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.apply_filters_button = ctk.CTkButton(button_frame, text="Aplicar Filtros", command=self.filter_history)
        self.apply_filters_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.clear_filters_button = ctk.CTkButton(button_frame, text="Limpar Filtros", command=self.clear_filters,
                                                  fg_color=self.controller.GRAY_BUTTON_COLOR, hover_color=self.controller.GRAY_HOVER_COLOR)
        self.clear_filters_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")


        # --- Frame de Scroll para a Lista de Ocorrências ---
        self.history_scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Carregando histórico...",
                                                               fg_color="gray10",
                                                               label_text_color=self.controller.TEXT_COLOR)
        self.history_scrollable_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")

        # --- Rodapé ---
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.grid(row=4, column=0, padx=20, pady=(5, 10), sticky="ew")
        footer_frame.grid_columnconfigure(0, weight=1)

        self.stats_footer_label = ctk.CTkLabel(footer_frame, text="",
                                               font=ctk.CTkFont(size=12, weight="bold"),
                                               text_color="gray70")
        self.stats_footer_label.pack(side="left")

        self.back_button = ctk.CTkButton(footer_frame, text="Voltar", command=self._go_back_to_previous_view,
                                    fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                                    hover_color=self.controller.GRAY_HOVER_COLOR)
        self.back_button.pack(side="right")


    def _go_back_to_previous_view(self):
        # Ação configurada dinamicamente em on_show
        pass

    def on_show(self, from_view=None, mode="all"):
        """
        Chamado sempre que a tela é exibida.
        """
        self.current_mode = mode
        user_profile = self.controller.get_current_user_profile()
        main_group = user_profile.get("main_group")

        self._configure_access_badge_and_filters(main_group)

        # Configura o botão "Voltar"
        if from_view:
            self.back_button.configure(command=lambda: self.controller.show_frame(from_view))
        else:
            self.back_button.configure(command=lambda: self.controller.show_frame("MainMenuView"))

        self.history_scrollable_frame.configure(label_text="Carregando histórico...")
        self.update_idletasks()
        self.load_history()

    def _configure_access_badge_and_filters(self, main_group):
        """Configura o badge de acesso e os filtros com base no perfil do usuário."""
        if main_group == '67_TELECOM':
            self.access_badge_label.configure(text="🔓 Acesso Completo", text_color="green")
            status_options = ["TODOS", "REGISTRADO", "EM ANÁLISE", "AGUARDANDO TERCEIROS", "PARCIALMENTE RESOLVIDO", "RESOLVIDO", "CANCELADO"]
        else:
            status_options = ["TODOS", "REGISTRADO", "EM ANÁLISE", "PARCIALMENTE RESOLVIDO", "RESOLVIDO", "CANCELADO"]
            if main_group == 'PARTNER':
                self.access_badge_label.configure(text="🔐 Acesso Restrito", text_color="orange")
            elif main_group == 'PREFEITURA':
                self.access_badge_label.configure(text="📋 Acesso Específico", text_color="blue")
            else:
                self.access_badge_label.configure(text="")
        
        self.status_filter.configure(values=status_options)

    def load_history(self):
        """Inicia o carregamento forçado do histórico em uma thread."""
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        self.history_scrollable_frame.configure(label_text="Carregando histórico...")
        self.update_idletasks()
        threading.Thread(target=self._load_history_thread, daemon=True).start()

    def _load_history_thread(self):
        """
        Busca os dados no serviço, armazena no cache e chama a atualização da UI.
        """
        user_email = self.controller.user_email
        all_user_visible_occurrences = self.controller.occurrence_service.get_all_occurrences_for_user(user_email, force_refresh=True)

        self.cached_occurrences = all_user_visible_occurrences
        
        user_profile = self.controller.get_current_user_profile()
        self.after(0, self.filter_history) # Chama o filtro que por sua vez chama o _populate

    def clear_filters(self):
        """Limpa todos os filtros e recarrega a lista completa."""
        self.search_entry.delete(0, "end")
        self.status_filter.set("TODOS")
        self.type_filter.set("TODOS")
        self.start_date_entry.delete(0, "end")
        self.end_date_entry.delete(0, "end")
        self.filter_history()

    def filter_history(self):
        """
        Filtra a lista em cache com base nos critérios de busca.
        """
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
        
        if selected_status != "TODOS":
            filtered_list = [occ for occ in filtered_list if occ.get('Status', '').upper() == selected_status]

        if selected_type != "TODOS":
            type_map = {
                "CHAMADA": "CALL",
                "EQUIPAMENTO": "EQUIP",
                "CHAMADA SIMPLES": "SCALL"
            }
            type_prefix = type_map.get(selected_type)
            if type_prefix:
                filtered_list = [occ for occ in filtered_list if occ.get('ID', '').startswith(type_prefix)]

        try:
            if start_date_str:
                start_date = datetime.strptime(start_date_str, "%d-%m-%Y")
                filtered_list = [occ for occ in filtered_list if datetime.strptime(occ['Data de Registro'], "%Y-%m-%d %H:%M:%S") >= start_date]
            if end_date_str:
                end_date = datetime.strptime(end_date_str, "%d-%m-%Y").replace(hour=23, minute=59, second=59)
                filtered_list = [occ for occ in filtered_list if datetime.strptime(occ['Data de Registro'], "%Y-%m-%d %H:%M:%S") <= end_date]
        except ValueError:
            messagebox.showerror("Erro de Data", "Formato de data inválido. Use DD-MM-AAAA.")
            return

        self._populate_history(filtered_list, self.controller.get_current_user_profile())


    def _populate_history(self, occurrences, user_profile):
        """Preenche a lista de scroll com os cards das ocorrências."""
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()

        if not occurrences:
            self.history_scrollable_frame.configure(label_text="Nenhuma ocorrência encontrada.")
            self.stats_footer_label.configure(text="")
            return

        self.history_scrollable_frame.configure(label_text=f"Exibindo {len(occurrences)} ocorrência(s)")

        for item in occurrences:
            card_frame = ctk.CTkFrame(self.history_scrollable_frame, fg_color="gray20")
            card_frame.pack(fill="x", padx=5, pady=5)
            card_frame.grid_columnconfigure(0, weight=1)

            info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            info_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            item_id = item.get('ID', 'N/A')
            title = item.get('Título da Ocorrência', 'Ocorrência sem Título')
            date_str = item.get('Data de Registro', 'N/A')
            status = item.get('Status', 'N/A')
            registrador = item.get('Nome do Registrador', 'N/A')
            
            formatted_date = date_str
            if date_str != 'N/A':
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    formatted_date = date_obj.strftime("%d-%m-%Y")
                except ValueError:
                    pass

            ctk.CTkLabel(info_frame, text=f"ID: {item_id} - {title}",
                         font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
                         text_color=self.controller.TEXT_COLOR).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Registrado por: {registrador} em {formatted_date}",
                         anchor="w", text_color="gray60").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Status: {status}", anchor="w",
                         font=ctk.CTkFont(weight="bold"), text_color=self.controller.TEXT_COLOR).pack(anchor="w")

            controls_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            controls_frame.grid(row=0, column=1, padx=10, pady=10, sticky="e")

            open_button = ctk.CTkButton(controls_frame, text="Abrir", width=80,
                                        command=partial(self.controller.show_occurrence_details, item_id),
                                        fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                        hover_color=self.controller.ACCENT_COLOR)
            open_button.pack(side="left")

        # Atualiza as estatísticas
        main_group = user_profile.get("main_group")
        stats_text = ""
        if main_group == 'PREFEITURA':
            own_occurrences = [occ for occ in occurrences if occ.get('registradormaingroup', '').upper() == 'PREFEITURA']
            own_count = len(own_occurrences)
            external_count = len(occurrences) - own_count
            stats_text = f"Estatística: {own_count} suas + {external_count} da 67 Telecom"
        
        self.stats_footer_label.configure(text=stats_text)
