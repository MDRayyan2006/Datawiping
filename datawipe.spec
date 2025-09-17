# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Get the current directory
current_dir = Path.cwd()

# Define the main script
main_script = 'main.py'

# Define data files to include
datas = [
    # Include the entire project structure
    ('models', 'models'),
    ('routers', 'routers'),
    ('services', 'services'),
    ('utils', 'utils'),
    ('flutter_app', 'flutter_app'),
    
    # Include configuration files
    ('requirements.txt', '.'),
    ('README.md', '.'),
    ('init_db.py', '.'),
    ('database.py', '.'),
    
    # Include test files (optional - remove if not needed in production)
    ('test_*.py', '.'),
    ('demo_*.py', '.'),
    ('check_*.py', '.'),
    ('start_*.py', '.'),
]

# Define hidden imports (modules that PyInstaller might miss)
hiddenimports = [
    # FastAPI and related
    'fastapi',
    'fastapi.middleware.cors',
    'fastapi.routing',
    'fastapi.applications',
    'fastapi.dependencies',
    'fastapi.responses',
    'fastapi.requests',
    'fastapi.exceptions',
    'fastapi.status',
    'fastapi.background',
    'fastapi.security',
    
    # Uvicorn and ASGI
    'uvicorn',
    'uvicorn.main',
    'uvicorn.config',
    'uvicorn.server',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.websockets',
    'uvicorn.lifespan',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.workers',
    
    # SQLAlchemy
    'sqlalchemy',
    'sqlalchemy.orm',
    'sqlalchemy.engine',
    'sqlalchemy.pool',
    'sqlalchemy.dialects',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.sql',
    'sqlalchemy.sql.functions',
    
    # Pydantic
    'pydantic',
    'pydantic.main',
    'pydantic.fields',
    'pydantic.validators',
    'pydantic.types',
    'pydantic.networks',
    'pydantic.datetime_parse',
    'pydantic.json',
    'pydantic.color',
    'pydantic.types',
    
    # Cryptography
    'cryptography',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.primitives.asymmetric',
    'cryptography.hazmat.primitives.asymmetric.rsa',
    'cryptography.hazmat.primitives.asymmetric.padding',
    'cryptography.hazmat.primitives.hashes',
    'cryptography.hazmat.primitives.serialization',
    'cryptography.hazmat.backends',
    'cryptography.hazmat.backends.openssl',
    'cryptography.x509',
    'cryptography.x509.oid',
    
    # ReportLab
    'reportlab',
    'reportlab.lib',
    'reportlab.lib.pagesizes',
    'reportlab.lib.styles',
    'reportlab.lib.units',
    'reportlab.lib.colors',
    'reportlab.platypus',
    'reportlab.platypus.flowables',
    'reportlab.platypus.paragraph',
    'reportlab.platypus.tables',
    'reportlab.platypus.doctemplate',
    'reportlab.graphics',
    'reportlab.graphics.shapes',
    'reportlab.graphics.charts',
    
    # System and platform specific
    'psutil',
    'psutil._psutil_windows' if sys.platform == 'win32' else 'psutil._psutil_linux',
    'psutil._psutil_posix',
    
    # Standard library modules that might be missed
    'asyncio',
    'asyncio.events',
    'asyncio.base_events',
    'asyncio.coroutines',
    'asyncio.futures',
    'asyncio.tasks',
    'asyncio.subprocess',
    'asyncio.streams',
    'asyncio.protocols',
    'asyncio.transports',
    'asyncio.queues',
    'asyncio.locks',
    'asyncio.threads',
    'asyncio.runners',
    
    # HTTP and networking
    'httptools',
    'httptools.parser',
    'httptools.parser.parser',
    'httptools.parser.errors',
    
    # JSON and data handling
    'orjson',
    'ujson',
    'msgpack',
    
    # File handling
    'aiofiles',
    'aiofiles.os',
    'aiofiles.threadpool',
    
    # Database
    'aiosqlite',
    'sqlite3',
    
    # Logging
    'logging',
    'logging.handlers',
    'logging.config',
    
    # Path and file operations
    'pathlib',
    'shutil',
    'tempfile',
    'zipfile',
    'tarfile',
    'gzip',
    'bz2',
    'lzma',
    
    # System operations
    'subprocess',
    'platform',
    'ctypes',
    'ctypes.wintypes' if sys.platform == 'win32' else None,
    
    # Threading and multiprocessing
    'threading',
    'multiprocessing',
    'concurrent',
    'concurrent.futures',
    'concurrent.futures.thread',
    'concurrent.futures.process',
    
    # Time and date
    'datetime',
    'time',
    'calendar',
    
    # Math and random
    'math',
    'random',
    'hashlib',
    'hmac',
    'secrets',
    
    # Regular expressions
    're',
    
    # Collections
    'collections',
    'collections.abc',
    'itertools',
    'functools',
    'operator',
    
    # String and text
    'string',
    'textwrap',
    'unicodedata',
    
    # Enum
    'enum',
    
    # Dataclasses
    'dataclasses',
    
    # Typing
    'typing',
    'typing_extensions',
    
    # Context managers
    'contextlib',
    
    # Weak references
    'weakref',
    
    # Copy
    'copy',
    'pickle',
    'json',
    'csv',
    'xml',
    'xml.etree',
    'xml.etree.ElementTree',
    
    # Compression
    'zlib',
    'gzip',
    'bz2',
    'lzma',
    
    # Base64 encoding
    'base64',
    'binascii',
    'quopri',
    'uu',
    
    # URL handling
    'urllib',
    'urllib.parse',
    'urllib.request',
    'urllib.response',
    'urllib.error',
    
    # Email
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',
    'email.mime.base',
    
    # HTML
    'html',
    'html.parser',
    'html.entities',
    
    # HTTP
    'http',
    'http.server',
    'http.client',
    'http.cookies',
    'http.cookiejar',
    
    # Socket
    'socket',
    'ssl',
    'ssl',
    
    # Windows specific (if on Windows)
    'winreg' if sys.platform == 'win32' else None,
    'msvcrt' if sys.platform == 'win32' else None,
    'winsound' if sys.platform == 'win32' else None,
    
    # Unix specific (if on Unix)
    'fcntl' if sys.platform != 'win32' else None,
    'termios' if sys.platform != 'win32' else None,
    'tty' if sys.platform != 'win32' else None,
    'pty' if sys.platform != 'win32' else None,
    'select' if sys.platform != 'win32' else None,
    'signal' if sys.platform != 'win32' else None,
    'resource' if sys.platform != 'win32' else None,
    'pwd' if sys.platform != 'win32' else None,
    'grp' if sys.platform != 'win32' else None,
    'crypt' if sys.platform != 'win32' else None,
    'spwd' if sys.platform != 'win32' else None,
    'nis' if sys.platform != 'win32' else None,
    'syslog' if sys.platform != 'win32' else None,
    'syslog' if sys.platform != 'win32' else None,
]

