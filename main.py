import sys
import os
import traceback

# 1. Adiciona a pasta 'src' diretamente ao caminho de busca do Python.
SRC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, SRC_PATH)

# 2. Agora que o caminho está configurado, importamos e executamos a aplicação.
from app import App  # noqa


if __name__ == "__main__":
    try:
        print(
            f"A executar a partir de: {os.path.dirname(os.path.abspath(__file__))}")
        print(f"Caminho do 'src' adicionado: {SRC_PATH}")
        print("-" * 20)

        app = App()
        app.mainloop()
    except Exception as e:
        print("\n" + "="*20 + " ERRO FATAL " + "="*20)
        print(f"Ocorreu uma exceção não tratada: {e}")
        traceback.print_exc()
        print("="*52)
        # Mantém a janela do terminal aberta para ver o erro.
        input("Pressione Enter para fechar...")