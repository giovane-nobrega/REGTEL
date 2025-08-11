# ==============================================================================
# FICHEIRO: src/views/equipment_view.py
# DESCRIÇÃO: Contém a classe de interface para o formulário de registo
#            de ocorrências de suporte técnico de equipamento.
#            (VERSÃO COM VALIDAÇÃO PROATIVA E CORES)
# ==============================================================================
import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import re

class EquipmentView(ctk.CTkFrame):
    """
    Tela para utilizadores da Prefeitura registarem problemas relacionados
    com equipamentos físicos, com validação proativa.
    """
    def __init__(self, parent, controller):
        super().__init__(parent) # Removido fg_color do super().__init__
        self.controller = controller

        # Definir a cor de fundo após a inicialização do super
        self.configure(fg_color=self.controller.BASE_COLOR)

        self.attachment_paths = []

        # --- Configuração da Responsividade ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 

        ctk.CTkLabel(self, text="Registar Suporte Técnico de Equipamento",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=self.controller.TEXT_COLOR).grid(row=0, column=0, padx=20, pady=(10, 20), sticky="ew")

        # --- Frame Principal do Formulário ---
        form_frame = ctk.CTkFrame(self, fg_color="gray15") # Fundo do formulário
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_rowconfigure(4, weight=1) # Permite que a caixa de descrição expanda

        # --- Campos do Formulário ---
        ctk.CTkLabel(form_frame, text="Tipo de Equipamento:", text_color=self.controller.TEXT_COLOR).grid(
            row=0, column=0, padx=10, pady=10, sticky="w")
        self.equip_type = ctk.CTkComboBox(form_frame, values=[
                                          "Telefone IP", "ATA", "Softphone", "Fonte de Alimentação", "Outro"],
                                          fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                          border_color="gray40", button_color=self.controller.PRIMARY_COLOR,
                                          button_hover_color=self.controller.ACCENT_COLOR)
        self.equip_type.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Marca/Modelo:", text_color=self.controller.TEXT_COLOR).grid(row=1,
                                                            column=0, padx=10, pady=10, sticky="w")
        self.equip_model = ctk.CTkEntry(
            form_frame, placeholder_text="Ex: Grandstream GXP1610",
            fg_color="gray20", text_color=self.controller.TEXT_COLOR,
            border_color="gray40")
        self.equip_model.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Ramal:", text_color=self.controller.TEXT_COLOR).grid(
            row=2, column=0, padx=10, pady=10, sticky="w")
        self.equip_ramal = ctk.CTkEntry(
            form_frame, placeholder_text="Apenas números, ex: 2001",
            fg_color="gray20", text_color=self.controller.TEXT_COLOR,
            border_color="gray40")
        self.equip_ramal.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Localização:", text_color=self.controller.TEXT_COLOR).grid(
            row=3, column=0, padx=10, pady=10, sticky="w")
        self.equip_location = ctk.CTkEntry(
            form_frame, placeholder_text="Ex: Prédio A, Sala 101, Mesa 5",
            fg_color="gray20", text_color=self.controller.TEXT_COLOR,
            border_color="gray40")
        self.equip_location.grid(
            row=3, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Descrição do Problema:", text_color=self.controller.TEXT_COLOR).grid(
            row=4, column=0, padx=10, pady=10, sticky="nw")
        self.equip_description = ctk.CTkTextbox(form_frame, height=120,
                                                fg_color="gray20", text_color=self.controller.TEXT_COLOR,
                                                border_color="gray40")
        self.equip_description.grid(
            row=4, column=1, padx=10, pady=10, sticky="nsew")

        # --- Secção de Anexos ---
        attachment_frame = ctk.CTkFrame(self, fg_color="gray15") # Fundo da seção de anexos
        attachment_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        ctk.CTkLabel(attachment_frame, text="Anexar Imagens (Opcional):",
                     font=ctk.CTkFont(weight="bold"),
                     text_color=self.controller.TEXT_COLOR).pack(side="left", padx=(10,5), pady=10)
        
        attach_button = ctk.CTkButton(attachment_frame, text="Selecionar Ficheiros...", command=self._select_files,
                                      fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
                                      hover_color=self.controller.ACCENT_COLOR)
        attach_button.pack(side="left", padx=5, pady=10)

        self.attachment_label = ctk.CTkLabel(attachment_frame, text="Nenhum ficheiro selecionado.", text_color="gray60")
        self.attachment_label.pack(side="left", padx=5, pady=10)

        # --- Botões de Ação ---
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, padx=20, pady=(10, 10), sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.back_button = ctk.CTkButton(button_frame, text="Voltar ao Menu", command=lambda: self.controller.show_frame(
            "MainMenuView"), fg_color=self.controller.GRAY_BUTTON_COLOR,
            text_color=self.controller.TEXT_COLOR, hover_color=self.controller.GRAY_HOVER_COLOR)
        self.back_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.submit_button = ctk.CTkButton(
            button_frame, text="Registar Problema", command=self.submit, height=40,
            fg_color=self.controller.PRIMARY_COLOR, text_color=self.controller.TEXT_COLOR,
            hover_color=self.controller.ACCENT_COLOR)
        self.submit_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # --- Configuração da Lógica de Validação ---
        self.default_border_color = self.equip_model.cget("border_color")
        self.equip_ramal.bind("<FocusOut>", lambda event: self._validate_numeric_field(self.equip_ramal))
        self.equip_model.bind("<FocusOut>", lambda event: self._validate_required_field(self.equip_model))
        self.equip_location.bind("<FocusOut>", lambda event: self._validate_required_field(self.equip_location))
        self.equip_description.bind("<KeyRelease>", lambda event: self._validate_required_field(self.equip_description))
        self.equip_type.configure(command=lambda choice: self._validate_required_combobox(self.equip_type))


    def _validate_numeric_field(self, widget):
        """Verifica se o conteúdo de um widget contém apenas números."""
        content = widget.get()
        if content and not content.isdigit():
            widget.configure(border_color="red")
            return False
        else:
            widget.configure(border_color=self.default_border_color)
            return True

    def _validate_required_field(self, widget):
        """Valida se um campo de texto (ou Textbox) não está vazio."""
        content = ""
        if isinstance(widget, ctk.CTkTextbox):
            content = widget.get("1.0", "end-1c")
        else:
            content = widget.get()

        if not content.strip():
            widget.configure(border_color="red")
            return False
        else:
            widget.configure(border_color=self.default_border_color)
            return True
            
    def _validate_required_combobox(self, widget):
        """Valida se uma ComboBox tem um valor selecionado."""
        if not widget.get():
            widget.configure(border_color="red")
            return False
        else:
            widget.configure(border_color=self.default_border_color)
            return True

    def _select_files(self):
        """Abre uma janela para o utilizador selecionar ficheiros de imagem."""
        filepaths = filedialog.askopenfilenames(
            title="Selecione as imagens",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg")]
        )
        if filepaths:
            self.attachment_paths = list(filepaths)
            self.attachment_label.configure(text=f"{len(filepaths)} ficheiro(s) selecionado(s).")
        else:
            self.attachment_paths = []
            self.attachment_label.configure(text="Nenhum ficheiro selecionado.")

    def on_show(self):
        """Limpa o formulário e restaura o estado visual sempre que a tela é exibida."""
        self.equip_type.set("")
        self.equip_model.delete(0, "end")
        self.equip_ramal.delete(0, "end")
        self.equip_location.delete(0, "end")
        self.equip_description.delete("1.0", "end")
        
        self.attachment_paths = []
        self.attachment_label.configure(text="Nenhum ficheiro selecionado.")
        
        # Restaura as cores das bordas
        self.equip_type.configure(border_color=self.default_border_color)
        self.equip_model.configure(border_color=self.default_border_color)
        self.equip_ramal.configure(border_color=self.default_border_color)
        self.equip_location.configure(border_color=self.default_border_color)
        self.equip_description.configure(border_color=self.default_border_color)
        
        self.set_submitting_state(False)

    def submit(self):
        """Coleta os dados, valida todos os campos e os envia para o controlador."""
        # Executa todas as validações novamente antes de submeter
        is_type_valid = self._validate_required_combobox(self.equip_type)
        is_model_valid = self._validate_required_field(self.equip_model)
        is_ramal_valid = self._validate_numeric_field(self.equip_ramal)
        is_location_valid = self._validate_required_field(self.equip_location)
        is_desc_valid = self._validate_required_field(self.equip_description)
        
        if not all([is_type_valid, is_model_valid, is_ramal_valid, is_location_valid, is_desc_valid]):
            messagebox.showwarning("Campos Inválidos", "Por favor, preencha todos os campos obrigatórios e corrija os destacados em vermelho.")
            return

        data = {
            "tipo": self.equip_type.get().upper(),
            "modelo": self.equip_model.get().upper(),
            "ramal": self.equip_ramal.get().upper(),
            "localizacao": self.equip_location.get().upper(),
            "descricao": self.equip_description.get("1.0", "end-1c").upper()
        }
        self.controller.submit_equipment_occurrence(data, self.attachment_paths)

    def set_submitting_state(self, is_submitting):
        """Ativa/desativa os botões durante o processo de envio."""
        if is_submitting:
            self.submit_button.configure(state="disabled", text="A Enviar...")
        else:
            self.submit_button.configure(
                state="normal", text="Registar Problema")

