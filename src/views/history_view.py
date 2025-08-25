# ==============================================================================
# FICHEIRO: src/views/history_view.py
# DESCRIÇÃO: Contém a classe de interface para a tela de histórico de ocorrências.
#            (VERSÃO CORRIGIDA PARA ERRO DE LAYOUT)
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
    Tela para exibir o histórico de ocorrências do utilizador.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        self.cached_occurrences = []
        self.return_to_view = "MainMenuView"

        # --- Configuração da Responsividade ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Linha para o scrollable frame

        self.title_label = ctk.CTkLabel(self, text="Histórico de Ocorrências",
                                        font=ctk.CTkFont(size=24, weight="bold"),
                                        text_color=self.controller.TEXT_COLOR)
        self.title_label.grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")

        # --- Frame de Filtros e Busca ---
        filter_frame = ctk.CTkFrame(self, fg_color="gray15")
        filter_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        filter_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(filter_frame, text="Buscar no Histórico:",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))

        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Digite para buscar por ID, título, nome, etc...")
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))
        self.search_entry.bind("<KeyRelease>", self._filter_history_live)


        # --- Frame de Scroll para a Lista de Ocorrências ---
        self.history_scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Carregando histórico...")
        self.history_scrollable_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        # Botão de voltar
        self.back_button = ctk.CTkButton(self, text="Voltar", command=self._go_back_to_previous_view)
        self.back_button.grid(row=3, column=0, padx=20, pady=(10, 10), sticky="ew")

    def _go_back_to_previous_view(self):
        self.controller.show_frame(self.return_to_view)

    def on_show(self, from_view=None):
        if from_view == "AdminDashboardView":
            self.return_to_view = "AdminDashboardView"
        else:
            self.return_to_view = "MainMenuView"
        self.load_history()

    def load_history(self):
        self.history_scrollable_frame.configure(label_text="Carregando histórico...")
        self.search_entry.delete(0, "end")
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self._load_history_thread, daemon=True).start()

    def _load_history_thread(self):
        self.cached_occurrences = self.controller.get_all_occurrences(force_refresh=True)
        user_profile = self.controller.get_current_user_profile()
        self.after(0, self._populate_history, self.cached_occurrences, user_profile)

    def _filter_history_live(self, event=None):
        """Filtra a lista de ocorrências em tempo real enquanto o utilizador digita."""
        search_term = self.search_entry.get().lower()
        if not search_term:
            filtered_list = self.cached_occurrences
        else:
            filtered_list = [
                occ for occ in self.cached_occurrences
                if any(search_term in str(v).lower() for v in occ.values())
            ]
        self._populate_history(filtered_list, self.controller.get_current_user_profile())


    def _populate_history(self, occurrences, user_profile):
        """Preenche a lista de scroll com os cards das ocorrências."""
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()

        if not occurrences:
            self.history_scrollable_frame.configure(label_text="Nenhuma ocorrência encontrada.")
            return
        self.history_scrollable_frame.configure(label_text=f"Exibindo {len(occurrences)} ocorrência(s)")

        for item in occurrences:
            item_id = item.get('ID', 'N/A')
            card_frame = ctk.CTkFrame(self.history_scrollable_frame, fg_color="gray20")
            card_frame.pack(fill="x", padx=5, pady=5) # .pack() é seguro aqui
            card_frame.grid_columnconfigure(0, weight=1)

            info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            info_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            title = item.get('Título da Ocorrência', 'Ocorrência sem Título')
            date_str = item.get('Data de Registro', 'N/A')
            status = item.get('Status', 'N/A')

            ctk.CTkLabel(info_frame, text=f"ID: {item_id} - {title}", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Registrado por: {item.get('Nome do Registrador', 'N/A')} em {date_str}", text_color="gray60").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Status: {status}", font=ctk.CTkFont(weight="bold")).pack(anchor="w")

            controls_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            controls_frame.grid(row=0, column=1, padx=10, pady=10, sticky="e")

            open_button = ctk.CTkButton(controls_frame, text="Abrir", width=80,
                                        command=partial(self.controller.show_occurrence_details, item_id))
            open_button.pack(side="left")
