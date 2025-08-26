# ==============================================================================
# ARQUIVO: main.py
# DESCRIÇÃO: Ponto de entrada principal da aplicação REGTEL.
#            Configura o ambiente e inicia a janela principal.
# ==============================================================================

import sys
import os
from tkinter import messagebox
import traceback # Importado para imprimir o traceback completo em caso de erros
from builtins import ImportError, Exception, print # CORRIGIDO: Importa built-ins explicitamente para satisfazer o Pylance

# Adiciona a pasta 'src' ao caminho do Python para encontrar os módulos
# (Assumindo que este arquivo está na raiz do projeto, e os outros em /src)
SRC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

try:
    # Importa a classe principal da aplicação a partir do módulo app
    from app import App
except ImportError as ea: # A exceção é capturada como 'ea'
    # Mostra um erro claro se a estrutura de pastas estiver incorreta
    messagebox.showerror(
        "Erro de Importação",
        f"Não foi possível encontrar o módulo 'app'. Verifique a estrutura de pastas.\n\n"
        f"Detalhes: {ea}" # CORRIGIDO: Usando 'ea' em vez de 'e'
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
        # O loop de eventos é o que mantém a interface gráfica responsiva.
        app = App()
        app.mainloop()
    except Exception as e:
        # Captura qualquer erro fatal que não foi tratado dentro da aplicação.
        # Exibe uma caixa de mensagem de erro para o usuário.
        messagebox.showerror(
            "Erro Fatal",
            f"Ocorreu um erro inesperado e a aplicação será fechada:\n\n{e}"
        )
        # Imprime o traceback completo no terminal para ajudar na depuração.
        print(f"Erro fatal: {e}") # Usando print explicitamente
        traceback.print_exc()
