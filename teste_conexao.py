import gspread
from datetime import datetime
import os  # Importa o módulo 'os' para interagir com o sistema operacional
import auth  # Módulo de autenticação centralizado

 # <<-- COLOQUE O NOME EXATO DA SUA PLANILHA AQUI -->>
NOME_DA_PLANILHA = "Dados_da_Telefonia"
# <<---------------------------------------------------->>

def main():
    """
    Função principal que lida com a autenticação e escrita na planilha.
    """
    # --- Exemplo de como listar arquivos (o equivalente a 'ls') ---
    print("Listando arquivos no diretório atual:")
    print(os.listdir('.'))
    print("-" * 20)
    # -------------------------------------------------------------
    print("Verificando credenciais...")
    creds = auth.load_credentials()

    if not creds or not creds.valid:
        print("Iniciando novo login...")
        try:
            creds = auth.run_login_flow()
            auth.save_credentials(creds)
        except Exception as e:
            print(f"O fluxo de autenticação falhou ou foi cancelado: {e}")
            return  # Sai se o login falhar

    if not creds:
        print("Não foi possível obter as credenciais. Saindo.")
        return

    try:
        print("Autenticação bem-sucedida!")

        # Autoriza o gspread com as credenciais obtidas
        gc = gspread.authorize(creds)

        print(f"Acessando a planilha '{NOME_DA_PLANILHA}'...")
        # Abre a planilha pelo nome e seleciona a primeira aba (sheet1)
        planilha = gc.open(NOME_DA_PLANILHA).sheet1

        print("Adicionando uma nova linha de teste...")

        # Pega a data e hora atuais para o nosso teste
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Acessa o e-mail de forma segura usando o módulo de autenticação
        email_usuario = auth.get_user_email(creds)

        # Cria a linha de dados que vamos inserir
        linha_para_inserir = ["ID de Teste", "Conexão OK via script", agora, email_usuario]

        # Insere a linha na planilha
        planilha.append_row(linha_para_inserir)

        print("="*30)
        print("SUCESSO! Linha adicionada à sua planilha.")
        print("="*30)

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

# Executa a função principal quando o script é rodado
if __name__ == '__main__':
    main()