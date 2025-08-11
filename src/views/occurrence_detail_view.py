# ==============================================================================
# FICHEiro: src/views/occurrence_detail_view.py
# DESCRIÇÃO: Contém a classe de interface para a janela (Toplevel) que exibe
#            os detalhes completos de uma ocorrência. (ATUALIZADA COM CORES)
# ==============================================================================

import customtkinter as ctk
import json
import webbrowser

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
        for key, value in occurrence_data.items():
            # Campos com tratamento especial são ignorados neste loop
            if key in ['Testes', 'Anexos']:
                continue

            key_label = ctk.CTkLabel(scrollable_frame, text=f"{key}:",
                                     font=ctk.CTkFont(weight="bold"),
                                     text_color=self.controller.TEXT_COLOR)
            key_label.grid(row=row_counter, column=0, padx=10, pady=5, sticky="ne")

            value_label = ctk.CTkLabel(scrollable_frame, text=value, wraplength=400, justify="left",
                                       text_color="gray70") # Texto de valor um pouco mais claro
            value_label.grid(row=row_counter, column=1, padx=10, pady=5, sticky="nw")

            row_counter += 1

        # --- Exibição dos Testes de Ligação ---
        if 'Testes' in occurrence_data and occurrence_data['Testes']:
            try:
                # O campo 'Testes' é uma string JSON, então precisa ser convertido
                testes = json.loads(occurrence_data['Testes'])
                if testes:
                    tests_header_label = ctk.CTkLabel(scrollable_frame, text="Testes de Ligação:",
                                                      font=ctk.CTkFont(size=14, weight="bold"),
                                                      text_color=self.controller.TEXT_COLOR)
                    tests_header_label.grid(row=row_counter, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")
                    row_counter += 1

                    tests_container = ctk.CTkFrame(scrollable_frame, fg_color="gray20") # Fundo do container de testes
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
                # Ignora erros se o JSON for inválido
                pass

        # --- Exibição dos Anexos ---
        if 'Anexos' in occurrence_data and occurrence_data['Anexos']:
            try:
                # O campo 'Anexos' também é uma string JSON
                anexos = json.loads(occurrence_data['Anexos'])
                if anexos:
                    anexos_header_label = ctk.CTkLabel(scrollable_frame, text="Anexos:",
                                                      font=ctk.CTkFont(size=14, weight="bold"),
                                                      text_color=self.controller.TEXT_COLOR)
                    anexos_header_label.grid(row=row_counter, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")
                    row_counter += 1

                    anexos_container = ctk.CTkFrame(scrollable_frame, fg_color="gray20") # Fundo do container de anexos
                    anexos_container.grid(row=row_counter, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

                    for i, link in enumerate(anexos):
                        # Cria um label que parece e age como um link
                        link_font = ctk.CTkFont(underline=True)
                        link_label = ctk.CTkLabel(
                            anexos_container, 
                            text=f"Anexo {i+1}: Abrir no navegador",
                            text_color=(self.controller.PRIMARY_COLOR, self.controller.ACCENT_COLOR), # Usar cores de destaque/acento
                            cursor="hand2", 
                            font=link_font
                        )
                        link_label.pack(anchor="w", padx=10, pady=2)
                        # Associa o clique do mouse à função que abre o link
                        link_label.bind("<Button-1>", lambda e, url=link: webbrowser.open_new(url))

            except (json.JSONDecodeError, TypeError):
                # Ignora erros se o JSON for inválido
                pass

        # --- Botão de Fechar ---
        close_button = ctk.CTkButton(self, text="Fechar", command=self.destroy,
                                     fg_color=self.controller.GRAY_BUTTON_COLOR,
                                     text_color=self.controller.TEXT_COLOR,
                                     hover_color=self.controller.GRAY_HOVER_COLOR)
        close_button.pack(pady=10)