# Remove None values from hiddenimports
hiddenimports = [imp for imp in hiddenimports if imp is not None]

# Define binaries (external executables)
binaries = []

# Platform-specific binaries
if sys.platform == 'win32':
    # Windows specific binaries
    binaries.extend([
        # Add any Windows-specific DLLs or executables here
    ])
elif sys.platform == 'linux':
    # Linux specific binaries
    binaries.extend([
        # Add any Linux-specific libraries or executables here
    ])
elif sys.platform == 'darwin':
    # macOS specific binaries
    binaries.extend([
        # Add any macOS-specific libraries or executables here
    ])

# Analysis configuration
a = Analysis(
    [main_script],
    pathex=[str(current_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude modules that are not needed
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'Pillow',
        'cv2',
        'tensorflow',
        'torch',
        'sklearn',
        'jupyter',
        'notebook',
        'ipython',
        'IPython',
        'pytest',
        'pytest_*',
        'test_*',
        'tests',
        'testing',
        'unittest',
        'doctest',
        'pdb',
        'pydoc',
        'profile',
        'pstats',
        'cProfile',
        'hotshot',
        'trace',
        'timeit',
        'cgitb',
        'pdb',
        'bdb',
        'cmd',
        'code',
        'codeop',
        'py_compile',
        'compileall',
        'dis',
        'pickletools',
        'tabnanny',
        'pyclbr',
        'ast',
        'symtable',
        'keyword',
        'token',
        'tokenize',
        'symbol',
        'parser',
        'py_compile',
        'compileall',
        'dis',
        'pickletools',
        'tabnanny',
        'pyclbr',
        'ast',
        'symtable',
        'keyword',
        'token',
        'tokenize',
        'symbol',
        'parser',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
a.datas = list(set(a.datas))
a.binaries = list(set(a.binaries))

# PYZ configuration
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# EXE configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DataWipe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False for GUI mode
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
    version=None,  # Add version info here if needed
)

# Optional: Create a directory distribution instead of a single file
# Uncomment the following lines if you want a directory distribution
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='DataWipe'
# )
