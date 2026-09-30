"""
MarkItDown Studio v0.2.0 — Pipeline de conversão universal.
Orquestra MarkItDown Core, RapidOCR, PyPDFium2 e MediaEngine (Vídeo & Áudio Speech-to-Text).
"""

import io
import re
import time
from pathlib import Path
from typing import Dict, Any, Tuple

from markitdown import MarkItDown

from . import config
from .ocr_engine import perform_ocr_on_image_bytes, get_ocr_engine
from .media_engine import process_media_to_markdown
from .diagnostics import diagnose_exception

# Importações opcionais
try:
    from PIL import Image
    HAS_PILLOW = True
except Exception:
    HAS_PILLOW = False

try:
    import pypdfium2 as pdfium
    HAS_PDFIUM = True
except Exception:
    HAS_PDFIUM = False

# Instância do conversor MarkItDown (singleton)
_converter = MarkItDown()


def sanitize_filename(name: str) -> str:
    """Corrige codificação de nomes de arquivo (UTF-8 / Latin-1) preservando acentuação pt-BR e limpando caracteres inválidos no Windows."""
    if not name:
        return "documento"
    try:
        # Se veio com dupla codificação UTF-8 via Latin-1
        name_fixed = name.encode('latin1').decode('utf-8')
        name = name_fixed
    except Exception:
        pass
        
    # Remove caracteres ilegais para o sistema de arquivos do Windows
    name_clean = re.sub(r'[\\/*?:"<>|]', '_', name)
    return name_clean.strip()


def sanitize_path(path_str: str) -> str:
    """Corrige codificação e normaliza caminhos de diretório."""
    if not path_str:
        return ""
    try:
        path_str = path_str.encode('latin1').decode('utf-8')
    except Exception:
        pass
    return path_str.strip()


