import customtkinter as ctk
import json

class OccurrenceDetailView(ctk.CTkToplevel):
    """
    Uma janela pop-up para exibir os detalhes completos de uma ocorrência.
    """
    def __init__(self, master, occurrence_data):
        super().__init__(master)
        
        self.title(f"Detalhes da Ocorrência: {occurrence_data.get('ID', 'N/A')}")
        self.geometry("600x650")
        self.transient(master) # Mantém esta janela à frente da principal
        self.grab_set() # Bloqueia interações com a janela principal

        scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Informações da Ocorrência")
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Exibição dos Detalhes ---
        row_counter = 0
        for key, value in occurrence_data.items():
            # Não exibe a lista de testes diretamente aqui, será tratada abaixo
            if key == 'Testes':
                continue

            # Label do Campo (ex: "ID", "Status")
            key_label = ctk.CTkLabel(scrollable_frame, text=f"{key}:", font=ctk.CTkFont(weight="bold"))
            key_label.grid(row=row_counter, column=0, padx=10, pady=5, sticky="ne")

            # Label do Valor
            value_label = ctk.CTkLabel(scrollable_frame, text=value, wraplength=400, justify="left")
            value_label.grid(row=row_counter, column=1, padx=10, pady=5, sticky="nw")
            
            row_counter += 1

        # --- Tratamento Especial para a Lista de Testes ---
        if 'Testes' in occurrence_data and occurrence_data['Testes']:
            try:
                testes = json.loads(occurrence_data['Testes'])
                if testes:
                    # Título para a secção de testes
                    tests_header_label = ctk.CTkLabel(scrollable_frame, text="Testes de Ligação:", font=ctk.CTkFont(size=14, weight="bold"))
                    tests_header_label.grid(row=row_counter, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")
                    row_counter += 1

                    # Frame para conter os cartões de teste
                    tests_container = ctk.CTkFrame(scrollable_frame)
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
                        test_card = ctk.CTkLabel(tests_container, text=card_text, justify="left", anchor="w")
                        test_card.pack(fill="x", padx=10, pady=5)

            except (json.JSONDecodeError, TypeError):
                # Caso o campo 'Testes' não seja um JSON válido
                tests_header_label = ctk.CTkLabel(scrollable_frame, text="Testes:", font=ctk.CTkFont(weight="bold"))
                tests_header_label.grid(row=row_counter, column=0, padx=10, pady=5, sticky="ne")
                value_label = ctk.CTkLabel(scrollable_frame, text="Não foi possível carregar os detalhes dos testes.", wraplength=400, justify="left")
                value_label.grid(row=row_counter, column=1, padx=10, pady=5, sticky="nw")

        close_button = ctk.CTkButton(self, text="Fechar", command=self.destroy)
        close_button.pack(pady=10)
