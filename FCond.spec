# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['/Users/kylelafollette/anl-exploration-fear-project/CONDMain/main.py'],
             pathex=['/Users/kylelafollette/anl-exploration-fear-project'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['_tkinter', 'Tkinter', 'enchant', 'twisted'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='FCond',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe, Tree('/Users/kylelafollette/anl-exploration-fear-project/CONDMain/'),
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='FCond')
app = BUNDLE(coll,
             name='FCond.app',
             icon='/Users/kylelafollette/anl-exploration-fear-project/CONDMain/stress_icon_blue_7Ri_icon.ico',
             bundle_identifier=None)
