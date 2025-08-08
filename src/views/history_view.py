# ==============================================================================
# FICHEIRO: src/views/history_view.py
# DESCRIÇÃO: Contém a classe de interface para a tela de histórico de
#            ocorrências, que exibe os registos visíveis ao utilizador.
#            (VERSÃO OTIMIZADA COM CACHE, FILTROS AVANÇADOS E MELHORIAS DE USABILIDADE)
# ==============================================================================

import customtkinter as ctk
import threading
from functools import partial
import json
from datetime import datetime
import re # Importação adicionada para validação com regex

class HistoryView(ctk.CTkFrame):
    """
    Tela para exibir o histórico de ocorrências do utilizador, com cache
    para otimizar a performance da busca e filtros avançados.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.cached_occurrences = [] # Cache para guardar os dados
        
        # --- Configuração da Responsividade ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Linha para o scrollable frame
        
        self.title_label = ctk.CTkLabel(self, text="Histórico de Ocorrências", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")
        
        # --- Frame de Filtros e Busca ---
        filter_frame = ctk.CTkFrame(self)
        filter_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        # Configura as colunas para se expandirem proporcionalmente
        filter_frame.grid_columnconfigure((1, 2, 3), weight=1)

        # Rótulo da seção de filtros
        ctk.CTkLabel(filter_frame, text="Painel de Filtros", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(5, 0))

        # Filtro de Palavra-chave (ocupa mais espaço)
        ctk.CTkLabel(filter_frame, text="Busca por Palavra-Chave:").grid(row=1, column=0, sticky="w", padx=10, pady=(5, 0))
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="ID, título, nome do usuário...")
        self.search_entry.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

        # Filtro por Status
        ctk.CTkLabel(filter_frame, text="Filtrar por Status:").grid(row=1, column=2, sticky="w", padx=10, pady=(5, 0))
        status_options = ["TODOS", "REGISTRADO", "EM ANÁLISE", "AGUARDANDO TERCEIROS", "RESOLVIDO", "CANCELADO"]
        self.status_filter = ctk.CTkComboBox(filter_frame, values=status_options)
        self.status_filter.grid(row=2, column=2, padx=10, pady=(0, 10), sticky="ew")
        self.status_filter.set("TODOS")

        # Filtro por Tipo de Ocorrência
        ctk.CTkLabel(filter_frame, text="Filtrar por Tipo:").grid(row=1, column=3, sticky="w", padx=10, pady=(5, 0))
        type_options = ["TODOS", "CHAMADA", "EQUIPAMENTO", "CHAMADA SIMPLES"]
        self.type_filter = ctk.CTkComboBox(filter_frame, values=type_options)
        self.type_filter.grid(row=2, column=3, padx=10, pady=(0, 10), sticky="ew")
        self.type_filter.set("TODOS")

        # Filtro por Data de Início
        ctk.CTkLabel(filter_frame, text="Filtrar por Data de Início:").grid(row=3, column=0, sticky="w", padx=10, pady=(5, 0))
        self.start_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="AAAA-MM-DD") # Alterado para AAAA-MM-DD
        self.start_date_entry.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        # Vincular validação em tempo real e na perda de foco
        self.start_date_entry.bind("<KeyRelease>", partial(self._validate_date_live, self.start_date_entry))
        self.start_date_entry.bind("<FocusOut>", partial(self._validate_date_live, self.start_date_entry, is_focus_out=True))


        # Filtro por Data de Fim
        ctk.CTkLabel(filter_frame, text="Filtrar por Data de Fim:").grid(row=3, column=1, sticky="w", padx=10, pady=(5, 0))
        self.end_date_entry = ctk.CTkEntry(filter_frame, placeholder_text="AAAA-MM-DD") # Alterado para AAAA-MM-DD
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

        self.apply_filters_button = ctk.CTkButton(button_frame, text="Aplicar Filtros", command=self.filter_history)
        self.apply_filters_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.clear_filters_button = ctk.CTkButton(button_frame, text="Limpar Filtros", command=self.clear_filters, fg_color="gray50", hover_color="gray40")
        self.clear_filters_button.grid(row=0, column=1, padx=(5, 5), sticky="ew")

        self.refresh_button = ctk.CTkButton(button_frame, text="Recarregar Dados", command=self.load_history, fg_color="gray50", hover_color="gray40")
        self.refresh_button.grid(row=0, column=2, padx=(5, 0), sticky="ew")
        
        # --- Frame de Scroll para a Lista de Ocorrências ---
        self.history_scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Carregando histórico...")
        self.history_scrollable_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        back_button = ctk.CTkButton(self, text="Voltar ao Menu", command=lambda: controller.show_frame("MainMenuView"), fg_color="gray50", hover_color="gray40")
        back_button.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

    def _validate_date_live(self, widget, event=None, is_focus_out=False):
        """
        Valida o formato da data em tempo real enquanto o utilizador digita
        e quando o campo perde o foco.
        Retorna True se o formato é (parcialmente) válido, False caso contrário.
        """
        date_str = widget.get()
        is_valid_format = True

        if not date_str: # Campo vazio é considerado válido para digitação ao vivo
            widget.configure(border_color=self.default_border_color)
            return True

        # Regex para AAAA-MM-DD (permite digitação parcial)
        # Ex: "2", "20", "202", "2024", "2024-", "2024-0", "2024-01", "2024-01-", "2024-01-0", "2024-01-01"
        pattern = r"^\d{0,4}(?:-\d{0,2}(?:-\d{0,2})?)?$"
        if not re.match(pattern, date_str):
            is_valid_format = False
        
        # Tenta a validação completa apenas se o comprimento for o esperado (10 caracteres para AAAA-MM-DD)
        # ou se o foco saiu do campo (para pegar datas incompletas mas que o regex aceitou)
        if (len(date_str) == 10 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str)) or is_focus_out:
            try:
                datetime.strptime(date_str, "%Y-%m-%d") # Alterado para %Y-%m-%d
                is_valid_format = True
            except ValueError:
                is_valid_format = False

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

        self.load_history()

    def load_history(self):
        """Inicia o carregamento FORÇADO do histórico a partir do Google Sheets."""
        self.history_scrollable_frame.configure(label_text="Carregando histórico...")
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self._load_history_thread, daemon=True).start()

    def _load_history_thread(self):
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

        self.filter_history() # Chama a função para re-aplicar o filtro (sem termos)

    def filter_history(self):
        """
        Filtra a lista JÁ CARREGADA (cache) com base no termo de pesquisa e nos novos filtros.
        Inclui validação final dos campos de data.
        """
        # Valida os campos de data antes de prosseguir com a filtragem completa
        start_date_valid = self._validate_date_live(self.start_date_entry, is_focus_out=True)
        end_date_valid = self._validate_date_live(self.end_date_entry, is_focus_out=True)

        if not start_date_valid or not end_date_valid:
            messagebox.showwarning("Formato de Data Inválido", "Por favor, corrija o formato das datas (AAAA-MM-DD) antes de aplicar os filtros.")
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
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else datetime.min # Alterado para %Y-%m-%d
                # Se a data de fim não for fornecida, usa a data máxima possível,
                # garantindo que inclui o dia inteiro (até 23:59:59)
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59) if end_date_str else datetime.max # Alterado para %Y-%m-%d

                filtered_list = [
                    occ for occ in filtered_list
                    if 'Data de Registro' in occ and \
                       start_date <= datetime.strptime(occ['Data de Registro'].split(' ')[0], "%Y-%m-%d") <= end_date # Mantém %Y-%m-%d para a parte da data
                ]

            except ValueError:
                messagebox.showwarning("Formato de Data Inválido", "Ocorreu um erro inesperado na validação da data. Por favor, verifique o formato AAAA-MM-DD.")
                return

        self._populate_history(filtered_list, self.controller.get_current_user_profile(),
                               search_term=search_term, selected_status=selected_status,
                               selected_type=selected_type,
                               start_date_str=start_date_str, end_date_str=end_date_str)

    def _populate_history(self, occurrences, user_profile, search_term="", selected_status="TODOS", selected_type="TODOS", start_date_str="", end_date_str=""):
        """Preenche a lista de scroll com os cards das ocorrências."""
        main_group = user_profile.get("main_group")
        if main_group == '67_TELECOM':
            self.title_label.configure(text="Histórico Geral de Ocorrências")
        elif main_group in ['PARTNER', 'PREFEITURA']:
            company = user_profile.get("company", "N/A")
            self.title_label.configure(text=f"Histórico de Ocorrências: {company}")
        
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()

        # Feedback visual no rótulo da lista de resultados
        if not occurrences:
            self.history_scrollable_frame.configure(label_text="Nenhuma ocorrência encontrada para os filtros aplicados.")
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

        self.history_scrollable_frame.configure(label_text=label_text)
        
        for item in occurrences:
            item_id = item.get('ID', 'N/A')
            
            card_frame = ctk.CTkFrame(self.history_scrollable_frame)
            card_frame.pack(fill="x", padx=5, pady=5)
            card_frame.grid_columnconfigure(0, weight=1)

            info_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            info_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            title = item.get('Título da Ocorrência', 'Ocorrência sem Título')
            date_str = item.get('Data de Registro', 'N/A')
            status = item.get('Status', 'N/A')
            
            # Obtenha a data de registro e formate-a
            formatted_date = 'N/A'
            if date_str != 'N/A':
                # Converte a string (ex: '2025-08-08 16:37:59') para um objeto datetime
                try:
                    # Converte a string do banco de dados (YYYY-MM-DD HH:MM:SS)
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    # Formata o objeto datetime para 'AAAA-MM-DD' para exibição padronizada
                    formatted_date = date_obj.strftime("%Y-%m-%d") # Alterado para AAAA-MM-DD
                except ValueError:
                    # Em caso de erro, mantém a string original ou define como 'N/A'
                    formatted_date = date_str

            ctk.CTkLabel(info_frame, text=f"ID: {item_id} - {title}", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Registrado por: {item.get('Nome do Registrador', 'N/A')} em {formatted_date}", anchor="w", text_color="gray60").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Status: {status}", anchor="w", font=ctk.CTkFont(weight="bold")).pack(anchor="w")

            open_button = ctk.CTkButton(card_frame, text="Abrir", width=80, command=partial(self.controller.show_occurrence_details, item_id))
            open_button.grid(row=0, column=1, padx=10, pady=10, sticky="e")