def format_file_size(size_bytes: int) -> str:
    """Converte bytes para formato legível (B, KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_default_output_dir() -> str:
    """Retorna o diretório padrão de saída em Documentos/MarkItDown_Output."""
    docs = Path.home() / "Documents" / config.DEFAULT_OUTPUT_DIR_NAME
    try:
        docs.mkdir(parents=True, exist_ok=True)
        return str(docs.resolve())
    except Exception:
        fallback = Path.cwd() / "output"
        fallback.mkdir(parents=True, exist_ok=True)
        return str(fallback.resolve())


def convert_image_to_markdown(file_name: str, file_bytes: bytes) -> Tuple[str, str]:
    """Lê a imagem, extrai o texto completo via OCR e formata como Markdown com metadados."""
    src_stem = Path(file_name).stem
    ext = Path(file_name).suffix.lower()
    
    # 1. Executa OCR para extração real do conteúdo textual
    extracted_text_lines = perform_ocr_on_image_bytes(file_bytes)
    
    # 2. Extrai metadados visuais da imagem (Pillow)
    meta_info = {
        "dim": "N/D",
        "format": ext.replace('.', '').upper(),
        "mode": "RGB"
    }
    
    if HAS_PILLOW:
        try:
            im = Image.open(io.BytesIO(file_bytes))
            w, h = im.size
            meta_info["dim"] = f"{w} x {h} pixels"
            meta_info["format"] = im.format or ext.replace('.', '').upper()
            meta_info["mode"] = im.mode
        except Exception:
            pass

    # 3. Monta o Markdown estruturado
    md_parts = [f"# 🖼️ {src_stem}\n"]
    
    if extracted_text_lines:
        md_parts.append("## Conteúdo Textual Detectado (Extraído via OCR RapidOCR)\n")
        md_parts.append("\n\n".join(extracted_text_lines))
        md_parts.append("\n\n---\n")
    else:
        md_parts.append("> ℹ️ *Nenhum texto detectado nesta imagem.*\n\n---\n")

    md_parts.append("### Informações Técnicas da Imagem")
    md_parts.append(f"- **Formato:** `{meta_info['format']}`")
    md_parts.append(f"- **Dimensões:** `{meta_info['dim']}`")
    md_parts.append(f"- **Modo de Cor:** `{meta_info['mode']}`")
    md_parts.append(f"- **Tamanho do Arquivo:** `{format_file_size(len(file_bytes))}`")

    return "\n".join(md_parts), src_stem


def convert_pdf_robust(file_name: str, file_bytes: bytes) -> Tuple[str, str]:
    """Conversor de PDF multi-estágio inteligente:
    1. Tenta extrair texto com MarkItDown Core
    2. Fallback para PyPdfium2
    3. Se o PDF for digitalizado (sem texto digital), executa OCR página a página
    """
    src_stem = Path(file_name).stem
    
    # 1. Tenta MarkItDown nativo
    try:
        stream = io.BytesIO(file_bytes)
        res = _converter.convert_stream(stream, file_extension='.pdf')
        if res and res.text_content and len(res.text_content.strip()) > 30:
            return res.text_content.strip(), getattr(res, 'title', None) or src_stem
    except Exception:
        pass

    # 2. Tenta PyPdfium2 para texto e detecção de páginas escaneadas
    if HAS_PDFIUM:
        try:
            pdf = pdfium.PdfDocument(io.BytesIO(file_bytes))
            page_sections = []
            
            for i, page in enumerate(pdf):
                tp = page.get_textpage()
                txt = tp.get_text_range().strip()
                
                if txt and len(txt) > 20:
                    page_sections.append(f"## Página {i + 1}\n\n{txt}")
                else:
                    engine = get_ocr_engine()
                    if engine is not None:
                        try:
                            page_img = page.render(scale=2.0).to_pil()
                            buf = io.BytesIO()
                            page_img.save(buf, format='JPEG')
                            ocr_lines = perform_ocr_on_image_bytes(buf.getvalue())
                            if ocr_lines:
                                page_sections.append(f"## Página {i + 1} *(OCR)*\n\n" + "\n\n".join(ocr_lines))
                            else:
                                w, h = round(page.get_width()), round(page.get_height())
                                page_sections.append(f"## Página {i + 1}\n\n*(Página digitalizada sem texto detectável - {w} x {h} pt)*")
                        except Exception:
                            page_sections.append(f"## Página {i + 1}\n\n*(Página digitalizada)*")
                    else:
                        w, h = round(page.get_width()), round(page.get_height())
                        page_sections.append(f"## Página {i + 1}\n\n*(Página digitalizada - {w} x {h} pt)*")
            
            if page_sections:
                header = f"# 📄 {src_stem}\n\n| Propriedade | Detalhe |\n|---|---|\n| **Total de Páginas** | {len(pdf)} páginas |\n| **Modo de Extração** | Texto Vetorial & OCR Inteligente |\n\n---\n\n"
                return header + "\n\n---\n\n".join(page_sections), src_stem
        except Exception as ex_pdfium:
            print(f"[Aviso] Pdfium falhou para {file_name}: {ex_pdfium}")

    # 3. Fallback via arquivo temporário
    temp_dir = Path(get_default_output_dir())
    temp_file = temp_dir / f"_temp_pdf_{int(time.time()*1000)}.pdf"
    try:
        temp_file.write_bytes(file_bytes)
        res = _converter.convert(str(temp_file))
        if res and res.text_content:
            return res.text_content.strip(), getattr(res, 'title', None) or src_stem
    finally:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass

    return f"# 📄 {src_stem}\n\n*(Documento PDF processado)*", src_stem


def process_conversion(file_name: str, file_bytes: bytes = None, file_path: str = None, output_dir: str = None, overwrite: bool = True) -> Dict[str, Any]:
    """Função central de conversão universal com suporte completo a Documentos, Imagens, Vídeos e Áudios."""
    start_time = time.time()
    
    file_name = sanitize_filename(file_name)
    output_dir = sanitize_path(output_dir)
    
    try:
        if not output_dir:
            dest_dir = Path(get_default_output_dir())
        else:
            dest_dir = Path(output_dir).resolve()
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        src_stem = Path(file_name).stem
        ext = Path(file_name).suffix.lower()
        markdown_text = ""
        title = src_stem
        
        # 1. Mídias Audiovisuais (Vídeo e Áudio com Transcrição e Timestamps)
        if ext in config.MEDIA_EXTENSIONS:
            markdown_text, title = process_media_to_markdown(
                file_name=file_name,
                file_bytes=file_bytes,
                file_path=file_path,
                temp_dir=dest_dir
            )

        # 2. Imagens com OCR
        elif ext in config.IMAGE_EXTENSIONS:
            if file_bytes is None and file_path and Path(file_path).exists():
                file_bytes = Path(file_path).read_bytes()
            markdown_text, title = convert_image_to_markdown(file_name, file_bytes)
        
        # 3. Documentos PDF (com OCR em páginas escaneadas)
        elif ext == '.pdf':
            if file_bytes is None and file_path and Path(file_path).exists():
                file_bytes = Path(file_path).read_bytes()
            markdown_text, title = convert_pdf_robust(file_name, file_bytes)

        # 4. Arquivos de texto puro e formatos estruturados leves
        elif ext in {'.txt', '.json', '.xml', '.yaml', '.yml', '.csv', '.tsv', '.log', '.md'}:
            if file_bytes is None and file_path and Path(file_path).exists():
                file_bytes = Path(file_path).read_bytes()
            
            # Tenta decodificações comuns com segurança
            decoded_text = None
            for enc in ('utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1'):
                try:
                    decoded_text = file_bytes.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            
            if decoded_text is not None:
                if ext in {'.json', '.xml', '.yaml', '.yml'}:
                    lang = ext.replace('.', '')
                    markdown_text = f"# {src_stem}\n\n```{lang}\n{decoded_text}\n```"
                else:
                    markdown_text = f"# {src_stem}\n\n{decoded_text}"
                title = src_stem
            else:
                stream = io.BytesIO(file_bytes)
                result = _converter.convert_stream(stream, file_extension=ext)
                markdown_text = result.text_content or ""
                title = getattr(result, 'title', None) or src_stem
            
        # 5. Documentos gerais (Word, Excel, PowerPoint, HTML, EPUB, ZIP)
        else:
            if file_bytes is None and file_path and Path(file_path).exists():
                file_bytes = Path(file_path).read_bytes()
            try:
                stream = io.BytesIO(file_bytes)
                result = _converter.convert_stream(stream, file_extension=ext)
                markdown_text = result.text_content or ""
                title = getattr(result, 'title', None) or src_stem
            except Exception:
                temp_file = dest_dir / f"_temp_{int(time.time()*1000)}_{file_name}"
                try:
                    temp_file.write_bytes(file_bytes)
                    result = _converter.convert(str(temp_file))
                    markdown_text = result.text_content or ""
                    title = getattr(result, 'title', None) or src_stem
                finally:
                    if temp_file.exists():
                        try:
                            temp_file.unlink()
                        except Exception:
                            pass

        if not markdown_text or not markdown_text.strip():
            markdown_text = f"# {src_stem}\n\n*(Documento processado com sucesso)*"

        out_name = f"{src_stem}.md"
        out_path = dest_dir / out_name
        
        if not overwrite and out_path.exists():
            counter = 1
            while out_path.exists():
                out_path = dest_dir / f"{src_stem}_{counter}.md"
                counter += 1
        
        out_path.write_text(markdown_text, encoding="utf-8")
        elapsed = time.time() - start_time
        
        return {
            "success": True,
            "fileName": file_name,
            "outputPath": str(out_path.resolve()),
            "outputName": out_path.name,
            "title": title,
            "markdown": markdown_text,
            "charCount": len(markdown_text),
            "wordCount": len(markdown_text.split()),
            "lineCount": len(markdown_text.splitlines()),
            "duration": round(elapsed, 2),
            "outputSize": format_file_size(out_path.stat().st_size),
        }
    
    except Exception as exc:
        elapsed = time.time() - start_time
        diag = diagnose_exception(exc, file_name, file_bytes)
        print(f"[Erro de Conversão] {file_name}: {diag['rawError']}")
        return {
            "success": False,
            "fileName": file_name,
            "error": diag["rawError"],
            "diagnostic": diag,
            "duration": round(elapsed, 2),
        }
