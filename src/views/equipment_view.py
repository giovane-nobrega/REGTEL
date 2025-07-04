import customtkinter as ctk
class EquipmentView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        label = ctk.CTkLabel(self, text="Tela de Registo de Problema de Equipamento - Em Construção", font=ctk.CTkFont(size=20))
        label.pack(pady=20, padx=20)
        back_button = ctk.CTkButton(self, text="Voltar ao Menu", command=lambda: controller.show_frame("MainMenuView"))
        back_button.pack(pady=10)