# Módulo: sheets_service.py
# Este é um arquivo de simulação para permitir que o app.py funcione sem uma
# implementação completa do Google Sheets. Ele contém as funções esperadas
# com uma lógica de placeholder.

from datetime import datetime


def save_occurrence_with_tests(credentials, user_email, titulo_ocorrencia, testes_adicionados):
    """
    Simula o salvamento de uma ocorrência e seus testes. Em uma implementação
    real, esta função se conectaria ao Google Sheets e adicionaria novas linhas.
    """
    print("\n" + "="*40)
    print("  [sheets_service] SIMULAÇÃO DE ENVIO PARA PLANILHA")
    print("="*40)
    print(f"-> Autenticação fornecida: {'Sim' if credentials else 'Não'}")
    print(f"-> E-mail do Registrador: {user_email}")
    print(f"-> Título da Ocorrência: {titulo_ocorrencia}")
    print(f"-> Total de Testes: {len(testes_adicionados)}")

    for i, teste in enumerate(testes_adicionados, 1):
        print(f"\n  --- Teste {i} ---")
        print(f"  Horário: {teste.get('horario', 'N/A')}")
        print(f"  De: {teste.get('num_a', 'N/A')} ({teste.get('op_a', 'N/A')})")
        print(
            f"  Para: {teste.get('num_b', 'N/A')} ({teste.get('op_b', 'N/A')})")
        print(f"  Status: {teste.get('status', 'N/A')}")
        print(f"  Obs: {teste.get('obs', 'Nenhuma')}")

    print("\n" + "="*40)
    print("  (Simulação) Dados recebidos com sucesso!")
    print("="*40 + "\n")

    # Em uma implementação real, você usaria a biblioteca gspread aqui.
    # Ex:
    # import gspread
    # gc = gspread.authorize(credentials)
    # sh = gc.open_by_key("SUA_CHAVE_DE_PLANILHA").worksheet("NomeDaAba")
    # for teste in testes_adicionados:
    #     linha = [
    #         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #         user_email,
    #         titulo_ocorrencia,
    #         # ... outros dados do teste
    #     ]
    #     sh.append_row(linha)

    # A função não precisa retornar nada se tudo ocorrer bem.
    # Em caso de erro, poderia levantar uma exceção.


def get_all_occurrences(credentials):
    """
    Simula a busca por todas as ocorrências na planilha. Retorna uma lista
    de dicionários com dados de exemplo para que a tela de histórico funcione.
    """
    print("\n" + "="*40)
    print("  [sheets_service] SIMULAÇÃO DE BUSCA DE HISTÓRICO")
    print("="*40)
    print(f"-> Autenticação fornecida: {'Sim' if credentials else 'Não'}")

    # Em uma implementação real, você buscaria os dados da planilha.
    # Ex:
    # import gspread
    # gc = gspread.authorize(credentials)
    # sh = gc.open_by_key("SUA_CHAVE_DE_PLANILHA").worksheet("NomeDaAba")
    # return sh.get_all_records()

    # Retornando dados de exemplo para popular a UI:
    dados_exemplo = [
        {
            'Data de Registro': '2025-07-01 11:30:00',
            'Título da Ocorrência': 'Falha em chamadas para a Claro (Exemplo)',
            'Email do Registrador': 'usuario.exemplo@gmail.com',
            'Status': 'Em Análise'
        },
        {
            'Data de Registro': '2025-06-30 15:00:12',
            'Título da Ocorrência': 'Chiado em ligações para Vivo (Exemplo)',
            'Email do Registrador': 'outro.usuario@gmail.com',
            'Status': 'Resolvido'
        },
        {
            'Data de Registro': '2025-06-29 09:05:45',
            'Título da Ocorrência': 'Chamadas mudas para TIM (Exemplo)',
            'Email do Registrador': 'usuario.exemplo@gmail.com',
            'Status': 'Resolvido'
        }
    ]

    print(
        f"-> (Simulação) Retornando {len(dados_exemplo)} registros de exemplo.")
    print("="*40 + "\n")

    return dados_exemplo
