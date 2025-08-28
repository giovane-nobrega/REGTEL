# ==============================================================================
# ARQUIVO: hooks/hook-cryptography.py
# DESCRIÇÃO: Hook para o PyInstaller garantir a inclusão da biblioteca 'cryptography'.
# ==============================================================================

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# Coleta as bibliotecas dinâmicas (DLLs/SOs) da cryptography
binaries = collect_dynamic_libs('cryptography')

# Coleta quaisquer arquivos de dados adicionais que a cryptography possa precisar
datas = collect_data_files('cryptography')

# Adiciona o backend OpenSSL explicitamente para resolver o erro 'No module named cryptography.hazmat.backends.openssl'
hiddenimports = ['cryptography.hazmat.backends.openssl.backend']