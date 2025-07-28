import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

# --- CONFIGURAÇÕES ---
# 1. Altere para o ID da sua planilha
SPREADSHEET_ID = "1ymzB0QiZiuTnLk9h3qfFnZgcxkTKJUeT-3rn4bYqtQA" 

# 2. Não altere estas linhas
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
CLIENT_SECRET_FILE = "client_secrets.json"
TOKEN_FILE = "token.json"
# --------------------

def autenticar():
    """Função de autenticação simplificada para o teste."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Erro ao atualizar o token: {e}")
                creds = None # Força um novo login
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"ERRO: Não foi possível carregar 'client_secrets.json'. Verifique se o ficheiro está na pasta correta e se é do tipo 'Aplicativo para computador'.")
                print(f"Detalhes do erro: {e}")
                return None

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return creds

def main():
    """Função principal do teste."""
    print("--- Iniciando teste de conexão com o Google Sheets ---")
    
    print("\nPasso 1: Autenticando...")
    credentials = autenticar()
    
    if not credentials:
        print("\nFalha na autenticação. Verifique os erros acima.")
        return
        
    print("Autenticação bem-sucedida!")
    
    try:
        print("\nPasso 2: Conectando ao gspread...")
        gc = gspread.authorize(credentials)
        print("Conexão com gspread estabelecida.")
        
        print(f"\nPasso 3: Abrindo a planilha com ID: {SPREADSHEET_ID}...")
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        print("Planilha aberta com sucesso!")
        
        print("\nPasso 4: Listando todas as abas (worksheets)...")
        worksheets = spreadsheet.worksheets()
        worksheet_names = [ws.title for ws in worksheets]
        
        print("\n--- TESTE CONCLUÍDO COM SUCESSO! ---")
        print(f"As seguintes abas foram encontradas: {worksheet_names}")
        
    except Exception as e:
        print("\n--- O TESTE FALHOU ---")
        print("Ocorreu um erro ao tentar aceder à planilha.")
        print(f"Tipo de Erro: {type(e).__name__}")
        print(f"Detalhes do Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
    input("\nPressione Enter para fechar...")

