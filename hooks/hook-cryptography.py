# ==============================================================================
# ARQUIVO: hooks/hook-cryptography.py
# DESCRIÇÃO: Hook para o PyInstaller garantir a inclusão da biblioteca 'cryptography'.
# ==============================================================================

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

binaries = collect_dynamic_libs('cryptography')
datas = collect_data_files('cryptography')
hiddenimports = ['cryptography.hazmat.backends.openssl.backend'