# ==============================================================================
# FICHEIRO: main.py
# DESCRIÇÃO: Ponto de entrada principal da aplicação REGTEL.
# DATA DA ATUALIZAÇÃO: 27/08/2025
# ==============================================================================

import sys
import os
from tkinter import messagebox
import traceback

# Adiciona a pasta 'src' ao caminho do Python para encontrar os módulos
SRC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

try:
    # Importa a classe principal da aplicação a partir do módulo app
    from app import App
except ImportError as ea:
    # Mostra um erro claro se a estrutura de pastas estiver incorreta
    messagebox.showerror(
        "Erro de Estrutura do Projeto",
        f"Não foi possível encontrar o módulo 'app' no diretório 'src'.\n"
        f"Verifique se a estrutura de pastas do projeto está correta.\n\n"
        f"Detalhes: {ea}"
    )
    sys.exit(1)

# ==============================================================================
# PONTO DE ENTRADA DA APLICAÇÃO
# ==============================================================================
if __name__ == "__main__":
    """
    Função principal que é executada quando o script é chamado diretamente.
    """
    try:
        # Cria uma instância da aplicação principal e inicia o seu loop de eventos.
        app = App()
        app.mainloop()
    except Exception as e:
        # Captura qualquer erro fatal que não foi tratado dentro da aplicação.
        messagebox.showerror(
            "Erro Fatal",
            f"Ocorreu um erro inesperado e a aplicação será fechada:\n\n{e}"
        )
        # Imprime o traceback completo no terminal para ajudar na depuração.
        print(f"Erro fatal: {e}")
        traceback.print_exc()
