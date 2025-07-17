import customtkinter as ctk
import tkinter as tk

class AutocompleteEntry(ctk.CTkEntry):
    """
    Um widget CTkEntry com uma lista de sugestões de autocompletar.
    """
    def __init__(self, master, suggestions=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.suggestions = suggestions if suggestions else []
        self._suggestion_listbox = None
        
        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Down>", self._on_arrow_down)
        self.bind("<Up>", self._on_arrow_up)
        self.bind("<Return>", self._on_enter)
        self.bind("<Escape>", self._on_focus_out)

    def set_suggestions(self, suggestions):
        """Define a lista de sugestões."""
        self.suggestions = suggestions

    def _on_key_release(self, event):
        """Atualiza a lista de sugestões a cada tecla pressionada."""
        if event.keysym in ("Down", "Up", "Return", "Escape"):
            return

        value = self.get().upper()
        if not value:
            self._hide_suggestions()
            return

        matches = [s for s in self.suggestions if s.startswith(value)]
        if matches:
            self._show_suggestions(matches)
        else:
            self._hide_suggestions()

    def _show_suggestions(self, matches):
        """Cria e exibe a lista de sugestões."""
        if self._suggestion_listbox:
            self._suggestion_listbox.destroy()

        self._suggestion_listbox = tk.Listbox(self.master,
                                              background="#2B2B2B",
                                              foreground="white",
                                              selectbackground="#1F6AA5",
                                              selectforeground="white",
                                              borderwidth=0,
                                              highlightthickness=0)
        
        for match in matches:
            self._suggestion_listbox.insert(tk.END, match)
        
        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height()
        width = self.winfo_width()
        
        self._suggestion_listbox.place(x=x, y=y, width=width)
        self._suggestion_listbox.lift()
        self._suggestion_listbox.bind("<Button-1>", self._on_listbox_select)
        
    def _hide_suggestions(self, event=None):
        """Esconde a lista de sugestões."""
        if self._suggestion_listbox:
            self._suggestion_listbox.destroy()
            self._suggestion_listbox = None

    def _on_listbox_select(self, event):
        """Preenche o campo com a sugestão selecionada."""
        if self._suggestion_listbox:
            selected_index = self._suggestion_listbox.curselection()
            if selected_index:
                # ALTERAÇÃO AQUI: Corrigido o bug para obter o valor da listbox
                value = self._suggestion_listbox.get(selected_index)
                self.delete(0, tk.END)
                self.insert(0, value)
                self._hide_suggestions()
                self.focus()

    def _on_focus_out(self, event=None):
        """Esconde as sugestões quando o campo perde o foco."""
        self.after(200, self._hide_suggestions)

    def _on_arrow_down(self, event=None):
        """Move a seleção para baixo na lista de sugestões."""
        if self._suggestion_listbox:
            current_selection = self._suggestion_listbox.curselection()
            if not current_selection:
                self._suggestion_listbox.selection_set(0)
            else:
                next_index = current_selection[0] + 1
                if next_index < self._suggestion_listbox.size():
                    self._suggestion_listbox.selection_clear(0, tk.END)
                    self._suggestion_listbox.selection_set(next_index)
                    self._suggestion_listbox.activate(next_index)
            return "break"

    def _on_arrow_up(self, event=None):
        """Move a seleção para cima na lista de sugestões."""
        if self._suggestion_listbox:
            current_selection = self._suggestion_listbox.curselection()
            if current_selection:
                next_index = current_selection[0] - 1
                if next_index >= 0:
                    self._suggestion_listbox.selection_clear(0, tk.END)
                    self.after(10, lambda: self._suggestion_listbox.selection_set(next_index))
                    self._suggestion_listbox.activate(next_index)
            return "break"

    def _on_enter(self, event=None):
        """Confirma a seleção da lista com a tecla Enter."""
        if self._suggestion_listbox:
            self._on_listbox_select(None)
            return "break"
