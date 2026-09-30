"""
MarkItDown Studio v0.2.0 — Configurações centralizadas.
Todas as constantes, extensões suportadas, parâmetros do motor de vídeo/áudio e configurações do sistema ficam aqui.
"""

import os
import sys
import shutil
from pathlib import Path

# Versão da Aplicação
VERSION = "0.2.0"

# Diretório raiz do projeto
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# Diretório do frontend web
WEB_DIR = Path(__file__).parent / "web"

# Limite máximo de upload (1 GB)
MAX_UPLOAD_SIZE = 1024 * 1024 * 1024

# Extensões suportadas agrupadas por categoria
EXTENSIONS = {
    "document": {".pdf", ".docx", ".doc", ".txt", ".epub", ".msg", ".rtf", ".odt"},
    "spreadsheet": {".xlsx", ".xls", ".csv", ".tsv", ".ods"},
    "presentation": {".pptx", ".ppt", ".odp"},
    "web": {".html", ".htm", ".xhtml", ".xml", ".rss", ".atom", ".json", ".yaml", ".yml"},
    "image": {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".svg"},
    "audio": {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".wma", ".opus", ".aiff", ".alac", ".amr"},
    "video": {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v", ".3gp", ".ts", ".mts", ".ogv", ".vob"},
    "archive": {".zip"},
}

# Set unificado de todas as extensões
SUPPORTED_EXTENSIONS = set()
for exts in EXTENSIONS.values():
    SUPPORTED_EXTENSIONS.update(exts)

# Sets específicos para rotas especializadas
IMAGE_EXTENSIONS = EXTENSIONS["image"]
AUDIO_EXTENSIONS = EXTENSIONS["audio"]
VIDEO_EXTENSIONS = EXTENSIONS["video"]
MEDIA_EXTENSIONS = AUDIO_EXTENSIONS.union(VIDEO_EXTENSIONS)

# Configurações do Motor Speech-to-Text / Whisper (Alta Precisão)
# large-v3 oferece a mais alta precisão para transcrição em Português do Brasil
WHISPER_MODEL = os.environ.get("MARKITDOWN_WHISPER_MODEL", "large-v3")  # large-v3 / medium / small / base
WHISPER_FALLBACK_MODELS = ["large-v3", "medium", "small", "base"]
WHISPER_LANGUAGE = os.environ.get("MARKITDOWN_WHISPER_LANG", "pt")     # pt / pt-BR / auto
WHISPER_BEAM_SIZE = int(os.environ.get("MARKITDOWN_WHISPER_BEAM", "5"))
WHISPER_VAD_FILTER = True
WHISPER_COMPUTE_TYPE = os.environ.get("MARKITDOWN_COMPUTE_TYPE", "auto") # auto / float16 / int8
GOOGLE_SPEECH_LANGUAGE = "pt-BR"
GEMINI_MODEL = os.environ.get("MARKITDOWN_GEMINI_MODEL", "gemini-2.0-flash")

# Duração máxima de chunk para transcrição particionada (segundos)
AUDIO_CHUNK_DURATION_SEC = 25

# Porta padrão do servidor
DEFAULT_PORT = 8080
PORT_RANGE = 50

# Timeout OCR por página (segundos)
OCR_PAGE_TIMEOUT = 30

# Nome do diretório padrão de saída
DEFAULT_OUTPUT_DIR_NAME = "MarkItDown_Output"

# Python executável
PYTHON_EXE = sys.executable

# Tamanho e posicionamento da janela Eel
WINDOW_SIZE = (1300, 900)
WINDOW_POSITION = (60, 30)

# Modos de navegador
BROWSER_MODES = ["edge", "chrome", "default"]


def get_system_info():
    """Retorna informações completas do sistema e motores disponíveis para exibição na UI."""
    import platform
    info = {
        "python_version": platform.python_version(),
        "os": f"{platform.system()} {platform.release()}",
        "arch": platform.machine(),
        "studio_version": VERSION,
        "ffmpeg_available": shutil.which("ffmpeg") is not None,
    }
    
    # Detecção do Motor OCR
    try:
        import rapidocr_onnxruntime
        info["ocr_engine"] = "RapidOCR (ONNX Runtime)"
    except ImportError:
        info["ocr_engine"] = "Pillow Metadata Fallback"
        
    # Detecção do Motor Speech-to-Text
    try:
        import faster_whisper
        info["speech_engine"] = f"Faster-Whisper ({WHISPER_MODEL.upper()} - Alta Precisão)"
    except ImportError:
        try:
            import whisper
            info["speech_engine"] = f"OpenAI Whisper ({WHISPER_MODEL.upper()})"
        except ImportError:
            try:
                import speech_recognition
                info["speech_engine"] = "Google Speech API (pt-BR)"
            except ImportError:
                info["speech_engine"] = "Extração de Metadados Básicos"
                
    # Detecção do Google GenAI / Gemini Ecosystem
    has_gemini_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    try:
        import google.genai
        info["google_genai"] = f"Disponível (Gemini Multimodal{' - Chave Ativa' if has_gemini_key else ' - Sem Chave'})"
    except ImportError:
        try:
            import google.generativeai
            info["google_genai"] = f"Disponível (GenerativeAI{' - Chave Ativa' if has_gemini_key else ' - Sem Chave'})"
        except ImportError:
            info["google_genai"] = "Não Instalado"
        
    # Detecção OpenCV
    try:
        import cv2
        info["opencv"] = f"v{cv2.__version__}"
    except ImportError:
        info["opencv"] = "Não Instalado"

    return info
