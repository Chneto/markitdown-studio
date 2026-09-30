"""
MarkItDown Studio v0.2.0 — Diálogos nativos do Windows em subprocessos isolados.
Isola chamadas do Tkinter para prevenir deadlocks com o loop gevent do Eel.
"""

import sys
import subprocess
import json
from pathlib import Path

from .config import PYTHON_EXE, SUPPORTED_EXTENSIONS


def open_folder_dialog(title="Selecione a pasta de destino"):
    """Abre um diálogo nativo para escolher pasta."""
    script = f"""
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)
folder = filedialog.askdirectory(title={repr(title)})
root.destroy()
if folder:
    print(folder)
"""
    try:
        proc = subprocess.run(
            [PYTHON_EXE, "-c", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except Exception as e:
        print(f"[Dialog] Erro ao abrir diálogo de pasta: {e}")
    return ""


def open_files_dialog(title="Selecione os arquivos para converter"):
    """Abre um diálogo nativo para selecionar múltiplos arquivos com filtros completos."""
    all_exts = ";".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))
    
    script = f"""
import tkinter as tk
from tkinter import filedialog
import json

root = tk.Tk()
root.withdraw()
root.attributes('-topmost', True)

filetypes = [
    ("Todos os formatos suportados", "{all_exts}"),
    ("Vídeos (*.mp4;*.mkv;*.avi;*.mov;*.webm;*.flv;*.wmv;*.m4v;*.3gp;*.ts;*.mts;*.ogv;*.vob)", "*.mp4;*.mkv;*.avi;*.mov;*.webm;*.flv;*.wmv;*.m4v;*.3gp;*.ts;*.mts;*.ogv;*.vob"),
    ("Áudios (*.mp3;*.wav;*.m4a;*.ogg;*.flac;*.aac;*.wma;*.opus;*.aiff;*.alac;*.amr)", "*.mp3;*.wav;*.m4a;*.ogg;*.flac;*.aac;*.wma;*.opus;*.aiff;*.alac;*.amr"),
    ("Documentos PDF (*.pdf)", "*.pdf"),
    ("Documentos Word (*.docx;*.doc;*.odt;*.rtf)", "*.docx;*.doc;*.odt;*.rtf"),
    ("Planilhas Excel e Dados (*.xlsx;*.xls;*.csv;*.tsv;*.ods)", "*.xlsx;*.xls;*.csv;*.tsv;*.ods"),
    ("Apresentações PowerPoint (*.pptx;*.ppt;*.odp)", "*.pptx;*.ppt;*.odp"),
    ("Páginas Web e eBooks (*.html;*.htm;*.epub;*.json;*.xml;*.yaml;*.yml)", "*.html;*.htm;*.epub;*.json;*.xml;*.yaml;*.yml"),
    ("Imagens (*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.gif;*.tiff;*.svg)", "*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.gif;*.tiff;*.svg"),
    ("Arquivos Compactados (*.zip)", "*.zip"),
    ("Todos os Arquivos (*.*)", "*.*")
]

files = filedialog.askopenfilenames(title={repr(title)}, filetypes=filetypes)
root.destroy()
print(json.dumps(list(files)))
"""
    try:
        proc = subprocess.run(
            [PYTHON_EXE, "-c", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return json.loads(proc.stdout.strip())
    except Exception as e:
        print(f"[Dialog] Erro ao abrir diálogo de arquivos: {e}")
    return []
