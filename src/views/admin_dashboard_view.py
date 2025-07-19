import customtkinter as ctk
from functools import partial
from tkinter import messagebox
import threading
# ALTERAÇÃO AQUI: As importações do Matplotlib foram removidas do topo do ficheiro
# para serem carregadas apenas quando necessário.

class AdminDashboardView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # --- Configuração da Responsividade da Grelha Principal ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.original_statuses = {}
        self.status_updaters = {}
        self.original_roles = {}
        self.role_updaters = {}
        self.status_chart_canvas = None
        self.operator_chart_canvas = None
        self.current_analysis_list = []

        ctk.CTkLabel(self, text="Dashboard de Gestão", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 10), sticky="ew")
        
        self.tabview = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        self.occurrences_tab = self.tabview.add("Ocorrências")
        self.analysis_tab = self.tabview.add("Análise de Dados")
        self.access_tab = self.tabview.add("Gerenciar Acessos")
        self.users_tab = self.tabview.add("Gerenciar Usuários")
        
        self.setup_occurrences_tab()
        self.setup_analysis_tab()
        self.setup_access_tab()
        self.setup_users_tab()
        
        back_button = ctk.CTkButton(self, text="Voltar ao Menu", command=lambda: self.controller.show_frame("MainMenuView"), fg_color="gray50", hover_color="gray40")
        back_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

    def setup_analysis_tab(self):
        main_analysis_frame = ctk.CTkFrame(self.analysis_tab, fg_color="transparent")
        main_analysis_frame.pack(fill="both", expand=True)
        main_analysis_frame.grid_columnconfigure(0, weight=1)
        main_analysis_frame.grid_columnconfigure(1, weight=1)
        main_analysis_frame.grid_rowconfigure(0, weight=1)

        left_column = ctk.CTkFrame(main_analysis_frame, fg_color="transparent")
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        filter_frame = ctk.CTkFrame(left_column)
        filter_frame.pack(fill="x", padx=5, pady=5, anchor="n")
        filter_frame.grid_columnconfigure((0, 1, 2), weight=1)

        status_filter_group = ctk.CTkFrame(filter_frame, fg_color="transparent")
        status_filter_group.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(status_filter_group, text="Filtrar por Status:").pack(side="top", anchor="w")
        self.status_filter_menu = ctk.CTkOptionMenu(status_filter_group, values=["Todos", "Registrado", "Em Análise", "Aguardando Terceiros", "Resolvido", "Cancelado"], command=self.apply_filters)
        self.status_filter_menu.pack(side="top", fill="x", expand=True)

        role_filter_group = ctk.CTkFrame(filter_frame, fg_color="transparent")
        role_filter_group.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(role_filter_group, text="Filtrar por Grupo:").pack(side="top", anchor="w")
        self.role_filter_menu = ctk.CTkOptionMenu(role_filter_group, values=["Todos", "partner", "prefeitura"], command=self.apply_filters)
        self.role_filter_menu.pack(side="top", fill="x", expand=True)

        export_group = ctk.CTkFrame(filter_frame, fg_color="transparent")
        export_group.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(export_group, text="").pack(side="top")
        export_button = ctk.CTkButton(export_group, text="Exportar para CSV", command=self.export_to_csv)
        export_button.pack(side="top", fill="x", expand=True)

        self.stats_label = ctk.CTkLabel(left_column, text="Estatísticas: Carregando...", justify="left", font=ctk.CTkFont(size=14, weight="bold"))
        self.stats_label.pack(anchor="w", padx=10, pady=20)

        # --- Coluna da Direita com Gráficos (Agora com Scroll) ---
        right_column = ctk.CTkFrame(main_analysis_frame)
        right_column.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # ALTERAÇÃO AQUI: Adicionado um frame rolável para conter os gráficos
        scrollable_graphs_frame = ctk.CTkScrollableFrame(right_column, fg_color="transparent")
        scrollable_graphs_frame.pack(fill="both", expand=True)

        # Frame para o primeiro gráfico
        self.status_chart_frame = ctk.CTkFrame(scrollable_graphs_frame)
        self.status_chart_frame.pack(fill="x", expand=True, padx=5, pady=(0, 5))
        self.status_chart_frame.configure(height=300) # Altura mínima
        
        # Frame para o segundo gráfico
        self.operator_chart_frame = ctk.CTkFrame(scrollable_graphs_frame)
        self.operator_chart_frame.pack(fill="x", expand=True, padx=5, pady=5)
        self.operator_chart_frame.configure(height=300) # Altura mínima

    def export_to_csv(self):
        if not self.current_analysis_list:
            messagebox.showwarning("Nenhum Dado", "Não há dados para exportar. Por favor, aplique um filtro primeiro.")
            return
        self.controller.export_analysis_to_csv(self.current_analysis_list)

    def apply_filters(self, _=None):
        status = self.status_filter_menu.get()
        role = self.role_filter_menu.get()
        
        self.stats_label.configure(text="Estatísticas: Calculando...")
        if self.status_chart_canvas: self.status_chart_canvas.get_tk_widget().destroy()
        if self.operator_chart_canvas: self.operator_chart_canvas.get_tk_widget().destroy()
        for widget in self.status_chart_frame.winfo_children(): widget.destroy()
        for widget in self.operator_chart_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.status_chart_frame, text="Carregando...").pack(expand=True)
        ctk.CTkLabel(self.operator_chart_frame, text="Carregando...").pack(expand=True)

        threading.Thread(target=self._apply_filters_thread, args=(status, role), daemon=True).start()

    def _apply_filters_thread(self, status, role):
        filtered_list = self.controller.get_all_occurrences(status_filter=status, role_filter=role)
        self.after(0, self._populate_analysis_results, filtered_list)

    def _populate_analysis_results(self, results):
        self.current_analysis_list = results
        for widget in self.status_chart_frame.winfo_children(): widget.destroy()
        for widget in self.operator_chart_frame.winfo_children(): widget.destroy()

        if not results:
            self.stats_label.configure(text="Estatísticas: 0 ocorrências encontradas.")
            ctk.CTkLabel(self.status_chart_frame, text="Nenhum dado para exibir.").pack(expand=True)
            ctk.CTkLabel(self.operator_chart_frame, text="Nenhum dado para exibir.").pack(expand=True)
            return
        
        total = len(results)
        status_counts = {"Registrado": 0, "Em Análise": 0, "Aguardando Terceiros": 0, "Resolvido": 0, "Cancelado": 0}
        operator_counts = {}
        for item in results:
            status = item.get('Status', 'N/A')
            if status in status_counts:
                status_counts[status] += 1
            if 'Operadora A' in item:
                op_a = item['Operadora A']
                operator_counts[op_a] = operator_counts.get(op_a, 0) + 1
            if 'Operadora B' in item:
                op_b = item['Operadora B']
                operator_counts[op_b] = operator_counts.get(op_b, 0) + 1
        
        stats_text = f"Total de Ocorrências Encontradas: {total}"
        self.stats_label.configure(text=stats_text)
        
        self.update_chart(self.status_chart_frame, status_counts, "Ocorrências por Status", "Nº de Ocorrências", "status_chart_canvas")
        self.update_chart(self.operator_chart_frame, operator_counts, "Menções por Operadora", "Nº de Menções", "operator_chart_canvas")

    def update_chart(self, frame, data, title, ylabel, canvas_attr_name):
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            for widget in frame.winfo_children():
                widget.destroy()
            ctk.CTkLabel(frame, text="Erro: A biblioteca 'matplotlib' é necessária para exibir gráficos.\nInstale-a com: pip install matplotlib", wraplength=300, justify="center").pack(expand=True, padx=10)
            return

        if not data or sum(data.values()) == 0:
            ctk.CTkLabel(frame, text=f"Nenhum dado para o gráfico\n'{title}'").pack(expand=True)
            return

        labels = [label.replace(" ", "\n") for label in data.keys()]
        values = data.values()

        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        fig.patch.set_facecolor("#2B2B2B") 
        ax.set_facecolor("#2B2B2B")

        bars = ax.bar(labels, values, color="#1F6AA5")
        ax.tick_params(axis='x', colors='white', rotation=45, labelsize=8)
        ax.tick_params(axis='y', colors='white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('gray')
        ax.spines['left'].set_color('gray')
        ax.set_ylabel(ylabel, color='white')
        ax.set_title(title, color='white')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        setattr(self, canvas_attr_name, canvas)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def setup_access_tab(self):
        ctk.CTkLabel(self.access_tab, text="Solicitações de Acesso Pendentes").pack(pady=5)
        self.pending_users_frame = ctk.CTkScrollableFrame(self.access_tab, label_text="Carregando...")
        self.pending_users_frame.pack(fill="both", expand=True, pady=5, padx=5)
        refresh_button = ctk.CTkButton(self.access_tab, text="Atualizar Lista", command=self.load_access_requests)
        refresh_button.pack(pady=5, padx=5, fill="x")

    def setup_users_tab(self):
        ctk.CTkLabel(self.users_tab, text="Lista de Todos os Usuários").pack(pady=5)
        self.all_users_frame = ctk.CTkScrollableFrame(self.users_tab, label_text="Carregando...")
        self.all_users_frame.pack(fill="both", expand=True, pady=5, padx=5)
        button_frame = ctk.CTkFrame(self.users_tab, fg_color="transparent")
        button_frame.pack(fill="x", pady=5, padx=5)
        save_button = ctk.CTkButton(button_frame, text="Salvar Alterações de Perfil", command=self.save_role_changes)
        save_button.pack(side="left", padx=(0, 10), expand=True, fill="x")
        refresh_button = ctk.CTkButton(button_frame, text="Atualizar Lista", command=self.load_all_users)
        refresh_button.pack(side="left", expand=True, fill="x")

    def setup_occurrences_tab(self):
        ctk.CTkLabel(self.occurrences_tab, text="Visão Geral de Todas as Ocorrências").pack(pady=5)
        self.all_occurrences_frame = ctk.CTkScrollableFrame(self.occurrences_tab, label_text="Carregando...")
        self.all_occurrences_frame.pack(fill="both", expand=True, pady=5, padx=5)
        button_frame = ctk.CTkFrame(self.occurrences_tab, fg_color="transparent")
        button_frame.pack(fill="x", pady=5, padx=5)
        save_button = ctk.CTkButton(button_frame, text="Salvar Alterações de Status", command=self.save_status_changes)
        save_button.pack(side="left", padx=(0, 10), expand=True, fill="x")
        refresh_button = ctk.CTkButton(button_frame, text="Atualizar Lista", command=self.load_all_occurrences)
        refresh_button.pack(side="left", expand=True, fill="x")

    def on_show(self):
        self.on_tab_change()

    def on_tab_change(self):
        selected_tab = self.tabview.get()
        if selected_tab == "Ocorrências":
            self.load_all_occurrences()
        elif selected_tab == "Gerenciar Acessos":
            self.load_access_requests()
        elif selected_tab == "Gerenciar Usuários":
            self.load_all_users()
        elif selected_tab == "Análise de Dados":
            self.apply_filters()

    def load_access_requests(self):
        self.pending_users_frame.configure(label_text="Carregando solicitações...")
        threading.Thread(target=self._load_access_data_thread, daemon=True).start()

    def _load_access_data_thread(self):
        pending_list = self.controller.get_pending_requests()
        self.after(0, self._populate_access_requests, pending_list)

    def _populate_access_requests(self, pending_list):
        for widget in self.pending_users_frame.winfo_children(): widget.destroy()
        if not pending_list:
            self.pending_users_frame.configure(label_text="Nenhuma solicitação pendente.")
            return
        self.pending_users_frame.configure(label_text="")
        for user in pending_list:
            card = ctk.CTkFrame(self.pending_users_frame)
            card.pack(fill="x", pady=5)
            info_text = f"Nome: {user.get('name', 'N/A')} ({user.get('username', 'N/A')})\nE-mail: {user['email']}\nVínculo: {user.get('company', user.get('role'))}"
            ctk.CTkLabel(card, text=info_text, justify="left").pack(side="left", padx=10, pady=5)
            reject_button = ctk.CTkButton(card, text="Rejeitar", command=partial(self.controller.update_user_access, user['email'], 'rejected'), fg_color="red")
            reject_button.pack(side="right", padx=5, pady=5)
            approve_button = ctk.CTkButton(card, text="Aprovar", command=partial(self.controller.update_user_access, user['email'], 'approved'), fg_color="green")
            approve_button.pack(side="right", padx=5, pady=5)

    def load_all_users(self):
        self.all_users_frame.configure(label_text="Carregando usuários...")
        threading.Thread(target=self._load_users_data_thread, daemon=True).start()

    def _load_users_data_thread(self):
        all_users_list = self.controller.get_all_users()
        self.after(0, self._populate_all_users, all_users_list)

    def _populate_all_users(self, all_users_list):
        self.role_updaters.clear()
        self.original_roles.clear()
        for widget in self.all_users_frame.winfo_children(): widget.destroy()
        if not all_users_list:
            self.all_users_frame.configure(label_text="Nenhum usuário encontrado.")
            return
        self.all_users_frame.configure(label_text="")
        role_options = ["admin", "partner", "prefeitura"]
        for user in all_users_list:
            email = user.get('email')
            self.original_roles[email] = user.get('role')
            card = ctk.CTkFrame(self.all_users_frame)
            card.pack(fill="x", pady=5)
            card.grid_columnconfigure(0, weight=1)
            
            company_info = f" ({user.get('company')})" if user.get('role') == 'partner' and user.get('company') else ""
            info_text = f"{user.get('name', 'Nome não informado')} (@{user.get('username', 'N/A')}){company_info}"
            
            info_label = ctk.CTkLabel(card, text=info_text, anchor="w")
            info_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            
            role_combo = ctk.CTkComboBox(card, values=role_options, width=150)
            role_combo.set(user.get('role'))
            role_combo.grid(row=0, column=1, padx=10, pady=10, sticky="e")
            self.role_updaters[email] = role_combo

    def save_role_changes(self):
        changes_to_save = {}
        for email, combo_widget in self.role_updaters.items():
            new_role = combo_widget.get()
            if self.original_roles.get(email) != new_role:
                changes_to_save[email] = new_role
        if not changes_to_save:
            messagebox.showinfo("Nenhuma Alteração", "Nenhum perfil de usuário foi alterado.")
            return
        for email, new_role in changes_to_save.items():
            self.controller.update_user_role(email, new_role)

    def load_all_occurrences(self):
        self.all_occurrences_frame.configure(label_text="Carregando ocorrências...")
        threading.Thread(target=self._load_occurrences_data_thread, daemon=True).start()

    def _load_occurrences_data_thread(self):
        all_occurrences_list = self.controller.get_all_occurrences()
        self.after(0, self._populate_all_occurrences, all_occurrences_list)

    def _populate_all_occurrences(self, all_occurrences_list):
        self.status_updaters.clear()
        self.original_statuses.clear()
        for widget in self.all_occurrences_frame.winfo_children(): widget.destroy()
        if not all_occurrences_list:
            self.all_occurrences_frame.configure(label_text="Nenhuma ocorrência encontrada.")
            return
        self.all_occurrences_frame.configure(label_text="")
        status_options = ["REGISTRADO", "EM ANÁLISE", "AGUARDANDO TERCEIROS", "RESOLVIDO", "CANCELADO"]
        for item in all_occurrences_list:
            item_id = item.get('ID', 'N/A')
            self.original_statuses[item_id] = item.get('Status', 'N/A')
            card = ctk.CTkFrame(self.all_occurrences_frame)
            card.pack(fill="x", padx=5, pady=5)
            card.grid_columnconfigure(0, weight=1); card.grid_columnconfigure(1, weight=0)
            title = item.get('Título da Ocorrência', item.get('Tipo de Equipamento', 'N/A'))
            date = item.get('Data de Registro', 'N/A'); email = item.get('Email do Registrador', 'N/A')
            ctk.CTkLabel(card, text=f"ID: {item_id} - {title}", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 0))
            ctk.CTkLabel(card, text=f"Registrado por: {email} em {date}", anchor="w", text_color="gray60").grid(row=1, column=0, sticky="w", padx=10, pady=(0,5))
            status_combo = ctk.CTkComboBox(card, values=status_options, width=180)
            status_combo.set(self.original_statuses[item_id])
            status_combo.grid(row=1, column=1, sticky="e", padx=10, pady=(0,5))
            self.status_updaters[item_id] = status_combo

    def save_status_changes(self):
        changes_to_save = {}
        for occ_id, combo_widget in self.status_updaters.items():
            if self.original_statuses.get(occ_id) != combo_widget.get():
                changes_to_save[occ_id] = combo_widget.get()
        self.controller.save_occurrence_status_changes(changes_to_save)
