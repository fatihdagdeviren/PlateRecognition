# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['CamTest.py'],
             pathex=['D:\\OutSource\\PlateRecognition'],
             binaries=[],
             datas=[('C:\\Users\\fatih.dagdeviren\\AppData\\Local\\Continuum\\anaconda3\\pkgs\\libopencv-4.5.0-py36_2\\Library\\bin\\opencv_videoio_ffmpeg450_64.dll', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='CamTest',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
