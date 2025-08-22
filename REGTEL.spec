# Ficheiro: regtel.spec

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Importar collect_all do PyInstaller
from PyInstaller.utils.hooks import collect_all

# Coletar todas as dependências (binários, dados, hiddenimports) para 'cryptography'
coll_all_cryptography = collect_all('cryptography')

# Coletar todas as dependências (binários, dados, hiddenimports) para 'pytz'
coll_all_pytz = collect_all('pytz')

# --- NOVO: Combinar todas as dependências ANTES de passar para Analysis ---
# Inicializa as listas combinadas com os resultados de collect_all
all_binaries = coll_all_cryptography[0] + coll_all_pytz[0]
all_datas = coll_all_cryptography[1] + coll_all_pytz[1]
all_hiddenimports = coll_all_cryptography[2] + coll_all_pytz[2]

# Adicionar os ficheiros de dados específicos do seu projeto
# Estes são os ficheiros que você já tinha na lista 'datas' original
project_datas = [
    ('client_secrets.json', '.'),
    ('service_account.json', '.'),
    ('icon.ico', '.')
]
all_datas += project_datas # Adiciona os dados do projeto à lista combinada de dados


a = Analysis(['main.py'],
             pathex=['.', 'src'],
             binaries=all_binaries, # Passa os binários combinados diretamente
             datas=all_datas,       # Passa os dados combinados diretamente
             hiddenimports=all_hiddenimports, # Passa os hiddenimports combinados diretamente
             hookspath=['./hooks'], # Garante que o PyInstaller procure hooks na sua pasta 'hooks'
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

# --- REMOVIDO: As linhas 'a.binaries += ...' e 'a.datas += ...' e 'a.hiddenimports += ...'
#               foram removidas daqui porque as listas já são combinadas antes da chamada Analysis.
#               Isso evita a inconsistência de formato que causava o erro.


pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='REGTEL',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='icon.ico' # <--- Linha adicionada para o ícone do executável
         )
