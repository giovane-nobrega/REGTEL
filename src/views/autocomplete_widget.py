# ==============================================================================
# ARQUIVO: src/views/autocomplete_widget.py
# DESCRIÇÃO: Contém a classe para o widget de entrada de texto com
#            funcionalidade de autocompletar sugestões. (ATUALIZADA COM CORES)
# ==============================================================================

import customtkinter as ctk
import tkinter as tk

class AutocompleteEntry(ctk.CTkEntry):
    """
    Um CTkEntry personalizado que exibe uma lista de sugestões de preenchimento
    automático à medida que o usuário digita.
    """
    def __init__(self, master, suggestions=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.suggestions = suggestions if suggestions else []
        self._suggestion_listbox = None
        
        # Associa eventos a funções específicas
        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Down>", self._on_arrow_down)
        self.bind("<Up>", self._on_arrow_up)
        self.bind("<Return>", self._on_enter)
        self.bind("<Escape>", self._on_escape)

    def set_suggestions(self, suggestions):
        """Define ou atualiza a lista de sugestões disponíveis."""
        self.suggestions = suggestions

    def _on_key_release(self, event):
        """Chamado sempre que uma tecla é liberada no campo de entrada."""
        # Ignora teclas de navegação para não reabrir a lista desnecessariamente
        if event.keysym in ("Down", "Up", "Return", "Escape"):
            return

        value = self.get().upper()
        if not value:
            self._hide_suggestions()
            return

        # Filtra as sugestões para encontrar correspondências
        matches = [s for s in self.suggestions if value in s.upper()]
        if matches:
            self._show_suggestions(matches)
        else:
            self._hide_suggestions()

    def _show_suggestions(self, matches):
        """Cria e exibe a lista de sugestões abaixo do campo de entrada."""
        if self._suggestion_listbox:
            self._suggestion_listbox.destroy()

        parent_frame = self.winfo_toplevel()
        if hasattr(parent_frame, 'controller') and hasattr(parent_frame.controller, 'BASE_COLOR'):# pyright: ignore[reportAttributeAccessIssue]
            listbox_bg = parent_frame.controller.BASE_COLOR # pyright: ignore[reportAttributeAccessIssue]
            listbox_fg = parent_frame.controller.TEXT_COLOR # pyright: ignore[reportAttributeAccessIssue]
            select_bg = parent_frame.controller.PRIMARY_COLOR # pyright: ignore[reportAttributeAccessIssue]
        else:
            listbox_bg = "#2B2B2B"
            listbox_fg = "white"
            select_bg = "#1F6AA5"


        self._suggestion_listbox = tk.Listbox(
            self.master,
            background=listbox_bg,
            foreground=listbox_fg,
            selectbackground=select_bg,
            selectforeground="white",
            borderwidth=1,
            highlightthickness=0,
            relief="flat"
        )
        
        for match in matches:
            self._suggestion_listbox.insert(tk.END, match)
        
        listbox_height = min(len(matches), 5)
        self._suggestion_listbox.config(height=listbox_height)
        
        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height()
        width = self.winfo_width()
        
        self._suggestion_listbox.place(x=x, y=y, width=width)
        self._suggestion_listbox.lift()
        
        self._suggestion_listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
        
    def _hide_suggestions(self):
        """Destrói a lista de sugestões se ela existir."""
        if self._suggestion_listbox:
            self.after(150, self._suggestion_listbox.destroy)
            self._suggestion_listbox = None

    def _on_listbox_select(self, event=None):
        """Chamado quando um item da lista de sugestões é selecionado."""
        if not self._suggestion_listbox:
            return
            
        selected_indices = self._suggestion_listbox.curselection()
        if selected_indices:
            value = self._suggestion_listbox.get(selected_indices[0])
            self.delete(0, tk.END)
            self.insert(0, value)
            self._hide_suggestions()
            self.focus_set()

    def _on_focus_out(self, event=None):
        """Esconde as sugestões quando o widget perde o foco."""
        self._hide_suggestions()

    def _on_escape(self, event=None):
        """Esconde as sugestões quando a tecla Escape é pressionada."""
        self._hide_suggestions()
        return "break"

    def _on_arrow_down(self, event=None):
        """Navega para baixo na lista de sugestões."""
        if self._suggestion_listbox:
            current_selection = self._suggestion_listbox.curselection()
            next_index = 0 if not current_selection else current_selection[0] + 1
            if next_index < self._suggestion_listbox.size():
                self._suggestion_listbox.selection_clear(0, tk.END)
                self._suggestion_listbox.selection_set(next_index)
                self._suggestion_listbox.activate(next_index)
            return "break"

    def _on_arrow_up(self, event=None):
        """Navega para cima na lista de sugestões."""
        if self._suggestion_listbox:
            current_selection = self._suggestion_listbox.curselection()
            if current_selection:
                next_index = current_selection[0] - 1
                if next_index >= 0:
                    self._suggestion_listbox.selection_clear(0, tk.END)
                    self._suggestion_listbox.selection_set(next_index)
                    self._suggestion_listbox.activate(next_index)
            return "break"

    def _on_enter(self, event=None):
        """Seleciona o item destacado na lista quando Enter é pressionado."""
        if self._suggestion_listbox:
            self._on_listbox_select()
            return "break"
