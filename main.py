import sys
import os

# 1. Adiciona a pasta 'src' diretamente ao caminho de busca do Python.
#    Isto permite que todos os módulos dentro de 'src' se importem uns aos outros de forma simples.
SRC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, SRC_PATH)

# 2. Agora que o caminho está configurado, importamos e executamos a aplicação.
#    O comentário '# noqa' impede que o VS Code mova esta linha para o topo.
from app import App  # noqa


if __name__ == "__main__":
    print(
        f"A executar a partir de: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"Caminho do 'src' adicionado: {SRC_PATH}")
    print("-" * 20)

    app = App()
    app.mainloop()
