"""
MarkItDown Studio v0.2.0 — Motor OCR com carregamento sob demanda e pré-aquecimento.
Suporte a RapidOCR (ONNX Runtime) para extração de texto de imagens e PDFs digitalizados.
"""

import io
import threading
from pathlib import Path

# Estado global do motor OCR
_ocr_engine = None
_ocr_lock = threading.Lock()
_ocr_ready = threading.Event()
_ocr_status = "idle"  # idle | loading | ready | unavailable


def get_ocr_engine():
    """Retorna o motor OCR, inicializando sob demanda se necessário."""
    global _ocr_engine, _ocr_status
    
    if _ocr_status == "ready":
        return _ocr_engine
    
    if _ocr_status == "unavailable":
        return None
    
    # Se está carregando em background, aguarda (max 60s)
    if _ocr_status == "loading":
        _ocr_ready.wait(timeout=60)
        return _ocr_engine if _ocr_status == "ready" else None
    
    # Carrega sincronamente se não iniciou ainda
    _load_ocr_sync()
    return _ocr_engine if _ocr_status == "ready" else None


def _load_ocr_sync():
    """Carrega o motor OCR de forma síncrona."""
    global _ocr_engine, _ocr_status
    
    with _ocr_lock:
        if _ocr_status in ("ready", "unavailable"):
            return
        
        _ocr_status = "loading"
        try:
            from rapidocr_onnxruntime import RapidOCR
            _ocr_engine = RapidOCR()
            _ocr_status = "ready"
            print("[OCR] Motor RapidOCR carregado com sucesso.")
        except Exception as e:
            _ocr_engine = None
            _ocr_status = "unavailable"
            print(f"[OCR] RapidOCR não disponível: {e}")
        finally:
            _ocr_ready.set()


def preload_ocr_async():
    """Inicia o carregamento do OCR em uma thread de background.
    Chamado no startup do app para que o OCR já esteja pronto quando o usuário precisar."""
    global _ocr_status
    
    if _ocr_status != "idle":
        return
    
    _ocr_status = "loading"
    thread = threading.Thread(target=_load_ocr_sync, name="OCR-Preloader", daemon=True)
    thread.start()
    print("[OCR] Pré-carregamento do motor OCR iniciado em background...")


def get_ocr_status():
    """Retorna o status atual do motor OCR."""
    return _ocr_status


def perform_ocr_on_image_bytes(image_bytes):
    """Executa OCR nos bytes de uma imagem e retorna as linhas de texto encontradas."""
    engine = get_ocr_engine()
    if engine is None:
        return []
    
    try:
        result, _ = engine(image_bytes)
        if result:
            lines = []
            for item in result:
                txt = item[1].strip()
                if txt:
                    lines.append(txt)
            return lines
    except Exception as e:
        print(f"[OCR Error] {e}")
    
    return []
