import customtkinter as ctk
from tkinter import messagebox, filedialog
import os

class EquipmentView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.attachment_paths = []

        # --- Configuração da Responsividade ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Linha do formulário expande

        ctk.CTkLabel(self, text="Registar Suporte Técnico de Equipamento",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 20), sticky="ew")

        form_frame = ctk.CTkFrame(self)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_rowconfigure(4, weight=1) # Linha da descrição expande

        ctk.CTkLabel(form_frame, text="Tipo de Equipamento:").grid(
            row=0, column=0, padx=10, pady=10, sticky="w")
        self.equip_type = ctk.CTkComboBox(form_frame, values=[
                                          "Telefone IP", "ATA", "Softphone", "Fonte de Alimentação", "Outro"])
        self.equip_type.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Marca/Modelo:").grid(row=1,
                                                            column=0, padx=10, pady=10, sticky="w")
        self.equip_model = ctk.CTkEntry(
            form_frame, placeholder_text="Ex: Grandstream GXP1610")
        self.equip_model.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Identificação (Nº Série):").grid(
            row=2, column=0, padx=10, pady=10, sticky="w")
        self.equip_serial = ctk.CTkEntry(
            form_frame, placeholder_text="Ex: 987654321XYZ")
        self.equip_serial.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Localização:").grid(
            row=3, column=0, padx=10, pady=10, sticky="w")
        self.equip_location = ctk.CTkEntry(
            form_frame, placeholder_text="Ex: Prédio A, Sala 101, Mesa 5")
        self.equip_location.grid(
            row=3, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(form_frame, text="Descrição do Problema:").grid(
            row=4, column=0, padx=10, pady=10, sticky="nw")
        self.equip_description = ctk.CTkTextbox(form_frame, height=120)
        self.equip_description.grid(
            row=4, column=1, padx=10, pady=10, sticky="nsew")

        attachment_frame = ctk.CTkFrame(self)
        attachment_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        ctk.CTkLabel(attachment_frame, text="Anexar Imagens (Opcional):", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10,5), pady=10)
        
        attach_button = ctk.CTkButton(attachment_frame, text="Selecionar...", command=self._select_files)
        attach_button.pack(side="left", padx=5, pady=10)

        self.attachment_label = ctk.CTkLabel(attachment_frame, text="Nenhum ficheiro.", text_color="gray60")
        self.attachment_label.pack(side="left", padx=5, pady=10)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, padx=20, pady=(10, 10), sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.back_button = ctk.CTkButton(button_frame, text="Voltar ao Menu", command=lambda: self.controller.show_frame(
            "MainMenuView"), fg_color="gray50", hover_color="gray40")
        self.back_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.submit_button = ctk.CTkButton(
            button_frame, text="Registar Problema", command=self.submit, height=40)
        self.submit_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _select_files(self):
        filepaths = filedialog.askopenfilenames(
            title="Selecione as imagens",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg")]
        )
        if filepaths:
            self.attachment_paths = list(filepaths)
            self.attachment_label.configure(text=f"{len(filepaths)} ficheiro(s) selecionado(s).")
        else:
            self.attachment_paths = []
            self.attachment_label.configure(text="Nenhum ficheiro.")

    def on_show(self):
        self.equip_type.set("")
        self.equip_model.delete(0, "end")
        self.equip_serial.delete(0, "end")
        self.equip_location.delete(0, "end")
        self.equip_description.delete("1.0", "end")
        self.attachment_paths = []
        self.attachment_label.configure(text="Nenhum ficheiro.")
        self.set_submitting_state(False)

    def submit(self):
        data = {
            "tipo": self.equip_type.get().upper(),
            "modelo": self.equip_model.get().upper(),
            "serial": self.equip_serial.get().upper(),
            "localizacao": self.equip_location.get().upper(),
            "descricao": self.equip_description.get("1.0", "end-1c").upper()
        }
        self.controller.submit_equipment_occurrence(data, self.attachment_paths)

    def set_submitting_state(self, is_submitting):
        if is_submitting:
            self.submit_button.configure(state="disabled", text="A enviar...")
        else:
            self.submit_button.configure(
                state="normal", text="Registrar Problema")
