# ==============================================================================
# ARQUIVO: hooks/hook-gspread.py
# DESCRIÇÃO: Hook para o PyInstaller garantir a inclusão da biblioteca 'gspread'.
# ==============================================================================

from PyInstaller.utils.hooks import copy_metadata

# Copia os metadados da biblioteca gspread, que são necessários para o seu funcionamento
datas = copy_metadata('gspread')