# ==============================================================================
# FICHEiro: src/views/occurrence_detail_view.py
# DESCRIÇÃO: Contém a classe de interface para a janela (Toplevel) que exibe
#            os detalhes completos de uma ocorrência. (VERSÃO CORRIGIDA)
# ==============================================================================

import customtkinter as ctk
import json
import webbrowser
from datetime import datetime
from tkinter import messagebox
# CORREÇÃO: Importa 'super' e outros built-ins para satisfazer o Pylance
from builtins import super, set, sorted, list, str, ValueError, enumerate, TypeError

class OccurrenceDetailView(ctk.CTkToplevel):
    """
    Uma janela pop-up (Toplevel) para exibir os detalhes completos de uma ocorrência,
    incluindo todos os campos, testes de ligação e links para anexos.
    """
    def __init__(self, master, occurrence_data):
        super().__init__(master)
        self.master = master # Referência ao master (App)
        self.occurrence_data = occurrence_data # Armazena os dados da ocorrência
        self.editing_comment_id = None # Para rastrear o comentário que está sendo editado

        self.title(f"Detalhes da Ocorrência: {occurrence_data.get('ID', 'N/A')}")
        self.geometry("600x650")
        # Garante que a janela fique sempre à frente da janela principal
        self.transient(master)
        self.grab_set()

        # Acessar as cores do controller (App)
        self.controller = master

        # Definir a cor de fundo após a inicialização do super
        self.configure(fg_color=self.controller.BASE_COLOR)

        # Frame principal que será rolável
        scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Informações da Ocorrência",
                                                  fg_color=self.controller.BASE_COLOR,
                                                  label_text_color=self.controller.TEXT_COLOR)
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Exibição dos Dados Gerais ---
        details_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        details_frame.pack(fill="x", pady=(5, 15))

        keys_to_ignore_normalized = {'testes', 'anexos'}

        display_key_preference = {
            'descrição do problema': 'Descrição do problema',
            'operadora a': 'Operadora A',
            'operadora b': 'Operadora B',
            'título da ocorrência': 'Título da Ocorrência',
            'data de registro': 'Data de Registro',
            'status': 'Status',
            'id': 'ID',
            'nome do registrador': 'Nome do Registrador',
            'nome completo': 'Nome Completo',
            'username do registrador': 'Username do Registrador',
            'e-mail do registrador': 'E-mail do Registrador',
            'username': 'Username',
            'email': 'Email',
            'main_group': 'Grupo Principal',
            'sub_group': 'Subgrupo',
            'company': 'Empresa/Departamento',
            'tipo': 'Tipo',
            'modelo': 'Modelo',
            'ramal': 'Ramal',
            'localizacao': 'Localização',
            'origem': 'Origem',
            'destino': 'Destino',
            'registrador main group': 'Registrador Main Group',
            'registrador company': 'Registrador Company',
        }

        unique_normalized_keys = set()
        for key in occurrence_data.keys():
            unique_normalized_keys.add(key.strip().lower())

        for normalized_key in sorted(list(unique_normalized_keys)):
            if normalized_key in keys_to_ignore_normalized:
                continue

            display_key = normalized_key
            value_to_display = None

            if normalized_key in display_key_preference:
                preferred_original_key = display_key_preference[normalized_key]
                if preferred_original_key in occurrence_data:
                    display_key = preferred_original_key
                    value_to_display = occurrence_data[preferred_original_key]

            if value_to_display is None:
                if normalized_key in occurrence_data:
                    display_key = normalized_key
                    value_to_display = occurrence_data[normalized_key]
                else:
                    for original_key, val in occurrence_data.items():
                        if original_key.strip().lower() == normalized_key:
                            display_key = original_key
                            value_to_display = val
                            break

            if value_to_display is None or str(value_to_display).strip() == "":
                continue

            formatted_value = value_to_display
            if normalized_key == 'data de registro':
                try:
                    date_obj = datetime.strptime(str(value_to_display), "%Y-%m-%d %H:%M:%S")
                    formatted_value = date_obj.strftime("%d-%m-%Y %H:%M:%S")
                except ValueError:
                    pass
            elif normalized_key == 'status':
                formatted_value = str(value_to_display).upper()

            # CORREÇÃO DE LAYOUT: Usar um frame por linha com .pack() para alinhar
            row_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=2)

            key_label = ctk.CTkLabel(row_frame, text=f"{display_key}:", font=ctk.CTkFont(weight="bold"),
                                     width=200, anchor="e", text_color=self.controller.TEXT_COLOR)
            key_label.pack(side="left", padx=(0, 10))

            value_label = ctk.CTkLabel(row_frame, text=formatted_value, wraplength=300, justify="left",
                                       anchor="w", text_color="gray70")
            value_label.pack(side="left", fill="x", expand=True)


        # --- Exibição dos Testes de Ligação ---
        testes_data = occurrence_data.get('Testes') or occurrence_data.get('testes')
        if testes_data:
            try:
                testes = json.loads(testes_data)
                if testes:
                    tests_header_label = ctk.CTkLabel(scrollable_frame, text="Testes de Ligação:", font=ctk.CTkFont(size=14, weight="bold"),
                                                      text_color=self.controller.TEXT_COLOR)
                    tests_header_label.pack(fill="x", padx=10, pady=(15, 5), anchor="w")

                    tests_container = ctk.CTkFrame(scrollable_frame, fg_color="gray20")
                    tests_container.pack(fill="x", padx=10, pady=5)

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
            except (json.JSONDecodeError, TypeError):
                pass

        # --- Exibição dos Anexos ---
        anexos_data = occurrence_data.get('Anexos') or occurrence_data.get('anexos')
        if anexos_data:
            try:
                anexos = json.loads(anexos_data)
                if anexos:
                    anexos_header_label = ctk.CTkLabel(scrollable_frame, text="Anexos:", font=ctk.CTkFont(size=14, weight="bold"),
                                                      text_color=self.controller.TEXT_COLOR)
                    anexos_header_label.pack(fill="x", padx=10, pady=(15, 5), anchor="w")

                    anexos_container = ctk.CTkFrame(scrollable_frame, fg_color="gray20")
                    anexos_container.pack(fill="x", padx=10, pady=5)

                    for i, link in enumerate(anexos):
                        link_font = ctk.CTkFont(underline=True)
                        link_label = ctk.CTkLabel(
                            anexos_container,
                            text=f"Anexo {i+1}: Abrir no navegador",
                            text_color=(self.controller.PRIMARY_COLOR, self.controller.ACCENT_COLOR),
                            cursor="hand2",
                            font=link_font
                        )
                        link_label.pack(anchor="w", padx=10, pady=2)
                        link_label.bind("<Button-1>", lambda e, url=link: webbrowser.open_new(url))
            except (json.JSONDecodeError, TypeError):
                pass

        # --- Seção de Comentários ---
        self.comments_header_label = ctk.CTkLabel(scrollable_frame, text="Comentários:", font=ctk.CTkFont(size=14, weight="bold"),
                                                  text_color=self.controller.TEXT_COLOR)
        self.comments_header_label.pack(fill="x", padx=10, pady=(15, 5), anchor="w")

        self.comments_container = ctk.CTkFrame(scrollable_frame, fg_color="gray20")
        self.comments_container.pack(fill="x", padx=10, pady=5)

        self.new_comment_textbox = ctk.CTkTextbox(scrollable_frame, height=80,
                                                  fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                  border_color="gray40")
        self.new_comment_textbox.pack(fill="x", padx=10, pady=(10, 5))

        self.add_comment_button = ctk.CTkButton(scrollable_frame, text="Adicionar Comentário",
                                                command=self._add_or_update_comment,
                                                fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                                hover_color=self.controller.ACCENT_COLOR)
        self.add_comment_button.pack(fill="x", padx=10, pady=(0, 10))

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
            # Usar .grid() dentro do comment_frame é seguro, pois ele mesmo é posicionado com .pack()
            comment_frame.grid_columnconfigure(0, weight=1)

            comment_date = comment.get('Data_Comentario', 'N/A')
            if comment_date != 'N/A':
                try:
                    date_obj = datetime.strptime(comment_date, "%Y-%m-%d %H:%M:%S")
                    comment_date = date_obj.strftime("%d-%m-%Y %H:%M:%S")
                except ValueError:
                    pass

            header_text = f"Por: {comment.get('Nome_Autor', 'N/A')} em {comment_date}"
            ctk.CTkLabel(comment_frame, text=header_text, font=ctk.CTkFont(weight="bold"), text_color=self.controller.PRIMARY_COLOR).grid(row=0, column=0, sticky="w", padx=10, pady=(5,0))
            
            comment_text_label = ctk.CTkLabel(comment_frame, text=comment.get('Comentario', ''), wraplength=450, justify="left", text_color=self.controller.TEXT_COLOR)
            comment_text_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0,5))

            if comment.get('Email_Autor') == self.controller.user_email:
                button_frame = ctk.CTkFrame(comment_frame, fg_color="transparent")
                button_frame.grid(row=0, column=1, rowspan=2, sticky="e", padx=5, pady=5)

                edit_button = ctk.CTkButton(button_frame, text="✏️ Editar", width=70, height=25,
                                            command=lambda c=comment: self._edit_comment(c),
                                            fg_color="gray40", text_color="white", hover_color="gray50",
                                            font=ctk.CTkFont(size=11))
                edit_button.pack(pady=(0, 2))

                delete_button = ctk.CTkButton(button_frame, text="🗑️ Eliminar", width=70, height=25,
                                              command=lambda c_id=comment.get('id_comentario'): self._delete_comment(c_id),
                                              fg_color=self.controller.DANGER_COLOR, text_color="white", hover_color=self.controller.DANGER_HOVER_COLOR,
                                              font=ctk.CTkFont(size=11))
                delete_button.pack(pady=(2, 0))

    def _add_or_update_comment(self):
        """Lógica para adicionar um novo comentário ou atualizar um existente."""
        comment_text = self.new_comment_textbox.get("1.0", "end-1c").strip()
        if not comment_text:
            messagebox.showwarning("Campo Vazio", "Por favor, digite seu comentário antes de adicionar ou atualizar.")
            return

        occurrence_id = self.occurrence_data.get('ID', 'N/A')
        user_email = self.controller.user_email
        user_name = self.controller.user_profile.get("Nome Completo", user_email)

        if occurrence_id == 'N/A':
            messagebox.showerror("Erro", "Não foi possível identificar a ocorrência para adicionar/atualizar o comentário.")
            return

        if self.editing_comment_id:
            success, message = self.controller.sheets_service.update_occurrence_comment(self.editing_comment_id, comment_text)
            self.editing_comment_id = None
            self.add_comment_button.configure(text="Adicionar Comentário", fg_color=self.controller.PRIMARY_COLOR, hover_color=self.controller.ACCENT_COLOR)
        else:
            success, message = self.controller.sheets_service.add_occurrence_comment(occurrence_id, user_email, user_name, comment_text)
        
        if success:
            from .notification_popup import NotificationPopup
            NotificationPopup(self.master, message=message, type="success")
            self.new_comment_textbox.delete("1.0", "end")
            self._load_comments(occurrence_id)
        else:
            messagebox.showerror("Erro", f"Não foi possível completar a operação: {message}")

    def _edit_comment(self, comment_data):
        """Preenche a caixa de texto com o comentário para edição."""
        self.new_comment_textbox.delete("1.0", "end")
        self.new_comment_textbox.insert("1.0", comment_data.get('Comentario', ''))
        self.editing_comment_id = comment_data.get('id_comentario')
        self.add_comment_button.configure(text="Atualizar Comentário", fg_color="orange", hover_color="darkorange")

    def _delete_comment(self, comment_id):
        """Elimina um comentário após confirmação."""
        if messagebox.askyesno("Confirmar Eliminação", "Tem certeza que deseja eliminar este comentário? Esta ação não pode ser desfeita."):
            success, message = self.controller.sheets_service.delete_occurrence_comment(comment_id)
            if success:
                from .notification_popup import NotificationPopup
                NotificationPopup(self.master, message=message, type="success")
                self._load_comments(self.occurrence_data.get('ID', 'N/A'))
            else:
                messagebox.showerror("Erro", f"Não foi possível eliminar o comentário: {message}")
