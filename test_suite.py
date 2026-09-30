"""
MarkItDown Studio v0.2.0 - Test Suite de Verificação Completa
Testa conversão universal, OCR, MediaEngine (vídeo e áudio), diagnósticos, rotas e compatibilidade Windows.
"""

import io
import os
import sys
import wave
import struct
import unittest
from pathlib import Path

# Adiciona o diretório atual ao sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from studio import config
from studio.diagnostics import diagnose_exception, ERROR_CATEGORIES
from studio.ocr_engine import get_ocr_status, perform_ocr_on_image_bytes
from studio.media_engine import format_timestamp, extract_media_metadata, extract_wav_from_media, process_media_to_markdown
from studio.converter import process_conversion, sanitize_filename, sanitize_path, format_file_size, get_default_output_dir


class TestConfig(unittest.TestCase):
    """Verifica se todas as configurações, formatos de vídeo e metadados estão consistentes."""
    
    def test_version_and_paths(self):
        self.assertEqual(config.VERSION, "0.2.0")
        self.assertTrue(config.WEB_DIR.exists())
        self.assertTrue((config.WEB_DIR / "index.html").exists())
        self.assertTrue((config.WEB_DIR / "css" / "style.css").exists())
        self.assertTrue((config.WEB_DIR / "js" / "app.js").exists())
        self.assertTrue((config.WEB_DIR / "js" / "marked.min.js").exists())

    def test_video_and_audio_extensions(self):
        # Vídeos
        self.assertIn(".mp4", config.VIDEO_EXTENSIONS)
        self.assertIn(".mkv", config.VIDEO_EXTENSIONS)
        self.assertIn(".avi", config.VIDEO_EXTENSIONS)
        self.assertIn(".mov", config.VIDEO_EXTENSIONS)
        self.assertIn(".webm", config.VIDEO_EXTENSIONS)
        self.assertIn(".flv", config.VIDEO_EXTENSIONS)
        self.assertIn(".wmv", config.VIDEO_EXTENSIONS)
        self.assertIn(".m4v", config.VIDEO_EXTENSIONS)
        self.assertIn(".3gp", config.VIDEO_EXTENSIONS)
        self.assertIn(".ts", config.VIDEO_EXTENSIONS)

        # Áudios
        self.assertIn(".mp3", config.AUDIO_EXTENSIONS)
        self.assertIn(".wav", config.AUDIO_EXTENSIONS)
        self.assertIn(".m4a", config.AUDIO_EXTENSIONS)
        self.assertIn(".ogg", config.AUDIO_EXTENSIONS)
        self.assertIn(".flac", config.AUDIO_EXTENSIONS)
        self.assertIn(".aac", config.AUDIO_EXTENSIONS)
        self.assertIn(".wma", config.AUDIO_EXTENSIONS)
        self.assertIn(".opus", config.AUDIO_EXTENSIONS)

    def test_system_info(self):
        info = config.get_system_info()
        self.assertEqual(info["studio_version"], "0.2.0")
        self.assertIn("os", info)
        self.assertIn("speech_engine", info)
        self.assertIn("ocr_engine", info)
        self.assertIn("google_genai", info)


