import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Set up logging
log_file = f"build_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create logger instance
logger = logging.getLogger('BuildLogger')

# Log system information
logger.info("=== Build Process Started ===")
logger.info(f"Python Version: {sys.version}")
logger.info(f"Operating System: {os.name} - {sys.platform}")
logger.info(f"Current Working Directory: {os.getcwd()}")
logger.info(f"Log File: {os.path.abspath(log_file)}")

# Define directories
SPEC_DIR = Path(os.getcwd())
PROJECT_DIR = SPEC_DIR
DIST_DIR = PROJECT_DIR / 'dist'
FFMPEG_DIR = PROJECT_DIR / 'ffmpeg'

logger.info("=== Directory Configuration ===")
logger.info(f"SPEC_DIR: {SPEC_DIR}")
logger.info(f"PROJECT_DIR: {PROJECT_DIR}")
logger.info(f"DIST_DIR: {DIST_DIR}")
logger.info(f"FFMPEG_DIR: {FFMPEG_DIR}")

# FFmpeg files to include
ffmpeg_files = ['ffmpeg.exe']

# Determine Python, Tcl/Tk and DLL paths dynamically (works for Anaconda/Miniconda)
PY_BASE = Path(sys.base_prefix)  # Base of the current Python installation
# More reliable approach to locate Python DLL - check multiple potential locations
PYTHON_VERSION = f"{sys.version_info.major}{sys.version_info.minor}"
BASE_PYTHON_DLL = f"python{PYTHON_VERSION}.dll"

# Look in multiple potential locations for the Python DLL
POTENTIAL_DLL_LOCATIONS = [
    Path(sys.executable).parent / BASE_PYTHON_DLL,  # In the venv Scripts directory
    PY_BASE / BASE_PYTHON_DLL,                      # In base Python directory
    PY_BASE / "DLLs" / BASE_PYTHON_DLL,             # In base Python DLLs directory
    Path(os.environ["WINDIR"]) / "System32" / BASE_PYTHON_DLL,  # In System32
]

# Find the first existing DLL
PY_DLL_PATH = None
for location in POTENTIAL_DLL_LOCATIONS:
    if location.exists():
        PY_DLL_PATH = location
        break

if not PY_DLL_PATH:
    logger.error(f"Could not find Python DLL ({BASE_PYTHON_DLL}) in any of the expected locations")
    sys.exit(1)

TK_DLL_DIR = PY_BASE / 'Library' / 'bin'
TK_LIB_DIR = PY_BASE / 'Library' / 'lib'

logger.info(f"Detected Python base prefix: {PY_BASE}")
logger.info(f"Python DLL found at: {PY_DLL_PATH}")
logger.info(f"Expecting Tcl/Tk DLLs in: {TK_DLL_DIR}")
logger.info(f"Expecting Tcl/Tk libs in: {TK_LIB_DIR}")

def verify_ffmpeg_files():
    """Verify FFmpeg files exist"""
    logger.info("=== FFmpeg Files Verification ===")
    missing_files = []
    for file in ffmpeg_files:
        source = FFMPEG_DIR / file
        if not source.exists():
            missing_files.append(file)
            logger.error(f"Missing file: {file}")
        else:
            try:
                file_size = os.path.getsize(source)
                file_stats = os.stat(source)
                logger.info(f"Found {file}:")
                logger.info(f"  - Size: {file_size:,} bytes")
                logger.info(f"  - Created: {datetime.fromtimestamp(file_stats.st_ctime)}")
                logger.info(f"  - Modified: {datetime.fromtimestamp(file_stats.st_mtime)}")
                
                if file_size < 50_000_000:  # 50MB
                    logger.warning(f"WARNING: {file} is suspiciously small ({file_size:,} bytes)")
            except Exception as e:
                logger.error(f"Error checking {file}: {str(e)}")
                return False
    
    if missing_files:
        logger.error("Missing FFmpeg files:")
        for file in missing_files:
            logger.error(f"- {file}")
        logger.error(f"Please ensure FFmpeg files are in: {FFMPEG_DIR}")
        return False
    logger.info("All FFmpeg files verified successfully")
    return True

block_cipher = None

try:
    # Verify FFmpeg files before proceeding
    if not verify_ffmpeg_files():
        logger.error("FFmpeg verification failed")
        sys.exit(1)

    logger.info("=== Starting PyInstaller Configuration ===")

    # Handle the case where Python DLL might not be directly accessible
    binaries_list = []
    
    # Only add Python DLL if it exists and is accessible
    if PY_DLL_PATH and PY_DLL_PATH.exists():
        binaries_list.append((str(PY_DLL_PATH), '.'))
    
    # Add Tcl/Tk DLLs if they exist
    for dll_name in ['tk86t.dll', 'tcl86t.dll', 'liblzma.dll', 'libbz2.dll']:
        dll_path = TK_DLL_DIR / dll_name
        if dll_path.exists():
            binaries_list.append((str(dll_path), '.'))
        else:
            logger.warning(f"DLL not found: {dll_path}")
    
    a = Analysis(
        ['mkvtomp4.py'],
        pathex=[str(SPEC_DIR)],
        binaries=binaries_list,
        datas=[
            # Include FFmpeg executables
            (str(FFMPEG_DIR / 'ffmpeg.exe'), '.'),
            ('icon.ico', '.'),
            # Add Tcl/Tk libraries explicitly
            (str(TK_LIB_DIR / 'tcl8.6'), 'tcl8.6'),
            (str(TK_LIB_DIR / 'tk8.6'), 'tk8.6')
        ],
        hiddenimports=['tkinter', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.ttk'],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=['pygame'],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
        noarchive=False
    )

    pyz = PYZ(
        a.pure,
        a.zipped_data,
        cipher=block_cipher
    )

    # Correct configuration for onefile mode with PyInstaller
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='mkvtomp4',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,  # Set to False to avoid stripping symbols that might be needed
        upx=True,
        upx_exclude=[],
        runtime_tmpdir='${APPDATA}\\mkvtomp4',  # Specify a temp directory that's likely to exist
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(PROJECT_DIR / 'icon.ico'),
        onefile=True
    )

    # No need for COLLECT() when using onefile=True

    logger.info("=== Build Completed Successfully ===")

except Exception as e:
    logger.error(f"Build failed with error: {str(e)}", exc_info=True)
    sys.exit(1)

finally:
    logger.info(f"Build log saved to: {os.path.abspath(log_file)}")
    logger.info("=== Build Process Ended ===")