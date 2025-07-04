import uuid
import gspread
from datetime import datetime
from gspread.exceptions import WorksheetNotFound

NOME_DA_PLANILHA = "Dados_da_Telefonia"


def authorize_gspread(credentials):
    """Usa as credenciais para autorizar o cliente gspread."""
    return gspread.authorize(credentials)


def save_occurrence_with_tests(credentials, user_email, occurrence_title, tests_list):
    """
    Salva uma ocorrência principal e seus testes associados em abas separadas da planilha.
    Levanta exceções específicas em caso de erro para a UI tratar.
    """
    try:
        gc = authorize_gspread(credentials)
        planilha = gc.open(NOME_DA_PLANILHA)
        aba_ocorrencias = planilha.worksheet("Ocorrencias_Principais")
        aba_testes = planilha.worksheet("Testes_de_Ligacao")

        id_ocorrencia = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        data_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_inicial = "Registrado"
        linha_ocorrencia = [id_ocorrencia, data_registro,
                            occurrence_title, user_email, status_inicial]

        aba_ocorrencias.append_row(linha_ocorrencia)

        if tests_list:
            linhas_testes = []
            for teste in tests_list:
                linha_teste = [id_ocorrencia, teste["horario"], teste["num_a"],
                               teste["op_a"], teste["num_b"], teste["op_b"], teste["status"], teste["obs"]]
                linhas_testes.append(linha_teste)
            aba_testes.append_rows(linhas_testes)
    except WorksheetNotFound as e:
        raise WorksheetNotFound(
            f"Aba não encontrada. Verifique se 'Ocorrencias_Principais' e 'Testes_de_Ligacao' existem. Detalhe: {e}") from e


def get_all_occurrences(credentials):
    """
    Busca e retorna todos os registros da aba de ocorrências principais.
    """
    try:
        gc = authorize_gspread(credentials)
        planilha = gc.open(NOME_DA_PLANILHA)
        aba_ocorrencias = planilha.worksheet("Ocorrencias_Principais")
        return aba_ocorrencias.get_all_records()  # Retorna uma lista de dicionários
    except Exception as e:
        print(f"Erro ao buscar ocorrências: {e}")
        return []  # Retorna lista vazia em caso de erro
