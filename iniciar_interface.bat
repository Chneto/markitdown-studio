@echo off
chcp 65001 > nul
title MarkItDown Studio v0.2.0 - Conversor Universal & Vídeo/Áudio para Markdown

echo ======================================================================
echo          MARKITDOWN STUDIO v0.2.0 - INTERFACE LOCAL & SPEECH-TO-TEXT
echo ======================================================================
echo.
echo  Iniciando a interface gráfica...
echo  Formatos suportados:
echo    - Vídeos: MP4, MKV, AVI, MOV, WEBM, FLV, WMV
echo    - Áudios: MP3, WAV, M4A, OGG, FLAC, AAC, WMA
echo    - Documentos: PDF, Word, Excel, PowerPoint, HTML, EPUB, CSV, JSON
echo    - Imagens: PNG, JPG, JPEG, WEBP, BMP (com OCR RapidOCR)
echo.
echo  Para fechar o programa, feche a janela ou pressione CTRL+C aqui.
echo ======================================================================
echo.

set PYTHONPATH=%~dp0
python -m studio.app

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Ocorreu uma falha ao iniciar o aplicativo.
    echo Certifique-se de que o Python 3.10+ está instalado e configurado no PATH.
    echo.
    pause
)
