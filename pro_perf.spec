# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('ui/resources', 'ui/resources'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'pymodbus',
        'pymodbus.client',
        'mysql.connector',
        'mysql',
        'greenlet',
        'core.test_definitions.test_registry',
        'core.test_definitions.base_test',
        'core.test_definitions.g2_normal_operation',
        'core.test_definitions.g3_electrical_endurance',
        'core.test_definitions.g5_fault_current_making',
        'core.test_definitions.g6_short_circuit_current',
        'core.test_definitions.g7_minimum_switched_current',
        'core.test_definitions.manual_prospective_current',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Pro-Perf',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ui/resources/icons/app_icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Pro-Perf',
)