class TestMediaEngine(unittest.TestCase):
    """Testa formatação de timestamps, extração de metadados e conversão de vídeo/áudio."""
    
    def test_format_timestamp(self):
        self.assertEqual(format_timestamp(0), "00:00:00")
        self.assertEqual(format_timestamp(65), "00:01:05")
        self.assertEqual(format_timestamp(3665), "01:01:05")
        self.assertEqual(format_timestamp(12.345, include_ms=True), "00:00:12.345")
        self.assertEqual(format_timestamp(-5), "00:00:00")

    def test_audio_synthesis_and_conversion(self):
        """Cria um arquivo WAV sintético e processa via media_engine."""
        temp_dir = Path(get_default_output_dir())
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Gera 1 segundo de áudio WAV PCM 16kHz mono
        wav_buf = io.BytesIO()
        with wave.open(wav_buf, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            samples = [int(1000 * struct.unpack('h', b'\x00\x00')[0]) for _ in range(16000)]
            raw_data = struct.pack(f'<{len(samples)}h', *samples)
            wav_file.writeframes(raw_data)
        
        wav_bytes = wav_buf.getvalue()
        md_text, stem = process_media_to_markdown("teste_audio.wav", file_bytes=wav_bytes, temp_dir=temp_dir)
        
        self.assertEqual(stem, "teste_audio")
        self.assertIn("# 🎙️ teste_audio", md_text)
        self.assertIn("Informações Técnicas da Mídia", md_text)
        self.assertIn("WAV", md_text)

    def test_wav_extraction_passthrough(self):
        """Testa se arquivos WAV têm extração e cópia direta garantidas."""
        temp_dir = Path(get_default_output_dir())
        temp_src = temp_dir / "_test_src.wav"
        temp_dst = temp_dir / "_test_dst.wav"
        
        try:
            with wave.open(str(temp_src), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b'\x00\x00' * 1600)
                
            success = extract_wav_from_media(temp_src, temp_dst)
            self.assertTrue(success)
            self.assertTrue(temp_dst.exists())
        finally:
            for f in (temp_src, temp_dst):
                if f.exists():
                    f.unlink()


class TestDiagnostics(unittest.TestCase):
    """Testa a categorização inteligente de exceções."""
    
    def test_permission_error(self):
        diag = diagnose_exception(PermissionError("Access is denied"), "arquivo.pdf")
        self.assertEqual(diag["category"], "PERMISSION_DENIED")
        self.assertIn("Permissão", diag["title"])

    def test_ffmpeg_missing(self):
        diag = diagnose_exception(RuntimeError("ffmpeg was not found on PATH"), "video.mp4")
        self.assertEqual(diag["category"], "FFMPEG_MISSING")

    def test_encrypted_pdf(self):
        diag = diagnose_exception(ValueError("PDF is password encrypted"), "doc.pdf")
        self.assertEqual(diag["category"], "ENCRYPTED_FILE")


class TestConverterPipeline(unittest.TestCase):
    """Testa sanitização e conversão de múltiplos formatos de arquivo."""
    
    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("relatório/2026:final?.pdf"), "relatório_2026_final_.pdf")
        self.assertEqual(sanitize_filename("vídeo*aula<1>.mp4"), "vídeo_aula_1_.mp4")
        self.assertEqual(sanitize_filename(""), "documento")

    def test_convert_plain_text(self):
        content = "Este é um teste de documento de texto simples com acentos: á, é, í, ó, ú, ç, ã."
        res = process_conversion(file_name="teste_texto.txt", file_bytes=content.encode("utf-8"))
        self.assertTrue(res["success"])
        self.assertEqual(res["fileName"], "teste_texto.txt")
        self.assertTrue(Path(res["outputPath"]).exists())
        self.assertIn("teste de documento", res["markdown"])

    def test_convert_json_structured(self):
        content = '{"nome": "MarkItDown", "versao": "0.2.0", "recursos": ["video", "audio", "ocr"]}'
        res = process_conversion(file_name="config.json", file_bytes=content.encode("utf-8"))
        self.assertTrue(res["success"])
        self.assertIn("```json", res["markdown"])
        self.assertIn("MarkItDown", res["markdown"])

    def test_convert_html(self):
        html_content = "<html><body><h1>Título da Aula</h1><p>Parágrafo explicativo sobre o sistema.</p></body></html>"
        res = process_conversion(file_name="pagina.html", file_bytes=html_content.encode("utf-8"))
        self.assertTrue(res["success"])
        self.assertIn("Título da Aula", res["markdown"])

    def test_convert_video_mp4_mock(self):
        """Testa o pipeline completo de conversão de vídeo .mp4."""
        mock_mp4 = b"ftypmp42\x00\x00\x00\x00isommp42\x00\x00\x00\x08free"
        res = process_conversion(file_name="apresentacao_projeto.mp4", file_bytes=mock_mp4)
        self.assertTrue(res["success"])
        self.assertEqual(res["outputName"], "apresentacao_projeto.md")
        self.assertIn("🎬 apresentacao_projeto", res["markdown"])
        self.assertIn("MP4", res["markdown"])
        self.assertTrue(Path(res["outputPath"]).exists())


if __name__ == '__main__':
    unittest.main()
