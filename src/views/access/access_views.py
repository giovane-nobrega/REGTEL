# ==============================================================================
# FICHEIRO: src/views/access/access_views.py
# DESCRIÇÃO: Contém as classes de interface para o fluxo de solicitação
#            e aprovação de acesso de novos utilizadores.
# DATA DA ATUALIZAÇÃO: 27/08/2025
# NOTAS: Ficheiro movido para a nova subpasta 'access'. Nenhuma alteração
#        de código foi necessária.
# ==============================================================================

import customtkinter as ctk
from tkinter import messagebox
import re
import threading
import time

class RequestAccessView(ctk.CTkFrame):
    """
    Tela para novos utilizadores solicitarem acesso ao sistema REGTEL.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.configure(fg_color=self.controller.BASE_COLOR)

        self.partner_list = ["M2 TELECOMUNICAÇÕES", "MDA FIBRA", "DISK SISTEMA TELECOM", "GMN TELECOM", "67 INTERNET"]
        self.prefeitura_dept_list = ["SECRETARIA DE SAUDE", "SECRETARIA DE OBRAS", "DEPARTAMENTO DE TI", "GUARDA MUNICIPAL", "GABINETE DO PREFEITO", "OUTRO"]

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0, sticky="nsew")
        center_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6), weight=0)
        center_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(center_frame, text="Solicitação de Acesso",
                             font=ctk.CTkFont(size=24, weight="bold"),
                             text_color=self.controller.TEXT_COLOR)
        title.grid(row=0, column=0, pady=(0,10))

        subtitle = ctk.CTkLabel(center_frame, text="O seu e-mail não está registrado. Por favor, preencha seus dados para solicitar o acesso.",
                                wraplength=400, text_color="gray70")
        subtitle.grid(row=1, column=0, pady=(0, 20))

        personal_data_frame = ctk.CTkFrame(center_frame, fg_color="gray15", corner_radius=10)
        personal_data_frame.grid(row=2, column=0, pady=(10, 10), padx=20, sticky="ew")
        personal_data_frame.grid_columnconfigure(0, weight=1)
        personal_data_frame.grid_columnconfigure(1, weight=3)

        ctk.CTkLabel(personal_data_frame, text="Dados Pessoais", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")

        self.name_label = ctk.CTkLabel(personal_data_frame, text="Nome Completo:", text_color=self.controller.TEXT_COLOR)
        self.name_label.grid(row=1, column=0, sticky="w", padx=15, pady=(5,0))
        self.name_entry = ctk.CTkEntry(personal_data_frame, placeholder_text="Digite seu nome completo", width=300,
                                       fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                       border_color="gray40")
        self.name_entry.grid(row=1, column=1, sticky="ew", padx=15, pady=(5,0))
        self.name_validation_label = ctk.CTkLabel(personal_data_frame, text="", text_color="red", font=ctk.CTkFont(size=11))
        self.name_validation_label.grid(row=2, column=1, sticky="w", padx=15, pady=(0, 10))

        self.username_label = ctk.CTkLabel(personal_data_frame, text="Nome de Usuário:", text_color=self.controller.TEXT_COLOR)
        self.username_label.grid(row=3, column=0, sticky="w", padx=15, pady=(5,0))
        self.username_entry = ctk.CTkEntry(personal_data_frame, placeholder_text="Ex: jsilva (4-16 caracteres, sem espaços)", width=300,
                                           fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                           border_color="gray40")
        self.username_entry.grid(row=3, column=1, sticky="ew", padx=15, pady=(5,0))
        self.username_validation_label = ctk.CTkLabel(personal_data_frame, text="", text_color="red", font=ctk.CTkFont(size=11))
        self.username_validation_label.grid(row=4, column=1, sticky="w", padx=15, pady=(0, 10))

        affiliation_data_frame = ctk.CTkFrame(center_frame, fg_color="gray15", corner_radius=10)
        affiliation_data_frame.grid(row=3, column=0, pady=(10, 10), padx=20, sticky="ew")
        affiliation_data_frame.grid_columnconfigure(0, weight=1)
        affiliation_data_frame.grid_columnconfigure(1, weight=3)

        ctk.CTkLabel(affiliation_data_frame, text="Dados de Vínculo", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10), sticky="w")

        self.role_label = ctk.CTkLabel(affiliation_data_frame, text="Vínculo Principal:", text_color=self.controller.TEXT_COLOR)
        self.role_label.grid(row=1, column=0, sticky="w", padx=15, pady=(5,0))
        self.role_combobox = ctk.CTkComboBox(affiliation_data_frame, values=["Prefeitura", "Parceiro", "Colaboradores 67"], width=300, command=self._on_role_selected,
                                             fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                             border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                             button_hover_color=self.controller.ACCENT_COLOR)
        self.role_combobox.grid(row=1, column=1, sticky="ew", padx=15, pady=(5,10))

        self.company_label = ctk.CTkLabel(affiliation_data_frame, text="Departamento/Empresa:", text_color=self.controller.TEXT_COLOR)
        self.company_label.grid(row=2, column=0, sticky="w", padx=15, pady=(5,0))
        self.company_combobox = ctk.CTkComboBox(affiliation_data_frame, values=[], width=300,
                                                     fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                     border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                     button_hover_color=self.controller.ACCENT_COLOR)
        self.company_combobox.grid(row=2, column=1, sticky="ew", padx=15, pady=(5,0))
        self.company_validation_label = ctk.CTkLabel(affiliation_data_frame, text="", text_color="red", font=ctk.CTkFont(size=11))
        self.company_validation_label.grid(row=3, column=1, sticky="w", padx=15, pady=(0, 10))

        self.subgroup_67_label = ctk.CTkLabel(affiliation_data_frame, text="Selecione o Subgrupo:", text_color=self.controller.TEXT_COLOR)
        self.subgroup_67_combobox = ctk.CTkComboBox(affiliation_data_frame, values=["67_TELECOM_USER", "67_INTERNET_USER"],
                                                    fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                    border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                                    button_hover_color=self.controller.ACCENT_COLOR)


        self.submit_button = ctk.CTkButton(center_frame, text="Enviar Solicitação", command=self.submit, height=40,
                                           fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                           hover_color=self.controller.ACCENT_COLOR)
        self.submit_button.grid(row=4, column=0, pady=20, padx=20, sticky="ew")

        self.logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, height=40,
                                           fg_color=self.controller.GRAY_BUTTON_COLOR, hover_color=self.controller.GRAY_HOVER_COLOR)
        self.logout_button.grid(row=5, column=0, pady=10, padx=20, sticky="ew")

        self.default_border_color = self.name_entry.cget("border_color")

        self.name_entry.bind("<KeyRelease>", self._validate_name_live)
        self.name_entry.bind("<FocusOut>", self._validate_name_live)
        self.name_entry.bind("<FocusIn>", lambda e: self._on_focus_in(self.name_label))
        self.name_entry.bind("<FocusOut>", lambda e: self._on_focus_out(self.name_label))

        self.username_entry.bind("<KeyRelease>", self._validate_username_live)
        self.username_entry.bind("<FocusOut>", self._validate_username_live)
        self.username_entry.bind("<FocusIn>", lambda e: self._on_focus_in(self.username_label))
        self.username_entry.bind("<FocusOut>", lambda e: self._on_focus_out(self.username_label))

        self.company_combobox.bind("<<ComboboxSelected>>", self._validate_company_live)
        self.role_combobox.bind("<<ComboboxSelected>>", self._validate_company_live)
        self.company_combobox.bind("<FocusIn>", lambda e: self._on_focus_in(self.company_label))
        self.company_combobox.bind("<FocusOut>", lambda e: self._on_focus_out(self.company_label))
        self.role_combobox.bind("<FocusIn>", lambda e: self._on_focus_in(self.role_label))
        self.role_combobox.bind("<FocusOut>", lambda e: self._on_focus_out(self.role_label))

        self.subgroup_67_combobox.bind("<<ComboboxSelected>>", self._validate_company_live)
        self.subgroup_67_combobox.bind("<FocusIn>", lambda e: self._on_focus_in(self.subgroup_67_label))
        self.subgroup_67_combobox.bind("<FocusOut>", lambda e: self._on_focus_out(self.subgroup_67_label))

        self.role_combobox.set("Prefeitura")
        self._on_role_selected("Prefeitura")
        self._reset_validation_feedback()


    def _on_focus_in(self, label_widget):
        label_widget.configure(font=ctk.CTkFont(weight="bold", size=14))

    def _on_focus_out(self, label_widget):
        label_widget.configure(font=ctk.CTkFont(weight="normal", size=13))

    def _reset_validation_feedback(self):
        self.name_entry.configure(border_color=self.default_border_color)
        self.name_validation_label.configure(text="")
        self.username_entry.configure(border_color=self.default_border_color)
        self.username_validation_label.configure(text="")
        self.company_combobox.configure(border_color=self.default_border_color)
        self.company_validation_label.configure(text="")
        if hasattr(self, 'subgroup_67_combobox'):
            self.subgroup_67_combobox.configure(border_color=self.default_border_color)

    def _validate_name_live(self, event=None):
        name = self.name_entry.get().strip()
        is_valid = bool(name)
        if is_valid:
            self.name_entry.configure(border_color=self.default_border_color)
            self.name_validation_label.configure(text="✔️ Nome válido", text_color="green")
        else:
            self.name_entry.configure(border_color="red")
            self.name_validation_label.configure(text="❌ O nome completo é obrigatório.", text_color="red")
        return is_valid

    def _validate_username_live(self, event=None):
        username = self.username_entry.get()
        is_valid = True
        message = ""
        if not username.strip():
            is_valid = False
            message = "O nome de utilizador é obrigatório."
        elif not (4 <= len(username) <= 16):
            is_valid = False
            message = "Deve ter entre 4 e 16 caracteres."
        elif not re.fullmatch(r"^[a-zA-Z0-9_.]*$", username):
            is_valid = False
            message = "Não pode conter espaços ou caracteres especiais (exceto _ e .)."

        if is_valid:
            self.username_entry.configure(border_color=self.default_border_color)
            self.username_validation_label.configure(text="✔️ Nome de utilizador válido", text_color="green")
        else:
            self.username_entry.configure(border_color="red")
            self.username_validation_label.configure(text=f"❌ Nome de utilizador inválido: {message}", text_color="red")
        return is_valid

    def _validate_company_live(self, event=None):
        selected_role = self.role_combobox.get()
        role_map = {"Prefeitura": "PREFEITURA", "Parceiro": "PARTNER", "Colaboradores 67": "67_TELECOM"}
        main_group = role_map.get(selected_role)

        if main_group in ["PARTNER", "PREFEITURA"]:
            company_name = self.company_combobox.get().strip()
            is_valid = bool(company_name)
            if is_valid:
                self.company_combobox.configure(border_color=self.default_border_color)
                self.company_validation_label.configure(text="✔️ Seleção válida", text_color="green")
            else:
                self.company_combobox.configure(border_color="red")
                self.company_validation_label.configure(text="❌ A seleção do departamento/empresa é obrigatória.", text_color="red")
            return is_valid
        elif main_group == "67_TELECOM":
            sub_group_selected = self.subgroup_67_combobox.get().strip()
            is_valid = bool(sub_group_selected)
            if is_valid:
                self.subgroup_67_combobox.configure(border_color=self.default_border_color)
                self.company_validation_label.configure(text="✔️ Subgrupo válido", text_color="green")
            else:
                self.subgroup_67_combobox.configure(border_color="red")
                self.company_validation_label.configure(text="❌ A seleção do subgrupo é obrigatória.", text_color="red")
            return is_valid

        self.company_combobox.configure(border_color=self.default_border_color)
        self.company_validation_label.configure(text="")
        if hasattr(self, 'subgroup_67_combobox'):
            self.subgroup_67_combobox.configure(border_color=self.default_border_color)
        return True

    def _on_role_selected(self, selected_role):
        if selected_role == "Parceiro":
            self.company_label.grid(row=2, column=0, sticky="w", padx=15, pady=(5,0))
            self.company_combobox.grid(row=2, column=1, sticky="ew", padx=15, pady=(5,0))
            self.company_validation_label.grid(row=3, column=1, sticky="w", padx=15, pady=(0, 10))
            self.company_label.configure(text="Selecione a Empresa Parceira:")
            self.company_combobox.configure(values=[c for c in self.partner_list if c != "67 INTERNET"])
            self.company_combobox.set(self.company_combobox._values[0] if self.company_combobox._values else "")
            self.subgroup_67_label.grid_forget()
            self.subgroup_67_combobox.grid_forget()
        elif selected_role == "Prefeitura":
            self.company_label.grid(row=2, column=0, sticky="w", padx=15, pady=(5,0))
            self.company_combobox.grid(row=2, column=1, sticky="ew", padx=15, pady=(5,0))
            self.company_validation_label.grid(row=3, column=1, sticky="w", padx=15, pady=(0, 10))
            self.company_label.configure(text="Selecione o Departamento:")
            self.company_combobox.configure(values=self.prefeitura_dept_list)
            self.company_combobox.set(self.prefeitura_dept_list[0] if self.prefeitura_dept_list else "")
            self.subgroup_67_label.grid_forget()
            self.subgroup_67_combobox.grid_forget()
        elif selected_role == "Colaboradores 67":
            self.company_label.grid_forget()
            self.company_combobox.grid_forget()
            self.company_validation_label.grid_forget()
            self.subgroup_67_label.grid(row=2, column=0, sticky="w", padx=15, pady=(5,0))
            self.subgroup_67_combobox.grid(row=2, column=1, sticky="ew", padx=15, pady=(5,10))
            self.subgroup_67_combobox.set("67_TELECOM_USER")
        else:
            self.company_label.grid_forget()
            self.company_combobox.grid_forget()
            self.company_validation_label.grid_forget()
            self.subgroup_67_label.grid_forget()
            self.subgroup_67_combobox.grid_forget()
        self._validate_company_live()

    def on_show(self):
        self.name_entry.delete(0, "end")
        self.username_entry.delete(0, "end")
        self.role_combobox.set("Prefeitura")
        self._on_role_selected("Prefeitura")
        self._reset_validation_feedback()
        self.name_entry.focus_set()

    def submit(self):
        full_name = self.name_entry.get().upper()
        username = self.username_entry.get()
        role_map = {"Prefeitura": "PREFEITURA", "Parceiro": "PARTNER", "Colaboradores 67": "67_TELECOM"}
        main_group = role_map.get(self.role_combobox.get())
        company_name = None
        sub_group = None

        if main_group == "PARTNER":
            partner_subgroup_map = {
                "MDA FIBRA": "MDA_USER", "M2 TELECOMUNICAÇÕES": "M2_USER",
                "DISK SISTEMA TELECOM": "DISK_USER", "GMN TELECOM": "GMN_USER"
            }
            company_name = self.company_combobox.get()
            sub_group = partner_subgroup_map.get(company_name, "USER")
        elif main_group == "PREFEITURA":
            sub_group = "PREFEITURA_USER"
            company_name = self.company_combobox.get()
        elif main_group == "67_TELECOM":
            sub_group = self.subgroup_67_combobox.get()
            company_name = "TRR"

        all_valid = True
        if not self._validate_name_live(): all_valid = False
        if not self._validate_username_live(): all_valid = False
        if main_group in ["PARTNER", "PREFEITURA", "67_TELECOM"] and not self._validate_company_live(): all_valid = False

        if not all_valid:
            messagebox.showwarning("Campos Inválidos", "Por favor, corrija os campos destacados em vermelho antes de enviar a solicitação.")
            return

        self.controller.submit_access_request(full_name, username, main_group, sub_group, company_name)


class PendingApprovalView(ctk.CTkFrame):
    """
    Tela exibida enquanto o acesso do utilizador está pendente de aprovação.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(fg_color=self.controller.BASE_COLOR)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.grid(row=0, column=0, sticky="nsew")
        center_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=0)
        center_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(center_frame, text="Acesso Pendente",
                             font=ctk.CTkFont(size=24, weight="bold"),
                             text_color=self.controller.TEXT_COLOR)
        title.grid(row=0, column=0, pady=(0, 10))

        subtitle = ctk.CTkLabel(center_frame, text="Sua solicitação de acesso está aguardando aprovação de um administrador. O status será verificado a cada 30 segundos.",
                                wraplength=450, text_color="gray70")
        subtitle.grid(row=1, column=0, pady=(0, 20))

        self.status_label = ctk.CTkLabel(center_frame, text="A verificar o status...",
                                         font=ctk.CTkFont(size=14, slant="italic"),
                                         text_color=self.controller.ACCENT_COLOR)
        self.status_label.grid(row=2, column=0, pady=(0, 10))

        check_button = ctk.CTkButton(center_frame, text="Verificar Agora", command=self.check_status_now,
                                      fg_color=self.controller.PRIMARY_COLOR, hover_color=self.controller.ACCENT_COLOR)
        check_button.grid(row=3, column=0, pady=(0, 10))

        logout_button = ctk.CTkButton(center_frame, text="Sair", command=self.controller.perform_logout, height=40,
                                      fg_color=self.controller.GRAY_BUTTON_COLOR, hover_color=self.controller.GRAY_HOVER_COLOR)
        logout_button.grid(row=4, column=0, pady=10)

        self.is_running = False
        self.checker_thread = None

    def on_show(self):
        if not self.is_running or (self.checker_thread and not self.checker_thread.is_alive()):
            self.is_running = True
            self.checker_thread = threading.Thread(target=self._check_status_thread, daemon=True)
            self.checker_thread.start()

    def _check_status_thread(self):
        while self.is_running:
            self.controller.after(0, lambda: self.status_label.configure(text="A verificar o status..."))
            user_profile = self.controller.sheets_service.check_user_status(self.controller.user_email)
            status = user_profile.get("status")

            if status == "approved":
                self.is_running = False
                self.controller.user_profile = user_profile
                self.controller.after(0, self.controller.navigate_based_on_status)
            elif status == "rejected":
                self.is_running = False
                self.controller.after(0, lambda: messagebox.showerror("Acesso Negado", "Sua solicitação de acesso foi rejeitada. Por favor, entre em contacto com o administrador."))
                self.controller.after(0, self.controller.perform_logout)
            else:
                self.controller.after(0, lambda: self.status_label.configure(text=f"Aguardando aprovação. Próxima verificação em 30 segundos..."))

            for _ in range(30):
                if not self.is_running:
                    break
                time.sleep(1)

    def check_status_now(self):
        if self.is_running:
            self.is_running = False
            if self.checker_thread and self.checker_thread.is_alive():
                self.checker_thread.join(timeout=1)

            self.is_running = True
            self.status_label.configure(text="A verificar o status agora...")
            self.checker_thread = threading.Thread(target=self._check_status_thread, daemon=True)
            self.checker_thread.start()
