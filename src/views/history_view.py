# ==============================================================================
# FICHEIRO: src/views/history_view.py
# DESCRIÇÃO: Contém a classe de interface para a tela de histórico de
#            ocorrências, que exibe os registos visíveis ao utilizador.
#            (VERSÃO OTIMIZADA COM CACHE, FILTROS AVANÇADOS, MELHORIAS DE USABILIDADE E CORES)
# ==============================================================================

import customtkinter as ctk
import threading
from functools import partial
import json
from tkinter import messagebox
from datetime import datetime
import re # Importação adicionada para validação com regex

class HistoryView(ctk.CTkFrame):
    """
    Tela para exibir o histórico de ocorrências do utilizador, com cache
    para otimizar a performance da busca e filtros avançados.
    """
    def __init__(self, parent, controller):
        super().__init__(parent) # Removido fg_color do super().__init__
        self.controller = controller

        # Definir a cor de fundo após a inicialização do super
        self.configure(fg_color=self.controller.BASE_COLOR)

        self.cached_occurrences = [] # Cache para guardar os dados

        # --- Configuração da Responsividade ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Linha para o scrollable frame

        self.title_label = ctk.CTkLabel(self, text="Histórico de Ocorrências",
                                        font=ctk.CTkFont(size=24, weight="bold"),
                                        text_color=self.controller.TEXT_COLOR)
        self.title_label.grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")

        # --- Frame de Filtros e Busca ---
        filter_frame = ctk.CTkFrame(self, fg_color="gray15") # Fundo do frame de filtros
        filter_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        # Configura as colunas para se expandirem proporcionalmente
        filter_frame.grid_columnconfigure((1, 2, 3), weight=1)

        # Rótulo da seção de filtros
        ctk.CTkLabel(filter_frame, text="Painel de Filtros",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(5, 0))

        # Filtro de Palavra-chave (ocupa mais espaço)
        ctk.CTkLabel(filter_frame, text="Busca por Palavra-Chave:", text_color=self.controller.TEXT_COLOR).grid(row=1, column=0, sticky="w", padx=10, pady=(5, 0))
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="ID, título, nome do usuário...",
                                         fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                         border_color="gray40")
        self.search_entry.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

        # Filtro por Status
        ctk.CTkLabel(filter_frame, text="Filtrar por Status:", text_color=self.controller.TEXT_COLOR).grid(row=1, column=2, sticky="w", padx=10, pady=(5, 0))
        status_options = ["TODOS", "REGISTRADO", "EM ANÁLISE", "AGUARDANDO TERCEIROS", "PARCIALMENTE RESOLVIDO", "RESOLVIDO", "CANCELADO"] # Adicionado o novo status
        self.status_filter = ctk.CTkComboBox(filter_frame, values=status_options,
                                             fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                             border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                             button_hover_color=self.controller.ACCENT_COLOR)
        self.status_filter.grid(row=2, column=2, padx=10, pady=(0, 10), sticky="ew")
        self.status_filter.set("TODOS")

        # Filtro por Tipo de Ocorrência
        ctk.CTkLabel(filter_frame, text="Filtrar por Tipo:", text_color=self.controller.TEXT_COLOR).grid(row=1, column=3, sticky="w", padx=10, pady=(5, 0))
        type_options = ["TODOS", "CHAMADA", "EQUIPAMENTO", "CHAMADA SIMPLES"]
        self.type_filter = ctk.CTkComboBox(filter_frame, values=type_options,
                                           fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                           border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                           button_hover_color=self.controller.ACCENT_COLOR)
        self.type_filter.grid(row=2, column=3, padx=10, pady=(0, 10), sticky="ew")
        self.type_filter.set("TODOS")

        # Filtro por Data de Início
        ctk.CTkLabel(filter_frame, text="Filtrar por Data de Início:", text_color=self.controller.TEXT_COLOR).grid(row=3, column=0, sticky="w", padx=10, pady=(5, 0))
        self.start_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="DD-MM-AAAA",
                                             fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                             border_color="gray40")
        self.start_date_entry.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        # Vincular validação em tempo real e na perda de foco
        self.start_date_entry.bind("<KeyRelease>", partial(self._validate_date_live, self.start_date_entry))
        self.start_date_entry.bind("<FocusOut>", partial(self._validate_date_live, self.start_date_entry, is_focus_out=True))


        # Filtro por Data de Fim
        ctk.CTkLabel(filter_frame, text="Filtrar por Data de Fim:", text_color=self.controller.TEXT_COLOR).grid(row=3, column=1, sticky="w", padx=10, pady=(5, 0))
        self.end_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="DD-MM-AAAA",
                                           fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                           border_color="gray40")
        self.end_date_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=(0, 10))
        # Vincular validação em tempo real e na perda de foco
        self.end_date_entry.bind("<KeyRelease>", partial(self._validate_date_live, self.end_date_entry))
        self.end_date_entry.bind("<FocusOut>", partial(self._validate_date_live, self.end_date_entry, is_focus_out=True))


        # Armazena a cor da borda padrão para restauração
        self.default_border_color = self.start_date_entry.cget("border_color")

        # Frame para botões de ação (alterado para row 5)
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

        # --- Frame de Scroll para a Lista de Ocorrências ---
        self.history_scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Carregando histórico...",
                                                               fg_color="gray10",
                                                               label_text_color=self.controller.TEXT_COLOR)
        self.history_scrollable_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        back_button = ctk.CTkButton(self, text="Voltar ao Menu", command=lambda: controller.show_frame("MainMenuView"),
                                    fg_color=self.controller.GRAY_BUTTON_COLOR, text_color=self.controller.TEXT_COLOR,
                                    hover_color=self.controller.GRAY_HOVER_COLOR)
        back_button.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

    def _validate_date_live(self, widget, event=None, is_focus_out=False):
        """
        Valida e formata o formato da data em tempo real e quando o campo perde o foco.
        """
        date_str = widget.get()
        # Se o campo estiver vazio, retorna para não validar
        if not date_str:
            widget.configure(border_color=self.default_border_color)
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
            widget.configure(border_color=self.default_border_color)
        else:
            widget.configure(border_color="red")

        return is_valid_format

    def on_show(self):
        """Chamado sempre que a tela é exibida."""
        self.search_entry.delete(0, "end")
        self.status_filter.set("TODOS") # Reseta o filtro de status
        self.type_filter.set("TODOS")   # Reseta o filtro de tipo
        self.start_date_entry.delete(0, "end") # Limpa o campo de data de início
        self.end_date_entry.delete(0, "end")   # Limpa o campo de data de fim

        # Garante que as bordas voltem ao normal ao exibir a tela
        self.start_date_entry.configure(border_color=self.default_border_color)
        self.end_date_entry.configure(border_color=self.default_border_color)

        # Configura a mensagem de carregamento antes de iniciar a thread
        self.history_scrollable_frame.configure(label_text="Carregando histórico...")
        self.update_idletasks() # Força a atualização da UI
        self.load_history()

    def load_history(self):
        """Inicia o carregamento FORÇADO do histórico a partir do Google Sheets."""
        # A mensagem "Carregando histórico..." já deve ter sido definida antes de chamar esta função
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self._load_history_thread, daemon=True).start()

    def _load_history_thread(self,):
        """Busca os dados no serviço, armazena no cache e chama a atualização da UI."""
        self.cached_occurrences = self.controller.get_all_occurrences(force_refresh=True) # Força o refresh no controller também
        user_profile = self.controller.get_current_user_profile()
        self.after(0, self._populate_history, self.cached_occurrences, user_profile)

    def clear_filters(self):
        """Reseta todos os campos de filtro para o estado padrão e re-aplica a filtragem."""
        self.search_entry.delete(0, "end")
        self.status_filter.set("TODOS")
        self.type_filter.set("TODOS")
        self.start_date_entry.delete(0, "end") # Limpa o campo de data de início
        self.end_date_entry.delete(0, "end")   # Limpa o campo de data de fim

        # Garante que as bordas voltem ao normal após limpar os filtros
        self.start_date_entry.configure(border_color=self.default_border_color)
        self.end_date_entry.configure(border_color=self.default_border_color)

        self.filter_history() # Chama a função para re-aplica o filtro (sem termos)

    def filter_history(self):
        """
        Filtra a lista JÁ CARREGADA (cache) com base no termo de pesquisa e nos novos filtros.
        Inclui validação final dos campos de data.
        """
        # Valida os campos de data antes de prosseguir com a filtragem completa
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

        # 1. Filtrar por termo de busca
        if search_term:
            filtered_list = [
                occ for occ in filtered_list
                if any(search_term in str(v).lower() for v in occ.values())
            ]

        # 2. Filtrar por status
        if selected_status != "TODOS":
            filtered_list = [
                occ for occ in filtered_list
                if occ.get('Status', '').upper() == selected_status
            ]

        # 3. Filtrar por tipo de ocorrência
        if selected_type != "TODOS":
            # Usamos o ID para determinar o tipo de ocorrência
            if selected_type == "CHAMADA":
                # Ocorrências detalhadas (prefixo 'CALL')
                filtered_list = [occ for occ in filtered_list if 'CALL' in occ.get('ID', '') and 'SCALL' not in occ.get('ID', '')]
            elif selected_type == "CHAMADA SIMPLES":
                # Ocorrências simples (prefixo 'SCALL')
                filtered_list = [occ for occ in filtered_list if 'SCALL' in occ.get('ID', '')]
            elif selected_type == "EQUIPAMENTO":
                # Ocorrências de equipamento (prefixo 'EQUIP')
                filtered_list = [occ for occ in filtered_list if 'EQUIP' in occ.get('ID', '')]

        # 4. Filtrar por intervalo de datas
        if start_date_str or end_date_str:
            try:
                # Se a data de início não for fornecida, usa a data mínima possível
                start_date = datetime.strptime(start_date_str, "%d-%m-%Y") if start_date_str else datetime.min # Alterado para %d-%m-%Y
                # Se a data de fim não for fornecida, usa a data máxima possível,
                # garantindo que inclui o dia inteiro (até 23:59:59)
                end_date = datetime.strptime(end_date_str, "%d-%m-%Y").replace(hour=23, minute=59, second=59) if end_date_str else datetime.max # Alterado para %d-%m-%Y

                filtered_list = [
                    occ for occ in filtered_list
                    if 'Data de Registro' in occ and \
                       start_date <= datetime.strptime(occ['Data de Registro'].split(' ')[0], "%Y-%m-%d") <= end_date # Mantém %Y-%m-%d para a parte da data
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
        sub_group = user_profile.get("sub_group") # Obter o sub_group
        is_admin_or_super_admin = (main_group == "67_TELECOM" and (sub_group == "ADMIN" or sub_group == "SUPER_ADMIN"))

        if main_group == '67_TELECOM':
            self.title_label.configure(text="Histórico Geral de Ocorrências")
        elif main_group in ['PARTNER', 'PREFEITURA']:
            company = user_profile.get("company", "N/A")
            self.title_label.configure(text=f"Histórico de Ocorrências: {company}")

        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()

        # Feedback visual no rótulo da lista de resultados
        if not occurrences:
            self.history_scrollable_frame.configure(label_text="Nenhuma ocorrência encontrada para os filtros aplicados.",
                                                    label_text_color=self.controller.TEXT_COLOR)
            return

        filter_summary = []
        if search_term:
            filter_summary.append(f"Busca: '{search_term}'")
        if selected_status != "TODOS":
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

            # --- Lógica de obtenção do título para exibição no histórico ---
            # Tenta obter o título da chave 'Título da Ocorrência' (espera-se que venha normalizado do sheets_service)
            title = item.get('Título da Ocorrência')

            # Se o título não for encontrado ou estiver vazio, tenta gerar um fallback
            if not title or str(title).strip() == "":
                item_id_prefix = item_id.split('-')[0] if '-' in item_id else item_id

                if item_id_prefix == 'SCALL':
                    title = f"Chamada Simples de {item.get('Origem', 'N/A')} para {item.get('Destino', 'N/A')}"
                elif item_id_prefix == 'EQUIP':
                    title = item.get('Tipo de Equipamento', f"Equipamento {item_id}")
                elif item_id_prefix == 'CALL':
                    title = f"Chamada Detalhada {item_id}"
                else:
                    title = 'Ocorrência sem Título' # Fallback genérico final
            # --- Fim da lógica de obtenção do título ---

            date_str = item.get('Data de Registro', 'N/A')
            status = item.get('Status', 'N/A')

            # Obtenha a data de registro e formate-a
            formatted_date = 'N/A'
            if date_str != 'N/A':
                # Converte a string do banco de dados (YYYY-MM-DD HH:MM:%S)
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    # Formata o objeto datetime para 'DD-MM-AAAA' para exibição
                    formatted_date = date_obj.strftime("%d-%m-%Y") # ALTERADO para o formato brasileiro
                except ValueError:
                    # Em caso de erro, mantém a string original ou define como 'N/A'
                    formatted_date = date_str

            ctk.CTkLabel(info_frame, text=f"ID: {item_id} - {title}",
                         font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
                         text_color=self.controller.TEXT_COLOR).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Registrado por: {item.get('Nome do Registrador', 'N/A')} em {formatted_date}",
                         anchor="w", text_color="gray60").pack(anchor="w")

            # Frame para controles (status combo e botão Abrir)
            controls_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            controls_frame.grid(row=0, column=1, padx=10, pady=10, sticky="e")

            if is_admin_or_super_admin:
                # ComboBox para editar o status
                status_combo = ctk.CTkComboBox(controls_frame, values=status_options_for_editing, width=180,
                                               fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                               border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                               button_hover_color=self.controller.ACCENT_COLOR,
                                               command=partial(self._on_status_change_from_history, item_id))
                status_combo.set(status) # Define o status atual
                status_combo.pack(side="left", padx=(0, 10))
            else:
                # Se não for admin, apenas exibe o status como label
                ctk.CTkLabel(info_frame, text=f"Status: {status}", anchor="w",
                             font=ctk.CTkFont(weight="bold"), text_color=self.controller.TEXT_COLOR).pack(anchor="w")


            open_button = ctk.CTkButton(controls_frame, text="Abrir", width=80,
                                        command=partial(self.controller.show_occurrence_details, item_id),
                                        fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                        hover_color=self.controller.ACCENT_COLOR)
            open_button.pack(side="left")

    def _on_status_change_from_history(self, occurrence_id, new_status):
        """
        Chamado quando o status de uma ocorrência é alterado no ComboBox do histórico.
        """
        # Confirmação antes de atualizar
        if messagebox.askyesno("Confirmar Alteração de Status",
                               f"Tem certeza que deseja alterar o status da ocorrência {occurrence_id} para '{new_status}'?"):
            self.controller.update_occurrence_status_from_history(occurrence_id, new_status)
        else:
            # Se o usuário cancelar, recarrega o histórico para reverter o ComboBox
            self.load_history()
