# ==============================================================================
# FICHEIRO: src/utils/date_utils.py
# DESCRIÇÃO: Funções utilitárias para manipulação segura de datas e timezones.
# DATA DA ATUALIZAÇÃO: 27/08/2025
# NOTAS: Nenhuma alteração de código foi necessária neste ficheiro para a
#        nova estrutura.
# ==============================================================================

import datetime
import pytz

def safe_fromisoformat(dt_str):
    """
    Converte uma string de data/hora no formato ISO 8601 para um objeto datetime.
    Trata casos onde a string pode não ter informações de timezone e garante
    compatibilidade com diferentes versões do Python.
    """
    if not dt_str:
        return None
    
    try:
        # Tenta converter diretamente
        dt_obj = datetime.datetime.fromisoformat(dt_str)
        # Se não tiver timezone, assume UTC
        if dt_obj.tzinfo is None:
            return dt_obj.replace(tzinfo=pytz.utc)
        return dt_obj
    except ValueError:
        # Fallback para formatos comuns sem timezone
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
