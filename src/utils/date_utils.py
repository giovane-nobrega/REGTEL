# ==============================================================================
# ARQUIVO: src/utils/date_utils.py
# DESCRIÇÃO: Funções utilitárias para manipulação segura de datas e fusos horários.
# ==============================================================================

import datetime
import pytz # Necessário para lidar com fusos horários, especialmente em versões mais antigas do Python

def safe_fromisoformat(dt_str):
    """
    Converte uma string de data/hora no formato ISO 8601 para um objeto datetime.
    Trata casos onde a string pode não ter informações de fuso horário e garante
    compatibilidade com diferentes versões do Python.
    """
    if not dt_str:
        return None
    
    try:
        # Tenta converter diretamente (funciona bem com Python 3.11+ e strings completas)
        dt_obj = datetime.datetime.fromisoformat(dt_str)
        # Se não tiver fuso horário, assume UTC ou adiciona um fuso horário padrão
        if dt_obj.tzinfo is None:
            return dt_obj.replace(tzinfo=pytz.utc)
        return dt_obj
    except ValueError:
        # Fallback para strings que podem não ser totalmente compatíveis com fromisoformat
        # ou para versões mais antigas do Python que não suportam fusos horários nativamente.
        # Tenta um formato comum sem fuso horário e adiciona UTC.
        try:
            dt_obj = datetime.datetime.strptime(dt_str.split('+')[0].split('Z')[0], "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            try:
                dt_obj = datetime.datetime.strptime(dt_str.split('+')[0].split('Z')[0], "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                return None
        return dt_obj.replace(tzinfo=pytz.utc)
    except Exception as e:
        print(f"Erro inesperado em safe_fromisoformat: {e}")
        return None
