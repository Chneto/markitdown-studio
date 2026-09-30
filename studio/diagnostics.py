"""
MarkItDown Studio v0.2.0 — Sistema de diagnóstico estruturado de erros.
Classifica exceções em categorias amigáveis com explicações em Português e sugestões acionáveis.
"""

import traceback


# Categorias de erro conhecidas
ERROR_CATEGORIES = {
    "FFMPEG_MISSING": {
        "title": "FFMPEG Não Encontrado",
        "explanation": "O conversor de vídeo precisa do utilitário FFMPEG para extrair o áudio com máxima performance.",
        "suggestion": "Instale o FFMPEG no Windows ou utilize o motor embutido PyDub/OpenCV.",
        "keywords": ["ffmpeg", "ffprobe", "no ffmpeg", "avconv"],
    },
    "WHISPER_MODEL_ERROR": {
        "title": "Falha no Modelo Whisper / Speech-to-Text",
        "explanation": "Ocorreu uma falha ao carregar o modelo de transcrição Whisper ou memória de vídeo insuficiente.",
        "suggestion": "Tente utilizar um modelo menor (ex: 'small' ou 'base') ou ative a transcrição via Google Speech API.",
        "keywords": ["whisper", "faster_whisper", "ctranslate2", "cublas", "cudnn", "torch"],
    },
    "AUDIO_EXTRACTION_FAILED": {
        "title": "Falha na Extração do Áudio",
        "explanation": "Não foi possível extrair a faixa de áudio do arquivo de vídeo selecionado.",
        "suggestion": "Verifique se o vídeo possui áudio válido e se o arquivo não está corrompido.",
        "keywords": ["audio extraction", "could not find audio", "no audio stream", "audiosegment"],
    },
    "ENCRYPTED_FILE": {
        "title": "Arquivo Protegido por Senha",
        "explanation": "O arquivo PDF possui senha de proteção ou restrições de segurança que impedem a leitura.",
        "suggestion": "Remova a senha do PDF ou exporte uma cópia desprotegida antes de realizar a conversão.",
        "keywords": ["password", "encrypt", "crypted", "protected"],
    },
    "PERMISSION_DENIED": {
        "title": "Permissão de Gravação Negada",
        "explanation": "O sistema não tem permissão para salvar o arquivo na pasta de destino selecionada.",
        "suggestion": "Selecione outra pasta de destino (como Documentos ou Área de Trabalho) ou execute como Administrador.",
        "keywords": ["permission", "access is denied", "permissão", "denied"],
    },
    "CORRUPT_OR_MALFORMED": {
        "title": "Estrutura do Arquivo Inválida ou Danificada",
        "explanation": "A estrutura interna do arquivo contém dados corrompidos ou formato incompatível.",
        "suggestion": "Abra o arquivo no aplicativo original (ex: reprodutor de vídeo, Adobe Reader ou Word) e salve uma nova cópia ('Salvar Como').",
        "keywords": ["syntax", "header", "xref", "damaged", "corrupt", "invalid", "truncated", "bad zip"],
    },
    "ENCODING_ERROR": {
        "title": "Erro de Codificação de Caracteres",
        "explanation": "O arquivo contém caracteres especiais ou fontes não mapeadas na tabela padrão UTF-8.",
        "suggestion": "O sistema normaliza os caracteres automaticamente. Tente novamente.",
        "keywords": ["utf-8", "unicode", "charmap", "codec", "decode", "ascii"],
    },
    "FILE_NOT_FOUND": {
        "title": "Arquivo Não Encontrado",
        "explanation": "O arquivo especificado não foi encontrado no caminho indicado.",
        "suggestion": "Verifique se o arquivo não foi movido, renomeado ou excluído e tente novamente.",
        "keywords": ["not found", "no such file", "filenotfounderror"],
    },
    "UNSUPPORTED_FORMAT": {
        "title": "Formato de Arquivo Não Suportado",
        "explanation": "Este formato de arquivo não é suportado pelo conversor.",
        "suggestion": "Converta o arquivo para um formato suportado (MP4, MP3, PDF, DOCX, XLSX, etc.) e tente novamente.",
        "keywords": ["unsupported", "not supported", "unknown format", "extension"],
    },
    "MEMORY_ERROR": {
        "title": "Memória Insuficiente",
        "explanation": "O arquivo de mídia ou documento é muito grande e excedeu a memória RAM disponível durante o processamento.",
        "suggestion": "Feche outros programas abertos e tente novamente, ou utilize arquivos de menor duração.",
        "keywords": ["memoryerror", "out of memory", "memory", "cuda out of memory"],
    },
}


def diagnose_exception(exc: Exception, file_name: str, file_bytes: bytes = None):
    """Gera um diagnóstico estruturado e amigável sobre o erro ocorrido.
    
    Args:
        exc: A exceção capturada
        file_name: Nome do arquivo que causou o erro
        file_bytes: Bytes do arquivo (opcional, para diagnóstico avançado)
    
    Returns:
        dict com category, title, explanation, suggestion, rawError, traceback, fileName
    """
    exc_type = type(exc).__name__
    exc_msg = str(exc)
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    
    # Texto combinado para busca de keywords
    search_text = f"{exc_msg} {exc_type}".lower()
    
    # Busca a categoria mais adequada
    category = "GENERIC_ERROR"
    title = "Erro na Conversão do Documento"
    explanation = f"Ocorreu uma falha ({exc_type}) durante o processamento do arquivo."
    suggestion = "Verifique se o arquivo não está corrompido ou aberto em outro programa e tente novamente."
    
    for cat_key, cat_info in ERROR_CATEGORIES.items():
        if any(kw in search_text for kw in cat_info["keywords"]):
            category = cat_key
            title = cat_info["title"]
            explanation = cat_info["explanation"]
            suggestion = cat_info["suggestion"]
            break
    
    return {
        "category": category,
        "title": title,
        "explanation": explanation,
        "suggestion": suggestion,
        "rawError": f"{exc_type}: {exc_msg}",
        "traceback": tb,
        "fileName": file_name,
    }
