import customtkinter as ctk
import json
import webbrowser


class OccurrenceDetailView(ctk.CTkToplevel):
    """
    Uma janela pop-up para exibir os detalhes completos de uma ocorrência.
    """

    def __init__(self, master, occurrence_data):
        super().__init__(master)

        self.title(
            f"Detalhes da Ocorrência: {occurrence_data.get('ID', 'N/A')}")
        self.geometry("600x650")
        self.transient(master)
        self.grab_set()

        scrollable_frame = ctk.CTkScrollableFrame(
            self, label_text="Informações da Ocorrência")
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        row_counter = 0
        for key, value in occurrence_data.items():
            if key in ['Testes', 'Anexos']:
                continue

            key_label = ctk.CTkLabel(
                scrollable_frame, text=f"{key}:", font=ctk.CTkFont(weight="bold"))
            key_label.grid(row=row_counter, column=0,
                           padx=10, pady=5, sticky="ne")

            value_label = ctk.CTkLabel(
                scrollable_frame, text=value, wraplength=400, justify="left")
            value_label.grid(row=row_counter, column=1,
                             padx=10, pady=5, sticky="nw")

            row_counter += 1

        if 'Testes' in occurrence_data and occurrence_data['Testes']:
            try:
                testes = json.loads(occurrence_data['Testes'])
                if testes:
                    tests_header_label = ctk.CTkLabel(
                        scrollable_frame, text="Testes de Ligação:", font=ctk.CTkFont(size=14, weight="bold"))
                    tests_header_label.grid(
                        row=row_counter, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")
                    row_counter += 1

                    tests_container = ctk.CTkFrame(scrollable_frame)
                    tests_container.grid(
                        row=row_counter, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

                    for i, teste in enumerate(testes):
                        card_text = (
                            f"Teste {i+1}:\n"
                            f"  - Horário: {teste.get('horario', 'N/A')}\n"
                            f"  - De: {teste.get('num_a', 'N/A')} ({teste.get('op_a', 'N/A')})\n"
                            f"  - Para: {teste.get('num_b', 'N/A')} ({teste.get('op_b', 'N/A')})\n"
                            f"  - Status: {teste.get('status', 'N/A')}\n"
                            f"  - Obs: {teste.get('obs', 'N/A')}"
                        )
                        test_card = ctk.CTkLabel(
                            tests_container, text=card_text, justify="left", anchor="w")
                        test_card.pack(fill="x", padx=10, pady=5)
                    row_counter += 1
            except (json.JSONDecodeError, TypeError):
                pass

        if 'Anexos' in occurrence_data and occurrence_data['Anexos']:
            try:
                anexos = json.loads(occurrence_data['Anexos'])
                if anexos:
                    anexos_header_label = ctk.CTkLabel(
                        scrollable_frame, text="Anexos:", font=ctk.CTkFont(size=14, weight="bold"))
                    anexos_header_label.grid(
                        row=row_counter, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")
                    row_counter += 1

                    anexos_container = ctk.CTkFrame(scrollable_frame)
                    anexos_container.grid(
                        row=row_counter, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

                    for i, link in enumerate(anexos):
                        # --- ALTERAÇÃO AQUI: Melhora a aparência e funcionalidade do link ---
                        link_font = ctk.CTkFont(underline=True)
                        link_label = ctk.CTkLabel(anexos_container, text=f"Anexo {i+1}: Abrir no navegador",
                                                  text_color=("#1F6AA5", "#58A6FF"), cursor="hand2", font=link_font)
                        link_label.pack(anchor="w", padx=10, pady=2)
                        link_label.bind("<Button-1>", lambda e,
                                        url=link: webbrowser.open_new(url))
                        # --- FIM DA ALTERAÇÃO ---

            except (json.JSONDecodeError, TypeError):
                pass

        close_button = ctk.CTkButton(self, text="Fechar", command=self.destroy)
        close_button.pack(pady=10)
