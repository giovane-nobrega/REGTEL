# ==============================================================================
# FICHEiro: src/views/occurrence_detail_view.py
# DESCRIÇÃO: Contém a classe de interface para a janela (Toplevel) que exibe
#            os detalhes completos de uma ocorrência. (VERSÃO CORRIGIDA PARA DUPLICAÇÃO DE CAMPOS)
# ==============================================================================

import customtkinter as ctk
import json
import webbrowser
from datetime import datetime # Importação adicionada

class OccurrenceDetailView(ctk.CTkToplevel):
    """
    Uma janela pop-up (Toplevel) para exibir os detalhes completos de uma ocorrência,
    incluindo todos os campos, testes de ligação e links para anexos.
    """
    def __init__(self, master, occurrence_data):
        super().__init__(master)
        self.master = master # Referência ao master (App)
        
        self.title(f"Detalhes da Ocorrência: {occurrence_data.get('ID', 'N/A')}")
        self.geometry("600x650")
        # Garante que a janela fique sempre à frente da janela principal
        self.transient(master)
        self.grab_set()

        # Acessar as cores do controller (App)
        self.controller = master # Master é a instância de App
        
        # Definir a cor de fundo após a inicialização do super
        self.configure(fg_color=self.controller.BASE_COLOR)

        scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Informações da Ocorrência",
                                                  fg_color=self.controller.BASE_COLOR, # Cor de fundo base
                                                  label_text_color=self.controller.TEXT_COLOR)
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Exibição dos Dados Gerais ---
        row_counter = 0
        # Lista de chaves a serem ignoradas no loop de exibição geral
        # Inclui 'Testes' e 'Anexos' (chaves originais) e suas possíveis normalizações em minúsculas
        keys_to_ignore_list = ['Testes', 'Anexos', 'testes', 'anexos']
        
        # Para evitar duplicações vindas do _get_all_records_safe, 
        # vamos criar um conjunto para rastrear as chaves já exibidas (case-insensitive)
        shown_keys = set()

        for key, value in occurrence_data.items():
            # Ignorar se a chave (case-insensitive) estiver na lista de ignorados
            if key.lower() in (k.lower() for k in keys_to_ignore_list):
                continue

            # Ignorar chaves que já foram exibidas (evita duplicadas)
            if key.lower() in shown_keys:
                continue
            
            # Adiciona a chave (em minúsculas) ao conjunto de chaves já exibidas
            shown_keys.add(key.lower())

            display_key = key
            display_value = value

            # Formatação especial para algumas chaves
            if key.lower() == 'data de registro': # Usa lower() para ser compatível com chaves normalizadas se necessário
                try:
                    date_obj = datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
                    display_value = date_obj.strftime("%d-%m-%Y %H:%M:%S")
                except ValueError:
                    pass
            elif key.lower() == 'status': # Usa lower()
                display_value = str(value).upper()

            key_label = ctk.CTkLabel(scrollable_frame, text=f"{display_key}:", font=ctk.CTkFont(weight="bold"),
                                     text_color=self.controller.TEXT_COLOR)
            key_label.grid(row=row_counter, column=0, padx=10, pady=5, sticky="ne")

            value_label = ctk.CTkLabel(scrollable_frame, text=display_value, wraplength=400, justify="left",
                                       text_color="gray70")
            value_label.grid(row=row_counter, column=1, padx=10, pady=5, sticky="nw")

            row_counter += 1

        # --- Exibição dos Testes de Ligação ---
        # Acessa a chave original 'Testes' ou a normalizada 'testes'
        testes_data = occurrence_data.get('Testes') or occurrence_data.get('testes')
        if testes_data:
            try:
                # O campo 'Testes' é uma string JSON, então precisa ser convertido
                testes = json.loads(testes_data)
                if testes:
                    tests_header_label = ctk.CTkLabel(scrollable_frame, text="Testes de Ligação:", font=ctk.CTkFont(size=14, weight="bold"),
                                                      text_color=self.controller.TEXT_COLOR)
                    tests_header_label.grid(row=row_counter, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")
                    row_counter += 1

                    tests_container = ctk.CTkFrame(scrollable_frame, fg_color="gray20")
                    tests_container.grid(row=row_counter, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

                    for i, teste in enumerate(testes):
                        card_text = (
                            f"Teste {i+1}:\n"
                            f"  - Horário: {teste.get('horario', 'N/A')}\n"
                            f"  - De: {teste.get('num_a', 'N/A')} ({teste.get('op_a', 'N/A')})\n"
                            f"  - Para: {teste.get('num_b', 'N/A')} ({teste.get('op_b', 'N/A')})\n"
                            f"  - Status: {teste.get('status', 'N/A')}\n"
                            f"  - Obs: {teste.get('obs', 'N/A')}"
                        )
                        test_card = ctk.CTkLabel(tests_container, text=card_text, justify="left", anchor="w",
                                                 text_color=self.controller.TEXT_COLOR)
                        test_card.pack(fill="x", padx=10, pady=5)
                    row_counter += 1
            except (json.JSONDecodeError, TypeError):
                pass # Ignora erros se o JSON for inválido

        # --- Exibição dos Anexos ---
        # Acessa a chave original 'Anexos' ou a normalizada 'anexos'
        anexos_data = occurrence_data.get('Anexos') or occurrence_data.get('anexos')
        if anexos_data:
            try:
                # O campo 'Anexos' também é uma string JSON
                anexos = json.loads(anexos_data)
                if anexos:
                    anexos_header_label = ctk.CTkLabel(scrollable_frame, text="Anexos:", font=ctk.CTkFont(size=14, weight="bold"),
                                                      text_color=self.controller.TEXT_COLOR)
                    anexos_header_label.grid(row=row_counter, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")
                    row_counter += 1

                    anexos_container = ctk.CTkFrame(scrollable_frame, fg_color="gray20")
                    anexos_container.grid(row=row_counter, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

                    for i, link in enumerate(anexos):
                        # Cria um label que parece e age como um link
                        link_font = ctk.CTkFont(underline=True)
                        link_label = ctk.CTkLabel(
                            anexos_container, 
                            text=f"Anexo {i+1}: Abrir no navegador",
                            text_color=(self.controller.PRIMARY_COLOR, self.controller.ACCENT_COLOR), 
                            cursor="hand2", 
                            font=link_font
                        )
                        link_label.pack(anchor="w", padx=10, pady=2)
                        # Associa o clique do mouse à função que abre o link
                        link_label.bind("<Button-1>", lambda e, url=link: webbrowser.open_new(url))
                    row_counter += 1
            except (json.JSONDecodeError, TypeError):
                pass # Ignora erros se o JSON for inválido

        # --- Botão de Fechar ---
        close_button = ctk.CTkButton(self, text="Fechar", command=self.destroy,
                                     fg_color=self.controller.GRAY_BUTTON_COLOR,
                                     text_color=self.controller.TEXT_COLOR,
                                     hover_color=self.controller.GRAY_HOVER_COLOR)
        close_button.pack(pady=10)
