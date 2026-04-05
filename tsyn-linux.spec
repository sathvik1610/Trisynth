# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=['src.frontend.lexer', 'src.frontend.parser', 'src.semantic.analyzer', 'src.ir.ir_gen', 'src.optimization.optimizer', 'src.optimization.constant_fold', 'src.optimization.dead_code', 'src.optimization.strength_reduction', 'src.optimization.cse', 'src.optimization.copy_propagation', 'src.backend.codegen_x86', 'src.backend.codegen_riscv'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='tsyn-linux',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
