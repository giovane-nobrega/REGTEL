# ==============================================================================
# FICHEiro: src/views/occurrence_detail_view.py
# DESCRIÇÃO: Contém a classe de interface para a janela (Toplevel) que exibe
#            os detalhes completos de uma ocorrência. (VERSÃO CORRIGIDA PARA DUPLICAÇÃO DE CAMPOS)
# ==============================================================================

import customtkinter as ctk
import json
import webbrowser
from datetime import datetime # Importação adicionada
from tkinter import messagebox # Importado para mensagens de erro/aviso

class OccurrenceDetailView(ctk.CTkToplevel):
    """
    Uma janela pop-up (Toplevel) para exibir os detalhes completos de uma ocorrência,
    incluindo todos os campos, testes de ligação e links para anexos.
    """
    def __init__(self, master, occurrence_data):
        super().__init__(master)
        self.master = master # Referência ao master (App)
        self.occurrence_data = occurrence_data # Armazena os dados da ocorrência

        # print(f"DEBUG (OccurrenceDetailView): occurrence_data recebido: {self.occurrence_data}") # DEBUG PRINT REMOVIDO

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
        # Lista de chaves a serem ignoradas no loop de exibição geral (normalizadas)
        keys_to_ignore_normalized = {'testes', 'anexos'}

        # Mapeamento para preferir a capitalização original para exibição
        # Adicione aqui qualquer chave que possa vir duplicada com capitalização diferente
        display_key_preference = {
            'descrição do problema': 'Descrição do problema',
            'operadora a': 'Operadora A',
            'operadora b': 'Operadora B',
            'título da ocorrência': 'Título da Ocorrência',
            'data de registro': 'Data de Registro',
            'status': 'Status',
            'id': 'ID',
            'nome do registrador': 'Nome do Registrador', # Mantido, mas o SheetsService agora salva como 'Nome Completo'
            'nome completo': 'Nome Completo', # Chave que o SheetsService agora salva
            'username do registrador': 'Username do Registrador',
            'e-mail do registrador': 'E-mail do Registrador',
            'username': 'Username',
            'email': 'Email',
            'main_group': 'Grupo Principal',
            'sub_group': 'Subgrupo',
            'company': 'Empresa/Departamento',
            'tipo': 'Tipo', # Para equipamentos
            'modelo': 'Modelo', # Para equipamentos
            'ramal': 'Ramal', # Para equipamentos
            'localizacao': 'Localização', # Para equipamentos
            'origem': 'Origem', # Para chamadas simples
            'destino': 'Destino', # Para chamadas simples
            'registrador main group': 'Registrador Main Group',
            'registrador company': 'Registrador Company',
        }

        # Coletar todas as chaves normalizadas únicas dos dados da ocorrência
        unique_normalized_keys = set()
        for key in occurrence_data.keys():
            unique_normalized_keys.add(key.strip().lower())

        # Iterar sobre as chaves normalizadas únicas para garantir que não haja duplicatas
        for normalized_key in sorted(list(unique_normalized_keys)): # Ordenar para exibição consistente
            if normalized_key in keys_to_ignore_normalized:
                continue

            # Determinar a melhor chave para exibição (preferindo a capitalização original)
            display_key = normalized_key # Padrão para a chave normalizada
            value_to_display = None

            # Tenta encontrar a chave preferida ou a original que corresponde à normalizada
            if normalized_key in display_key_preference:
                preferred_original_key = display_key_preference[normalized_key]
                if preferred_original_key in occurrence_data:
                    display_key = preferred_original_key
                    value_to_display = occurrence_data[preferred_original_key]

            # Se a chave preferida não foi encontrada ou não tinha valor, tenta a chave normalizada diretamente
            if value_to_display is None:
                if normalized_key in occurrence_data:
                    display_key = normalized_key # Usa a chave normalizada para exibição
                    value_to_display = occurrence_data[normalized_key]
                else:
                    # Fallback: tentar encontrar qualquer chave que normalize para esta
                    for original_key, val in occurrence_data.items():
                        if original_key.strip().lower() == normalized_key:
                            display_key = original_key
                            value_to_display = val
                            break

            if value_to_display is None or str(value_to_display).strip() == "":
                continue # Não exibe campos vazios ou sem valor

            # Formatação especial para alguns valores
            formatted_value = value_to_display
            if normalized_key == 'data de registro':
                try:
                    date_obj = datetime.strptime(str(value_to_display), "%Y-%m-%d %H:%M:%S")
                    formatted_value = date_obj.strftime("%d-%m-%Y %H:%M:%S")
                except ValueError:
                    pass
            elif normalized_key == 'status':
                formatted_value = str(value_to_display).upper()

            key_label = ctk.CTkLabel(scrollable_frame, text=f"{display_key}:", font=ctk.CTkFont(weight="bold"),
                                     text_color=self.controller.TEXT_COLOR)
            key_label.grid(row=row_counter, column=0, padx=10, pady=5, sticky="ne")

            value_label = ctk.CTkLabel(scrollable_frame, text=formatted_value, wraplength=400, justify="left",
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
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Erro ao carregar testes de ligação: {e}")
                # print(f"Dados brutos dos testes: {testes_data}") # DEBUG PRINT REMOVIDO
                # Opcional: messagebox.showerror("Erro de Dados", f"Falha ao carregar testes de ligação: {e}. Verifique a formatação na planilha.")
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

        # Nova seção para comentários
        self.comments_header_label = ctk.CTkLabel(scrollable_frame, text="Comentários:", font=ctk.CTkFont(size=14, weight="bold"),
                                                  text_color=self.controller.TEXT_COLOR)
        self.comments_header_label.grid(row=row_counter, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")
        row_counter += 1

        self.comments_container = ctk.CTkFrame(scrollable_frame, fg_color="gray20")
        self.comments_container.grid(row=row_counter, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        row_counter += 1

        # Área para adicionar novo comentário (visível apenas para admins/super_admins)
        user_profile = self.controller.get_current_user_profile()
        if user_profile.get("main_group") == "67_TELECOM" and (user_profile.get("sub_group") == "ADMIN" or user_profile.get("sub_group") == "SUPER_ADMIN"):
            self.new_comment_textbox = ctk.CTkTextbox(scrollable_frame, height=80,
                                                      fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                      border_color="gray40")
            self.new_comment_textbox.grid(row=row_counter, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")
            row_counter += 1

            self.add_comment_button = ctk.CTkButton(scrollable_frame, text="Adicionar Comentário",
                                                    command=self._add_comment,
                                                    fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                                    hover_color=self.controller.ACCENT_COLOR)
            self.add_comment_button.grid(row=row_counter, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
            row_counter += 1

        # Carregar e exibir comentários
        self._load_comments(occurrence_data.get('ID', 'N/A'))


        # --- Botão de Fechar ---
        close_button = ctk.CTkButton(self, text="Fechar", command=self.destroy,
                                     fg_color=self.controller.GRAY_BUTTON_COLOR,
                                     text_color=self.controller.TEXT_COLOR,
                                     hover_color=self.controller.GRAY_HOVER_COLOR)
        close_button.pack(pady=10)

    def _load_comments(self, occurrence_id):
        """Carrega e exibe os comentários para a ocorrência."""
        for widget in self.comments_container.winfo_children():
            widget.destroy()

        comments = self.controller.sheets_service.get_occurrence_comments(occurrence_id)
        if not comments:
            ctk.CTkLabel(self.comments_container, text="Nenhum comentário ainda.", text_color="gray60").pack(padx=10, pady=5)
            return

        for comment in comments:
            comment_frame = ctk.CTkFrame(self.comments_container, fg_color="gray15")
            comment_frame.pack(fill="x", padx=5, pady=3)

            comment_date = comment.get('Data_Comentario', 'N/A')
            if comment_date != 'N/A':
                try:
                    date_obj = datetime.strptime(comment_date, "%Y-%m-%d %H:%M:%S")
                    comment_date = date_obj.strftime("%d-%m-%Y %H:%M:%S")
                except ValueError:
                    pass # Mantenha o formato original se falhar

            header_text = f"Por: {comment.get('Nome_Autor', 'N/A')} em {comment_date}"
            ctk.CTkLabel(comment_frame, text=header_text, font=ctk.CTkFont(weight="bold"), text_color=self.controller.PRIMARY_COLOR).pack(anchor="w", padx=10, pady=(5,0))
            ctk.CTkLabel(comment_frame, text=comment.get('Comentario', ''), wraplength=450, justify="left", text_color=self.controller.TEXT_COLOR).pack(anchor="w", padx=10, pady=(0,5))


    def _add_comment(self):
        """Lógica para adicionar um novo comentário."""
        comment_text = self.new_comment_textbox.get("1.0", "end-1c").strip()
        if not comment_text:
            messagebox.showwarning("Campo Vazio", "Por favor, digite seu comentário antes de adicionar.")
            return

        occurrence_id = self.occurrence_data.get('ID', 'N/A')
        user_email = self.controller.user_email
        user_name = self.controller.user_profile.get("Nome Completo", user_email)

        if occurrence_id == 'N/A':
            messagebox.showerror("Erro", "Não foi possível identificar a ocorrência para adicionar o comentário.")
            return

        success, message = self.controller.sheets_service.add_occurrence_comment(occurrence_id, user_email, user_name, comment_text)
        if success:
            # Não use master para o NotificationPopup, use self (a janela Toplevel)
            # ou o master original que é a instância de App
            from .notification_popup import NotificationPopup # Importação local para evitar circular
            NotificationPopup(self.master, message=message, type="success",
                              bg_color_success="green", text_color_success="white",
                              bg_color_info="gray", text_color_info="white")
            self.new_comment_textbox.delete("1.0", "end")
            self._load_comments(occurrence_id) # Recarrega a lista de comentários
        else:
            messagebox.showerror("Erro", f"Não foi possível adicionar o comentário: {message}")
