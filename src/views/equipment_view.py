import customtkinter as ctk
from tkinter import messagebox


class EquipmentView(ctk.CTkFrame):
    """Tela para o registo de problemas de equipamento (Prefeitura)."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ctk.CTkLabel(self, text="Registar Suporte Técnico de Equipamento",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 20))

        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", padx=20, pady=10)
        form_frame.grid_columnconfigure(1, weight=1)

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
            row=4, column=1, padx=10, pady=10, sticky="ew")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(10, 0))
        button_frame.grid_columnconfigure((0, 1), weight=1)

        self.back_button = ctk.CTkButton(button_frame, text="Voltar ao Menu", command=lambda: self.controller.show_frame(
            "MainMenuView"), fg_color="gray50", hover_color="gray40")
        self.back_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.submit_button = ctk.CTkButton(
            button_frame, text="Registar Problema", command=self.submit, height=40)
        self.submit_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def on_show(self):
        """Limpa o formulário sempre que a tela é exibida."""
        self.equip_type.set("")
        self.equip_model.delete(0, "end")
        self.equip_serial.delete(0, "end")
        self.equip_location.delete(0, "end")
        self.equip_description.delete("1.0", "end")
        self.set_submitting_state(False)

    def submit(self):
        """Chama o controlador para submeter a ocorrência."""
        data = {
            "tipo": self.equip_type.get(),
            "modelo": self.equip_model.get(),
            "serial": self.equip_serial.get(),
            "localizacao": self.equip_location.get(),
            "descricao": self.equip_description.get("1.0", "end-1c")
        }
        self.controller.submit_equipment_occurrence(data)

    def set_submitting_state(self, is_submitting):
        """Ativa/desativa os botões durante o envio."""
        if is_submitting:
            self.submit_button.configure(state="disabled", text="A enviar...")
        else:
            self.submit_button.configure(
                state="normal", text="Registar Problema")
