# ==============================================================================
# FICHEIRO: src/services/updater.py
# DESCRIÇÃO: Script auxiliar para descarregar e executar o novo instalador da aplicação.
#            Este script é executado pela aplicação principal quando uma atualização é detetada.
# ==============================================================================

import requests
import sys
import os
import subprocess
import time
import shutil

def run_update(download_url, current_app_path):
    """
    Descarrega o novo instalador e o executa.
    :param download_url: URL direta para o novo ficheiro do instalador.
    :param current_app_path: Caminho para o diretório de instalação atual da aplicação.
    """
    print("Iniciando processo de atualização...")
    print(f"URL de download do novo instalador: {download_url}")
    print(f"Caminho atual da aplicação: {current_app_path}")

    # Define o caminho para o ficheiro temporário do instalador
    # Usamos o diretório temporário do sistema para evitar problemas de permissão
    temp_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp", "REGTEL_Update")
    os.makedirs(temp_dir, exist_ok=True)
    installer_filename = download_url.split('/')[-1] # Pega o nome do ficheiro da URL
    if not installer_filename.endswith(".exe"):
        installer_filename = "REGTEL_Installer_New.exe" # Fallback se a URL não tiver nome .exe
    temp_installer_path = os.path.join(temp_dir, installer_filename)

    try:
        print(f"A descarregar o novo instalador para: {temp_installer_path}")
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status() # Levanta um erro para códigos de status HTTP ruins
            with open(temp_installer_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("Download concluído. A iniciar o novo instalador...")

        # Inicia o novo instalador em um processo separado
        # O Inno Setup é projetado para lidar com atualizações, desinstalando a versão antiga
        # e instalando a nova automaticamente.
        subprocess.Popen([temp_installer_path, '/SP-', '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'])
        
        # Opcional: Limpar o diretório temporário após um breve atraso
        # Isso é um pouco arriscado se o instalador ainda estiver a usar ficheiros de lá.
        # Geralmente, é melhor deixar o instalador limpar-se ou o sistema limpar o temp.
        # time.sleep(5) # Dá um tempo para o instalador iniciar
        # shutil.rmtree(temp_dir, ignore_errors=True) # Limpa o diretório temporário

        print("Novo instalador iniciado. A aplicação será atualizada.")

    except requests.exceptions.RequestException as e:
        print(f"Erro de rede ao descarregar o instalador: {e}")
        # Poderíamos adicionar uma messagebox aqui se quiséssemos feedback ao utilizador,
        # mas como é um script separado, é mais complexo.
    except FileNotFoundError:
        print(f"Erro: Ficheiro do instalador não encontrado em {temp_installer_path}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado durante a atualização: {e}")
    
    # É crucial que este script saia após tentar iniciar o instalador
    sys.exit(0)

if __name__ == "__main__":
    # Este script espera 2 argumentos: download_url e current_app_path
    if len(sys.argv) > 2:
        # sys.argv[0] é o nome do script
        download_url = sys.argv[1]
        current_app_path = sys.argv[2]
        run_update(download_url, current_app_path)
    else:
        print("Uso: python updater.py <download_url> <current_app_path>")
        sys.exit(1)
