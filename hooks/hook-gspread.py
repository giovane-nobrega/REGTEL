# ==============================================================================
# ARQUIVO: hooks/hook-gspread.py
# DESCRIÇÃO: Hook para o PyInstaller garantir a inclusão da biblioteca 'gspread'.
# ==============================================================================

from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('gspread')
