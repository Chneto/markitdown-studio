"""
MarkItDown Studio v0.2.0 - Servidor Principal & Interface Eel Desktop
"""

import os
import sys
import json
import base64
import socket
import subprocess
from pathlib import Path

import eel
import bottle

# Importações locais do módulo studio
from . import config
from . import dialog_service
from .converter import process_conversion, sanitize_path, get_default_output_dir
from .diagnostics import diagnose_exception
from .ocr_engine import preload_ocr_async

# Configuração do Bottle para aceitar uploads de até 1GB
bottle.BaseRequest.MEMFILE_MAX = config.MAX_UPLOAD_SIZE
eel.btl.BaseRequest.MEMFILE_MAX = config.MAX_UPLOAD_SIZE


def get_free_port(start_port=config.DEFAULT_PORT):
    """Encontra uma porta TCP livre a partir da porta padrão para evitar conflitos."""
    for port in range(start_port, start_port + config.PORT_RANGE):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return start_port


# ==========================================================================
# ROTAS HTTP REST (BOTTLE)
# ==========================================================================

@eel.btl.route('/api/system_info', method=['GET'])
def api_system_info():
    """Retorna informações do sistema e motores disponíveis para exibição na interface."""
    eel.btl.response.content_type = 'application/json; charset=utf-8'
    return json.dumps(config.get_system_info(), ensure_ascii=False)


@eel.btl.route('/api/get_default_output', method=['GET'])
def api_get_default_output():
    """Retorna o diretório padrão de saída do sistema."""
    eel.btl.response.content_type = 'application/json; charset=utf-8'
    return json.dumps({"success": True, "path": get_default_output_dir()}, ensure_ascii=False)


@eel.btl.route('/api/convert', method=['POST'])
def api_convert():
    """Endpoint principal de conversão universal."""
    eel.btl.response.content_type = 'application/json; charset=utf-8'
    try:
        output_dir = eel.btl.request.forms.get('output_dir', '')
        upload = eel.btl.request.files.get('file')
        file_base64 = eel.btl.request.forms.get('file_base64', '')
        file_name_param = eel.btl.request.forms.get('file_name', '')
        file_path = eel.btl.request.forms.get('file_path', '')
        
        # 1. Prioriza o arquivo binário (evita overhead do Base64)
        if upload:
            file_name = upload.raw_filename or upload.filename
            file_bytes = upload.file.read()
            res = process_conversion(file_name=file_name, file_bytes=file_bytes, output_dir=output_dir)
            return json.dumps(res, ensure_ascii=False)
        
        # 2. Fallback para Base64
        elif file_base64:
            if ',' in file_base64:
                file_base64 = file_base64.split(',', 1)[1]
            file_bytes = base64.b64decode(file_base64)
            file_name = file_name_param or "documento"
            res = process_conversion(file_name=file_name, file_bytes=file_bytes, output_dir=output_dir)
            return json.dumps(res, ensure_ascii=False)
            
        # 3. Fallback para caminho local no disco
        elif file_path:
            res = process_conversion(file_name=Path(file_path).name, file_path=file_path, output_dir=output_dir)
            return json.dumps(res, ensure_ascii=False)
            
        else:
            diag = {
                "category": "NO_FILE_DATA",
                "title": "Nenhum Dado Recebido",
                "explanation": "O navegador não enviou os dados do arquivo selecionado.",
                "suggestion": "Arraste o arquivo novamente ou selecione através do botão.",
                "rawError": "No payload received",
                "traceback": "",
                "fileName": ""
            }
            return json.dumps({"success": False, "error": "Nenhum arquivo enviado.", "diagnostic": diag}, ensure_ascii=False)
            
    except Exception as e:
        diag = diagnose_exception(e, "Upload")
        return json.dumps({"success": False, "error": str(e), "diagnostic": diag}, ensure_ascii=False)


