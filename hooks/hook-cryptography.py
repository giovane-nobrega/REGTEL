# ==============================================================================
# FICHEIRO: hooks/hook-cryptography.py
# DESCRIÇÃO: Hook personalizado para PyInstaller para garantir a inclusão
#            correta da biblioteca 'cryptography' e suas dependências.
# ==============================================================================

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# Coleta todas as bibliotecas dinâmicas (DLLs/SOs) associadas à cryptography
# Isso é crucial para os componentes de baixo nível da biblioteca
binaries = collect_dynamic_libs('cryptography')

# Coleta quaisquer ficheiros de dados adicionais que a cryptography possa precisar
datas = collect_data_files('cryptography')

# Adiciona o backend OpenSSL explicitamente para garantir que seja incluído
# Isso resolve o erro 'No module named cryptography.hazmat.backends.openssl'
hiddenimports = ['cryptography.hazmat.backends.openssl.backend']
