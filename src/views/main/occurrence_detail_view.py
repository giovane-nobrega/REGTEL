# ==============================================================================
# ARQUIVO: src/views/occurrence_detail_view.py
# DESCRIÇÃO: (VERSÃO CORRIGIDA PÓS-REFATORAÇÃO) Contém a classe de interface
#            para a janela que exibe os detalhes de uma ocorrência.
# ==============================================================================

import customtkinter as ctk
import json
import webbrowser
from datetime import datetime
from tkinter import messagebox
from builtins import super, set, sorted, list, str, ValueError, enumerate, TypeError

class OccurrenceDetailView(ctk.CTkToplevel):
    """
    Uma janela pop-up (Toplevel) para exibir os detalhes completos de uma ocorrência,
    incluindo todos os campos, testes de ligação e links para anexos.
    """
    def __init__(self, master, occurrence_data):
        super().__init__(master)
        self.master = master
        self.occurrence_data = occurrence_data
        self.editing_comment_id = None

        self.title(f"Detalhes da Ocorrência: {occurrence_data.get('ID', 'N/A')}")
        self.geometry("600x650")
        self.transient(master)
        self.grab_set()

        self.controller = master

        # Definir cores padrão caso o controller não tenha os atributos de cor
        self.BASE_COLOR = getattr(master, 'BASE_COLOR', '#0A0E1A')
        self.TEXT_COLOR = getattr(master, 'TEXT_COLOR', '#FFFFFF')
        self.PRIMARY_COLOR = getattr(master, 'PRIMARY_COLOR', '#1C274C')
        self.ACCENT_COLOR = getattr(master, 'ACCENT_COLOR', '#3A7EBF')
        self.GRAY_BUTTON_COLOR = getattr(master, 'GRAY_BUTTON_COLOR', '#333333')
        self.GRAY_HOVER_COLOR = getattr(master, 'GRAY_HOVER_COLOR', '#444444')
        self.DANGER_COLOR = getattr(master, 'DANGER_COLOR', '#BF3A3A')
        self.DANGER_HOVER_COLOR = getattr(master, 'DANGER_HOVER_COLOR', '#A93232')

        self.configure(fg_color=self.BASE_COLOR)

        scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Informações da Ocorrência",
                                                  fg_color=self.BASE_COLOR,
                                                  label_text_color=self.TEXT_COLOR)
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

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
            'registradormaingroup': 'Grupo Principal do Registrador',
            'registradorcompany': 'Empresa do Registrador',
        }

        displayed_keys = set()

        for original_key, value in occurrence_data.items():
            normalized_key = original_key.strip().lower().replace(' ', '')

            if normalized_key in displayed_keys:
                continue

            if normalized_key in keys_to_ignore_normalized:
                continue
            
            display_name = original_key
            value_to_display = value

            if normalized_key in display_key_preference:
                display_name = display_key_preference[normalized_key]
            
            if value_to_display is None or str(value_to_display).strip() == "":
                continue

            formatted_value = value_to_display
            if normalized_key == 'datadecadastro':
                try:
                    date_obj = datetime.strptime(str(value_to_display), "%Y-%m-%d %H:%M:%S")
                    formatted_value = date_obj.strftime("%d-%m-%Y %H:%M:%S")
                except ValueError:
                    pass
            elif normalized_key == 'status':
                formatted_value = str(value_to_display).upper()

            displayed_keys.add(normalized_key)

            row_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=2)

            key_label = ctk.CTkLabel(row_frame, text=f"{display_name}:", font=ctk.CTkFont(weight="bold"),
                                     width=200, anchor="e", text_color=self.TEXT_COLOR)
            key_label.pack(side="left", padx=(0, 10))

            value_label = ctk.CTkLabel(row_frame, text=formatted_value, wraplength=300, justify="left",
                                       anchor="w", text_color="gray70")
            value_label.pack(side="left", fill="x", expand=True)


        testes_data = occurrence_data.get('testes') or occurrence_data.get('Testes')
        if testes_data:
            try:
                testes = json.loads(testes_data)
                if testes:
                    tests_header_label = ctk.CTkLabel(scrollable_frame, text="Testes de Ligação:", font=ctk.CTkFont(size=14, weight="bold"),
                                                      text_color=self.TEXT_COLOR)
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
                                                 text_color=self.TEXT_COLOR)
                        test_card.pack(fill="x", padx=10, pady=5)
            except (json.JSONDecodeError, TypeError):
                pass

        anexos_data = occurrence_data.get('anexos') or occurrence_data.get('Anexos')
        if anexos_data:
            try:
                anexos = json.loads(anexos_data)
                if anexos:
                    anexos_header_label = ctk.CTkLabel(scrollable_frame, text="Anexos:", font=ctk.CTkFont(size=14, weight="bold"),
                                                      text_color=self.TEXT_COLOR)
                    anexos_header_label.pack(fill="x", padx=10, pady=(15, 5), anchor="w")

                    anexos_container = ctk.CTkFrame(scrollable_frame, fg_color="gray20")
                    anexos_container.pack(fill="x", padx=10, pady=5)

                    for i, link in enumerate(anexos):
                        link_font = ctk.CTkFont(underline=True)
                        link_label = ctk.CTkLabel(
                            anexos_container,
                            text=f"Anexo {i+1}: Abrir no navegador",
                            text_color=(self.PRIMARY_COLOR, self.ACCENT_COLOR),
                            cursor="hand2",
                            font=link_font
                        )
                        link_label.pack(anchor="w", padx=10, pady=2)
                        link_label.bind("<Button-1>", lambda e, url=link: webbrowser.open_new(url))
            except (json.JSONDecodeError, TypeError):
                pass

        self.comments_header_label = ctk.CTkLabel(scrollable_frame, text="Comentários:", font=ctk.CTkFont(size=14, weight="bold"),
                                                  text_color=self.TEXT_COLOR)
        self.comments_header_label.pack(fill="x", padx=10, pady=(15, 5), anchor="w")

        self.comments_container = ctk.CTkFrame(scrollable_frame, fg_color="gray20")
        self.comments_container.pack(fill="x", padx=10, pady=5)

        self.new_comment_textbox = ctk.CTkTextbox(scrollable_frame, height=80,
                                                  fg_color="gray20", text_color=self.TEXT_COLOR,
                                                  border_color="gray40")
        self.new_comment_textbox.pack(fill="x", padx=10, pady=(10, 5))

        self.add_comment_button = ctk.CTkButton(scrollable_frame, text="Adicionar Comentário",
                                                command=self._add_or_update_comment,
                                                fg_color=self.PRIMARY_COLOR, text_color=self.TEXT_COLOR,
                                                hover_color=self.ACCENT_COLOR)
        self.add_comment_button.pack(fill="x", padx=10, pady=(0, 10))

        self._load_comments(occurrence_data.get('ID', 'N/A'))

        close_button = ctk.CTkButton(self, text="Fechar", command=self.destroy,
                                     fg_color=self.GRAY_BUTTON_COLOR,
                                     text_color=self.TEXT_COLOR,
                                     hover_color=self.GRAY_HOVER_COLOR)
        close_button.pack(pady=10)

    def _load_comments(self, occurrence_id):
        """Carrega e exibe os comentários para a ocorrência."""
        for widget in self.comments_container.winfo_children():
            widget.destroy()

        # Tenta obter comentários do controller, se disponível
        comments = []
        if hasattr(self.controller, 'occurrence_service'):
            comments = self.controller.occurrence_service.get_comments(occurrence_id)
        
        if not comments:
            ctk.CTkLabel(self.comments_container, text="Nenhum comentário ainda.", text_color="gray60").pack(padx=10, pady=5)
            return

        for comment in comments:
            comment_frame = ctk.CTkFrame(self.comments_container, fg_color="gray15")
            comment_frame.pack(fill="x", padx=5, pady=3)
            comment_frame.grid_columnconfigure(0, weight=1)

            comment_date = comment.get('Data_Comentario', 'N/A')
            if comment_date != 'N/A':
                try:
                    date_obj = datetime.strptime(comment_date, "%Y-%m-%d %H:%M:%S")
                    comment_date = date_obj.strftime("%d-%m-%Y %H:%M:%S")
                except ValueError:
                    pass

            header_text = f"Por: {comment.get('Nome_Autor', 'N/A')} em {comment_date}"
            ctk.CTkLabel(comment_frame, text=header_text, font=ctk.CTkFont(weight="bold"), text_color=self.PRIMARY_COLOR).grid(row=0, column=0, sticky="w", padx=10, pady=(5,0))
            
            comment_text_label = ctk.CTkLabel(comment_frame, text=comment.get('Comentario', ''), wraplength=450, justify="left", text_color=self.TEXT_COLOR)
            comment_text_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0,5))

            if comment.get('Email_Autor') == self.controller.user_email:
                button_frame = ctk.CTkFrame(comment_frame, fg_color="transparent")
                button_frame.grid(row=0, column=1, rowspan=2, sticky="e", padx=5, pady=5)

                edit_button = ctk.CTkButton(button_frame, text="✏️ Editar", width=70, height=25,
                                            command=lambda c=comment: self._edit_comment(c),
                                            fg_color="gray40", text_color="white", hover_color="gray50",
                                            font=ctk.CTkFont(size=11))
                edit_button.pack(pady=(0, 2))

                delete_button = ctk.CTkButton(button_frame, text="🗑️ Excluir", width=70, height=25,
                                              command=lambda c_id=comment.get('id_comentario'): self._delete_comment(c_id),
                                              fg_color=self.DANGER_COLOR, text_color="white", hover_color=self.DANGER_HOVER_COLOR,
                                              font=ctk.CTkFont(size=11))
                delete_button.pack(pady=(2, 0))

    def _add_or_update_comment(self):
        """Adiciona um novo comentário ou atualiza um existente."""
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

        if not hasattr(self.controller, 'occurrence_service'):
            messagebox.showerror("Erro", "Serviço de ocorrências não disponível.")
            return
            
        if self.editing_comment_id:
            # CORREÇÃO: Chama o método do serviço de ocorrências
            success, message = self.controller.occurrence_service.update_comment(self.editing_comment_id, comment_text)
            self.editing_comment_id = None
            self.add_comment_button.configure(text="Adicionar Comentário", fg_color=self.PRIMARY_COLOR, hover_color=self.ACCENT_COLOR)
        else:
            # CORREÇÃO: Chama o método do serviço de ocorrências
            success, message = self.controller.occurrence_service.add_comment(occurrence_id, user_email, user_name, comment_text)
        
        if success:
            from views.components.notification_popup import NotificationPopup
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
        self.new_comment_textbox.focus_set()


    def _delete_comment(self, comment_id):
        """Exclui um comentário após confirmação."""
        if not hasattr(self.controller, 'occurrence_service'):
            messagebox.showerror("Erro", "Serviço de ocorrências não disponível.")
            return
            
        if messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir este comentário? Esta ação não pode ser desfeita."):
            # CORREÇÃO: Chama o método do serviço de ocorrências
            success, message = self.controller.occurrence_service.delete_comment(comment_id)
            if success:
                from views.components.notification_popup import NotificationPopup
                NotificationPopup(self.master, message=message, type="success")
                self._load_comments(self.occurrence_data.get('ID', 'N/A'))
            else:
                messagebox.showerror("Erro", f"Não foi possível excluir o comentário: {message}")