@eel.btl.route('/api/select_directory', method=['GET', 'POST'])
def api_select_directory():
    """Abre diálogo nativo para seleção de pasta no Windows."""
    eel.btl.response.content_type = 'application/json; charset=utf-8'
    try:
        folder = dialog_service.open_folder_dialog()
        return json.dumps({"success": True, "path": folder}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@eel.btl.route('/api/select_files', method=['GET', 'POST'])
def api_select_files():
    """Abre diálogo nativo para seleção de múltiplos arquivos no Windows."""
    eel.btl.response.content_type = 'application/json; charset=utf-8'
    try:
        files = dialog_service.open_files_dialog()
        return json.dumps({"success": True, "files": files}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@eel.btl.route('/api/open_explorer', method=['POST'])
def api_open_explorer():
    """Abre um arquivo ou pasta no Windows Explorer com seleção visual."""
    eel.btl.response.content_type = 'application/json; charset=utf-8'
    try:
        body = eel.btl.request.body.read().decode('utf-8')
        data = json.loads(body)
        target_path = sanitize_path(data.get('path', ''))
        p = Path(target_path).resolve()
        
        if p.exists():
            if p.is_file():
                subprocess.run(f'explorer /select,"{p}"', shell=True)
            else:
                os.startfile(str(p))
            return json.dumps({"success": True}, ensure_ascii=False)
        elif p.parent.exists():
            os.startfile(str(p.parent))
            return json.dumps({"success": True}, ensure_ascii=False)
            
        return json.dumps({"success": False, "error": "Caminho não encontrado no sistema."}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@eel.btl.route('/api/open_editor', method=['POST'])
def api_open_editor():
    """Abre um arquivo no editor padrão do sistema operacional."""
    eel.btl.response.content_type = 'application/json; charset=utf-8'
    try:
        body = eel.btl.request.body.read().decode('utf-8')
        data = json.loads(body)
        p = Path(sanitize_path(data.get('path', ''))).resolve()
        
        if p.exists():
            os.startfile(str(p))
            return json.dumps({"success": True}, ensure_ascii=False)
        return json.dumps({"success": False, "error": "Arquivo não encontrado."}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


@eel.btl.route('/api/save_markdown', method=['POST'])
def api_save_markdown():
    """Salva edições manuais feitas no editor Raw Markdown."""
    eel.btl.response.content_type = 'application/json; charset=utf-8'
    try:
        body = eel.btl.request.body.read().decode('utf-8')
        data = json.loads(body)
        p = Path(sanitize_path(data.get('path', ''))).resolve()
        content = data.get('content', '')
        
        p.write_text(content, encoding="utf-8")
        stat = p.stat()
        
        from .converter import format_file_size
        return json.dumps({
            "success": True,
            "charCount": len(content),
            "wordCount": len(content.split()),
            "outputSize": format_file_size(stat.st_size)
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)


# ==========================================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ==========================================================================

def run_app():
    """Inicia o servidor e a interface desktop."""
    if not config.WEB_DIR.exists():
        print(f"[ERRO] Diretório frontend '{config.WEB_DIR}' não encontrado.")
        sys.exit(1)
        
    # Inicializa o Eel com o diretório web estático
    eel.init(str(config.WEB_DIR))
    
    # Inicia o OCR em background para evitar travamento na 1ª conversão
    preload_ocr_async()
    
    port = get_free_port()
    
    print("=" * 65)
    print(f"  🎬 MarkItDown Studio v{config.VERSION} - Conversor Universal & Vídeo/Áudio")
    print(f"  🌐 Servidor Local: http://localhost:{port}/index.html")
    print("  ⌨️  Pressione CTRL+C no terminal para encerrar o aplicativo.")
    print("=" * 65)
    
    started = False
    
    for mode in config.BROWSER_MODES:
        try:
            eel.start(
                'index.html',
                mode=mode,
                port=port,
                size=config.WINDOW_SIZE,
                position=config.WINDOW_POSITION,
                close_callback=lambda page, sockets: None
            )
            started = True
            break
        except Exception as ex:
            print(f"Tentando modo alternativo de navegador ({mode} falhou: {ex})...")
            continue
            
    if not started:
        print("[AVISO] Abrindo no navegador padrão do sistema...")
        eel.start('index.html', mode='default', port=port)


if __name__ == '__main__':
    run_app()
