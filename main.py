import sys
import os

# Adiciona a pasta 'src' diretamente ao caminho de busca do Python.
SRC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, SRC_PATH)

from app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()