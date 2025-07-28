import customtkinter as ctk
import tkinter as tk

class AutocompleteEntry(ctk.CTkEntry):
    def __init__(self, master, suggestions=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.suggestions = suggestions if suggestions else []
        self._suggestion_listbox = None
        
        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Down>", self._on_arrow_down)
        self.bind("<Up>", self._on_arrow_up)
        self.bind("<Return>", self._on_enter)
        self.bind("<Escape>", self._on_escape)

    def set_suggestions(self, suggestions):
        self.suggestions = suggestions

    def _on_key_release(self, event):
        if event.keysym in ("Down", "Up", "Return", "Escape"):
            return

        value = self.get().upper()
        if not value:
            self._hide_suggestions()
            return

        matches = [s for s in self.suggestions if value in s]
        if matches:
            self._show_suggestions(matches)
        else:
            self._hide_suggestions()

    def _show_suggestions(self, matches):
        if self._suggestion_listbox:
            self._suggestion_listbox.destroy()

        self._suggestion_listbox = tk.Listbox(self.master,
                                              background="#2B2B2B",
                                              foreground="white",
                                              selectbackground="#1F6AA5",
                                              selectforeground="white",
                                              borderwidth=1,
                                              highlightthickness=0,
                                              relief="flat")
        
        for match in matches:
            self._suggestion_listbox.insert(tk.END, match)
        
        listbox_height = min(len(matches), 5)
        self._suggestion_listbox.config(height=listbox_height)
        
        x = self.winfo_x()
        y = self.winfo_y() + self.winfo_height()
        width = self.winfo_width()
        
        self._suggestion_listbox.place(x=x, y=y, width=width)
        self._suggestion_listbox.lift()
        # --- ALTERAÇÃO AQUI: Usa um evento diferente para mais fiabilidade ---
        self._suggestion_listbox.bind("<<ListboxSelect>>", self._on_listbox_select)
        # --- FIM DA ALTERAÇÃO ---
        
    def _hide_suggestions(self):
        if self._suggestion_listbox:
            self._suggestion_listbox.destroy()
            self._suggestion_listbox = None

    def _on_listbox_select(self, event=None):
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
        self.after(200, self._hide_suggestions)

    def _on_escape(self, event=None):
        self._hide_suggestions()
        return "break"

    def _on_arrow_down(self, event=None):
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
        if self._suggestion_listbox:
            self._on_listbox_select()
            return "break"
