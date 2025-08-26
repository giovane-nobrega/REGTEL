# ==============================================================================
# ARQUIVO: src/utils/date_utils.py
# DESCRIÇÃO: Funções utilitárias para manipulação segura de datas.
# ==============================================================================

import datetime
import pytz

def safe_fromisoformat(dt_str):
    """
    Converte uma string de data/hora no formato ISO 8601 para um objeto datetime
    de forma segura, lidando com diferentes formatos e fusos horários.
    """
    if not dt_str:
        return None
    
    try:
        # Tenta o formato completo com fuso horário
        dt_obj = datetime.datetime.fromisoformat(dt_str)
        # Garante que o objeto de data tenha informação de fuso horário
        if dt_obj.tzinfo is None:
            return dt_obj.replace(tzinfo=pytz.utc)
        return dt_obj
    except ValueError:
        # Tenta formatos alternativos sem fuso horário
        try:
            # Tenta com milissegundos
            dt_obj = datetime.datetime.strptime(dt_str.split('+')[0].split('Z')[0], "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            try:
                # Tenta sem milissegundos
                dt_obj = datetime.datetime.strptime(dt_str.split('+')[0].split('Z')[0], "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                return None
        # Adiciona o fuso horário UTC ao objeto de data
        return dt_obj.replace(tzinfo=pytz.utc)
    except Exception as e:
        print(f"Erro inesperado em safe_fromisoformat: {e}")
        return None
