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
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Registar Suporte Técnico de Equipamento",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 20), sticky="ew")

        form_frame = ctk.CTkFrame(self)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_rowconfigure(4, weight=1)

        # ... (campos do formulário de equipamento) ...

        # ALTERAÇÃO AQUI: Adicionado o frame de anexos
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

        self.back_button = ctk.CTkButton(button_frame, text="Voltar ao Menu", command=lambda: self.controller.show_frame("MainMenuView"), fg_color="gray50", hover_color="gray40")
        self.back_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.submit_button = ctk.CTkButton(button_frame, text="Registar Problema", command=self.submit, height=40)
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
        self.attachment_paths = []
        self.attachment_label.configure(text="Nenhum ficheiro.")
        # ... (resto do on_show)
        
    def submit(self):
        data = {
            "tipo": self.equip_type.get().upper(),
            "modelo": self.equip_model.get().upper(),
            "serial": self.equip_serial.get().upper(),
            "localizacao": self.equip_location.get().upper(),
            "descricao": self.equip_description.get("1.0", "end-1c").upper()
        }
        self.controller.submit_equipment_occurrence(data, self.attachment_paths)

    # ... (resto do código da classe)
