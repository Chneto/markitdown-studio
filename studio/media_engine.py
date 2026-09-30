"""
MarkItDown Studio v0.2.0 — Motor Audiovisual & Speech-to-Text de Alta Precisão.
Suporte para vídeos (.mp4, .mkv, .avi, .mov, .webm, .flv, .wmv, .m4v, .3gp, .ts, .mts, .ogv, .vob)
e áudios (.mp3, .wav, .m4a, .ogg, .flac, .aac, .wma, .opus, .aiff, .alac, .amr).

Extração de metadados técnicos (FFprobe, OpenCV, PyDub, Wave), segmentação temporal precisa
e arquitetura de contingência em múltiplos tiers:
- Tier 1: Faster-Whisper (CTranslate2 ONNX com modelos Large-v3 / Medium / Small / pt-BR)
- Tier 2: OpenAI-Whisper (PyTorch local)
- Tier 3: Google Gemini Multimodal SDK (Google GenAI / GenerativeAI)
- Tier 4: SpeechRecognition Chunked com Google Speech API (pt-BR)
"""

import io
import os
import sys
import json
import math
import time
import wave
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

from . import config

# Importações opcionais resilientes
try:
    import cv2
    HAS_OPENCV = True
except Exception:
    HAS_OPENCV = False

try:
    import pydub
    from pydub import AudioSegment
    HAS_PYDUB = True
except Exception:
    HAS_PYDUB = False

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except Exception:
    HAS_SPEECH_RECOGNITION = False


def format_timestamp(seconds: float, include_ms: bool = False) -> str:
    """Converte segundos em string de timestamp formatada [HH:MM:SS] ou [HH:MM:SS.mmm]."""
    if seconds is None or math.isnan(seconds) or seconds < 0:
        seconds = 0.0
    
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    
    if include_ms:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}.{ms:03d}"
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"


def extract_media_metadata(file_path: Path, ext: str) -> Dict[str, Any]:
    """Extrai metadados completos de vídeo ou áudio utilizando FFprobe, OpenCV, PyDub ou Wave."""
    meta = {
        "media_type": "Vídeo" if ext in config.VIDEO_EXTENSIONS else "Áudio",
        "duration_sec": 0.0,
        "duration_formatted": "00:00:00",
        "resolution": "N/D",
        "fps": "N/D",
        "frame_count": 0,
        "video_codec": "N/D",
        "audio_codec": "N/D",
        "audio_channels": "N/D",
        "audio_sample_rate": "N/D",
        "bitrate": "N/D",
    }

    # 1. Tenta extração de máxima precisão via FFprobe
    ffprobe_exe = shutil.which("ffprobe")
    if ffprobe_exe:
        try:
            cmd = [
                ffprobe_exe,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(file_path)
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", timeout=30)
            if res.returncode == 0 and res.stdout:
                data = json.loads(res.stdout)
                format_info = data.get("format", {})
                
                # Duração e Bitrate
                dur = float(format_info.get("duration", 0.0))
                if dur > 0:
                    meta["duration_sec"] = dur
                    meta["duration_formatted"] = format_timestamp(dur)
                    
                bitrate = int(format_info.get("bit_rate", 0))
                if bitrate > 0:
                    meta["bitrate"] = f"{bitrate // 1000} kbps"

                # Streams de vídeo e áudio
                for s in data.get("streams", []):
                    codec_type = s.get("codec_type")
                    if codec_type == "video" and meta["resolution"] == "N/D":
                        w = s.get("width", 0)
                        h = s.get("height", 0)
                        if w and h:
                            meta["resolution"] = f"{w} x {h}"
                            if w >= 3840:
                                meta["resolution"] += " (4K UHD)"
                            elif w >= 1920:
                                meta["resolution"] += " (Full HD 1080p)"
                            elif w >= 1280:
                                meta["resolution"] += " (HD 720p)"
                                
                        meta["video_codec"] = s.get("codec_name", "N/D").upper()
                        
                        # FPS
                        r_fps = s.get("r_frame_rate", "")
                        if "/" in r_fps:
                            num, den = map(float, r_fps.split("/"))
                            if den > 0:
                                meta["fps"] = f"{num / den:.2f} fps"
                        elif s.get("avg_frame_rate"):
                            meta["fps"] = f"{s.get('avg_frame_rate')} fps"
                            
                        nb_frames = s.get("nb_frames")
                        if nb_frames and str(nb_frames).isdigit():
                            meta["frame_count"] = int(nb_frames)

                    elif codec_type == "audio" and meta["audio_channels"] == "N/D":
                        meta["audio_codec"] = s.get("codec_name", "N/D").upper()
                        ch = s.get("channels", 0)
                        if ch == 1:
                            meta["audio_channels"] = "Mono (1 canal)"
                        elif ch == 2:
                            meta["audio_channels"] = "Estéreo (2 canais)"
                        elif ch > 2:
                            meta["audio_channels"] = f"{ch} canais (Surround)"
                            
                        sr_val = s.get("sample_rate")
                        if sr_val and str(sr_val).isdigit():
                            meta["audio_sample_rate"] = f"{int(sr_val)/1000:.1f} kHz ({sr_val} Hz)"
        except Exception as e:
            print(f"[MediaEngine] FFprobe falhou: {e}")

    # 2. Se for vídeo e resolução ainda N/D, usa OpenCV
    if ext in config.VIDEO_EXTENSIONS and meta["resolution"] == "N/D" and HAS_OPENCV:
        try:
            cap = cv2.VideoCapture(str(file_path))
            if cap.isOpened():
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                if width > 0 and height > 0:
                    meta["resolution"] = f"{width} x {height}"
                    if width >= 3840:
                        meta["resolution"] += " (4K UHD)"
                    elif width >= 1920:
                        meta["resolution"] += " (Full HD 1080p)"
                    elif width >= 1280:
                        meta["resolution"] += " (HD 720p)"
                        
                if fps and fps > 0:
                    meta["fps"] = f"{fps:.2f} fps"
                    if frame_count > 0 and meta["duration_sec"] <= 0:
                        duration = frame_count / fps
                        meta["duration_sec"] = duration
                        meta["duration_formatted"] = format_timestamp(duration)
                        meta["frame_count"] = frame_count
                cap.release()
        except Exception as e:
            print(f"[MediaEngine] OpenCV falhou: {e}")

    # 3. Se áudio ainda não extraído, usa PyDub
    if meta["duration_sec"] <= 0 or meta["audio_channels"] == "N/D":
        if HAS_PYDUB:
            try:
                audio_format = ext.replace(".", "")
                if audio_format in ["mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "m4v", "3gp", "ts", "mts", "ogv", "vob"]:
                    audio_format = None
                
                seg = AudioSegment.from_file(str(file_path), format=audio_format)
                if seg:
                    audio_dur = seg.duration_seconds
                    if meta["duration_sec"] <= 0 or abs(meta["duration_sec"] - audio_dur) > 2.0:
                        meta["duration_sec"] = audio_dur
                        meta["duration_formatted"] = format_timestamp(audio_dur)
                        
                    if meta["audio_channels"] == "N/D":
                        meta["audio_channels"] = "Estéreo (2 canais)" if seg.channels == 2 else f"{seg.channels} canal(is)"
                    if meta["audio_sample_rate"] == "N/D":
                        meta["audio_sample_rate"] = f"{seg.frame_rate / 1000:.1f} kHz ({seg.frame_rate} Hz)"
            except Exception:
                pass

    # 4. Fallback padrão via módulo wave se for .wav
    if ext == ".wav" and (meta["duration_sec"] <= 0 or meta["audio_channels"] == "N/D"):
        try:
            with wave.open(str(file_path), "rb") as wf:
                channels = wf.getnchannels()
                rate = wf.getframerate()
                frames = wf.getnframes()
                if rate > 0:
                    dur = frames / float(rate)
                    meta["duration_sec"] = dur
                    meta["duration_formatted"] = format_timestamp(dur)
                    meta["audio_channels"] = "Mono (1 canal)" if channels == 1 else ("Estéreo (2 canais)" if channels == 2 else f"{channels} canais")
                    meta["audio_sample_rate"] = f"{rate/1000:.1f} kHz ({rate} Hz)"
        except Exception:
            pass

    return meta


def extract_wav_from_media(input_path: Path, output_wav_path: Path) -> bool:
    """Extrai trilha de áudio em formato PCM WAV mono 16kHz para alimentar os motores de transcrição."""
    ext = input_path.suffix.lower()

    # 1. Se já for WAV válido, verifica ou copia
    if ext == ".wav":
        try:
            with wave.open(str(input_path), "rb") as wf:
                if wf.getnchannels() == 1 and wf.getframerate() == 16000 and wf.getsampwidth() == 2:
                    # Já está no formato ideal PCM mono 16kHz
                    shutil.copyfile(str(input_path), str(output_wav_path))
                    return True
        except Exception:
            pass

    # 2. Tenta via FFMPEG se disponível (mais rápido e suporta todos os codecs)
    ffmpeg_exe = shutil.which("ffmpeg")
    if ffmpeg_exe:
        try:
            cmd = [
                ffmpeg_exe,
                "-y",
                "-i", str(input_path),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(output_wav_path)
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
            if res.returncode == 0 and output_wav_path.exists() and output_wav_path.stat().st_size > 44:
                return True
        except Exception as e:
            print(f"[MediaEngine] FFMPEG falhou na extração: {e}")

    # 3. Tenta via PyDub
    if HAS_PYDUB:
        try:
            seg = AudioSegment.from_file(str(input_path))
            seg = seg.set_frame_rate(16000).set_channels(1)
            seg.export(str(output_wav_path), format="wav")
            if output_wav_path.exists() and output_wav_path.stat().st_size > 44:
                return True
        except Exception as e:
            print(f"[MediaEngine] PyDub falhou na extração: {e}")

    # 4. Cópia direta para arquivos .wav caso pydub/ffmpeg não estejam presentes
    if ext == ".wav" and input_path.exists():
        try:
            shutil.copyfile(str(input_path), str(output_wav_path))
            return True
        except Exception:
            pass

    return False


def transcribe_with_faster_whisper(wav_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Tier 1: Transcrição com faster-whisper (CTranslate2 ONNX de alta precisão).
    Testa modelos em cascata (large-v3 -> medium -> small -> base) com fallback de compute_type para evitar falhas no CPU."""
    try:
        from faster_whisper import WhisperModel
        
        # Lista de modelos a testar a partir da preferência configurada
        model_candidates = [config.WHISPER_MODEL]
        for fallback in config.WHISPER_FALLBACK_MODELS:
            if fallback not in model_candidates:
                model_candidates.append(fallback)

        model = None
        selected_model_name = ""

        for candidate in model_candidates:
            print(f"[MediaEngine] Tentando inicializar Faster-Whisper ({candidate})...")
            try:
                # Tenta compute_type especificado
                model = WhisperModel(
                    candidate,
                    device="auto",
                    compute_type=config.WHISPER_COMPUTE_TYPE
                )
                selected_model_name = candidate
                break
            except Exception as ex_init:
                # Fallback seguro para CPU com INT8 (previne erro de float16 no Windows)
                try:
                    model = WhisperModel(
                        candidate,
                        device="cpu",
                        compute_type="int8"
                    )
                    selected_model_name = candidate
                    break
                except Exception as ex_cpu:
                    print(f"[MediaEngine] Falha ao carregar modelo '{candidate}': {ex_cpu}")
                    continue

        if model is None:
            return None

        print(f"[MediaEngine] Transcrevendo com Faster-Whisper ({selected_model_name.upper()})...")
        segments, info = model.transcribe(
            str(wav_path),
            language=config.WHISPER_LANGUAGE if config.WHISPER_LANGUAGE != "auto" else None,
            beam_size=config.WHISPER_BEAM_SIZE,
            vad_filter=config.WHISPER_VAD_FILTER,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        results = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                results.append({
                    "start": segment.start,
                    "end": segment.end,
                    "start_str": format_timestamp(segment.start),
                    "end_str": format_timestamp(segment.end),
                    "text": text,
                    "model_used": f"Faster-Whisper ({selected_model_name.upper()})"
                })
        return results if results else None
    except ImportError:
        return None
    except Exception as e:
        print(f"[MediaEngine] Falha no Faster-Whisper: {e}")
        return None


def transcribe_with_openai_whisper(wav_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Tier 2: Transcrição com OpenAI Whisper padrão (PyTorch)."""
    try:
        import whisper
        model_candidates = [config.WHISPER_MODEL]
        for fallback in config.WHISPER_FALLBACK_MODELS:
            if fallback not in model_candidates:
                model_candidates.append(fallback)

        model = None
        selected_model_name = ""
        for candidate in model_candidates:
            try:
                model = whisper.load_model(candidate)
                selected_model_name = candidate
                break
            except Exception:
                continue

        if model is None:
            return None

        res = model.transcribe(
            str(wav_path),
            language=config.WHISPER_LANGUAGE if config.WHISPER_LANGUAGE != "auto" else None
        )
        
        results = []
        for seg in res.get("segments", []):
            text = seg.get("text", "").strip()
            if text:
                results.append({
                    "start": seg.get("start", 0.0),
                    "end": seg.get("end", 0.0),
                    "start_str": format_timestamp(seg.get("start", 0.0)),
                    "end_str": format_timestamp(seg.get("end", 0.0)),
                    "text": text,
                    "model_used": f"OpenAI Whisper ({selected_model_name.upper()})"
                })
        return results if results else None
    except ImportError:
        return None
    except Exception as e:
        print(f"[MediaEngine] Falha no OpenAI Whisper: {e}")
        return None


def transcribe_with_gemini(media_path: Path, ext: str) -> Optional[List[Dict[str, Any]]]:
    """Tier 3: Transcrição multimodal de alta fidelidade via Google GenAI / Gemini Ecosystem."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        print(f"[MediaEngine] Conectando ao Google Gemini Multimodal ({config.GEMINI_MODEL})...")
        
        # 1. Tenta nova biblioteca google-genai
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            
            # Envia áudio/vídeo para análise com instrução de formatação de timestamps
            uploaded_file = client.files.upload(file=str(media_path))
            
            prompt = (
                "Você é um transcritor profissional de alta precisão em Português do Brasil.\n"
                "Transcreva todo o áudio com máxima fidelidade às falas.\n"
                "Formate a resposta ESTRITAMENTE em formato JSON com a lista de segmentos temporais:\n"
                "[\n"
                "  {\"start\": 0.0, \"end\": 12.5, \"text\": \"Texto falado no trecho...\"},\n"
                "  ...\n"
                "]\n"
                "Retorne apenas o JSON puro, sem blocos de markdown adicionais."
            )
            
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=[uploaded_file, prompt]
            )
            
            if response and response.text:
                clean_json = response.text.strip()
                if clean_json.startswith("```"):
                    clean_json = clean_json.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                parsed = json.loads(clean_json)
                
                results = []
                for item in parsed:
                    st = float(item.get("start", 0.0))
                    en = float(item.get("end", st + 5.0))
                    txt = str(item.get("text", "")).strip()
                    if txt:
                        results.append({
                            "start": st,
                            "end": en,
                            "start_str": format_timestamp(st),
                            "end_str": format_timestamp(en),
                            "text": txt,
                            "model_used": f"Google Gemini ({config.GEMINI_MODEL})"
                        })
                return results if results else None
        except ImportError:
            pass

        # 2. Tenta biblioteca clássica google-generativeai
        try:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=api_key)
            model = genai_legacy.GenerativeModel("gemini-1.5-flash")
            
            uploaded_file = genai_legacy.upload_file(str(media_path))
            prompt = (
                "Transcreva o áudio deste arquivo em Português do Brasil com timestamps detalhados.\n"
                "Formate como JSON: [{\"start\": 0.0, \"end\": 10.0, \"text\": \"...\"}]"
            )
            response = model.generate_content([uploaded_file, prompt])
            if response and response.text:
                clean_json = response.text.strip()
                if clean_json.startswith("```"):
                    clean_json = clean_json.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                parsed = json.loads(clean_json)
                results = []
                for item in parsed:
                    st = float(item.get("start", 0.0))
                    en = float(item.get("end", st + 5.0))
                    txt = str(item.get("text", "")).strip()
                    if txt:
                        results.append({
                            "start": st,
                            "end": en,
                            "start_str": format_timestamp(st),
                            "end_str": format_timestamp(en),
                            "text": txt,
                            "model_used": "Google Gemini (1.5 Flash)"
                        })
                return results if results else None
        except ImportError:
            pass

    except Exception as e:
        print(f"[MediaEngine] Google Gemini falhou: {e}")

    return None


def transcribe_with_speech_recognition_chunked(wav_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Tier 4: Transcrição segmentada em chunks temporais com SpeechRecognition e Google Speech API pt-BR."""
    if not HAS_SPEECH_RECOGNITION:
        return None
        
    try:
        print("[MediaEngine] Transcrevendo via SpeechRecognition (Google Speech API pt-BR)...")
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        results = []

        # Caso PyDub esteja disponível, faz fatiamento fino em chunks
        if HAS_PYDUB:
            sound = AudioSegment.from_file(str(wav_path))
            chunk_length_ms = config.AUDIO_CHUNK_DURATION_SEC * 1000
            total_length_ms = len(sound)
            
            for i in range(0, total_length_ms, chunk_length_ms):
                chunk = sound[i:i + chunk_length_ms]
                start_sec = i / 1000.0
                end_sec = min((i + chunk_length_ms), total_length_ms) / 1000.0
                
                buf = io.BytesIO()
                chunk.export(buf, format="wav")
                buf.seek(0)
                
                with sr.AudioFile(buf) as source:
                    try:
                        audio_data = recognizer.record(source)
                        text = recognizer.recognize_google(audio_data, language=config.GOOGLE_SPEECH_LANGUAGE).strip()
                        if text:
                            results.append({
                                "start": start_sec,
                                "end": end_sec,
                                "start_str": format_timestamp(start_sec),
                                "end_str": format_timestamp(end_sec),
                                "text": text,
                                "model_used": f"Google Speech API ({config.GOOGLE_SPEECH_LANGUAGE})"
                            })
                    except sr.UnknownValueError:
                        continue
                    except Exception as chunk_err:
                        print(f"[MediaEngine] Chunk {start_sec:.1f}s erro: {chunk_err}")
                        continue
        else:
            # Sem PyDub, usa SpeechRecognition direto no arquivo WAV
            with sr.AudioFile(str(wav_path)) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data, language=config.GOOGLE_SPEECH_LANGUAGE).strip()
                    if text:
                        results.append({
                            "start": 0.0,
                            "end": 0.0,
                            "start_str": "00:00:00",
                            "end_str": "00:00:00",
                            "text": text,
                            "model_used": f"Google Speech API ({config.GOOGLE_SPEECH_LANGUAGE})"
                        })
                except Exception:
                    pass

        return results if results else None
    except Exception as e:
        print(f"[MediaEngine] Falha no SpeechRecognition Chunked: {e}")
        return None


def process_media_to_markdown(
    file_name: str,
    file_bytes: Optional[bytes] = None,
    file_path: Optional[str] = None,
    temp_dir: Optional[Path] = None
) -> Tuple[str, str]:
    """Pipeline completo e otimizado de conversão de Vídeo / Áudio para Markdown estruturado.
    Opera diretamente sobre arquivo local ou sobre buffer em memória para máxima eficiência de RAM."""
    src_stem = Path(file_name).stem
    ext = Path(file_name).suffix.lower()
    
    if temp_dir is None:
        from .converter import get_default_output_dir
        temp_dir = Path(get_default_output_dir())

    temp_media = None
    temp_wav = temp_dir / f"_audio_{int(time.time()*1000)}_{src_stem}.wav"
    
    try:
        # Determina o caminho de trabalho da mídia
        if file_path and Path(file_path).exists():
            active_media_path = Path(file_path)
            file_size_bytes = active_media_path.stat().st_size
        elif file_bytes is not None:
            temp_media = temp_dir / f"_media_{int(time.time()*1000)}_{file_name}"
            temp_media.write_bytes(file_bytes)
            active_media_path = temp_media
            file_size_bytes = len(file_bytes)
        else:
            raise ValueError(f"Nenhum dado ou caminho fornecido para a mídia: {file_name}")

        # 1. Extrai metadados técnicos do arquivo
        meta = extract_media_metadata(active_media_path, ext)
        
        # 2. Extrai áudio WAV mono 16kHz
        wav_extracted = extract_wav_from_media(active_media_path, temp_wav)
        audio_target = temp_wav if wav_extracted else active_media_path
        
        # 3. Executa pipeline de transcrição em cascata
        segments: Optional[List[Dict[str, Any]]] = None
        engine_used = "Nenhum"
        
        # Tier 1: Faster-Whisper (Modelo Large-v3 / Medium de Alta Precisão)
        segments = transcribe_with_faster_whisper(audio_target)
        if segments:
            engine_used = segments[0].get("model_used", f"Faster-Whisper ({config.WHISPER_MODEL.upper()} - pt-BR)")
            
        # Tier 2: OpenAI Whisper Local
        if not segments:
            segments = transcribe_with_openai_whisper(audio_target)
            if segments:
                engine_used = segments[0].get("model_used", f"OpenAI Whisper ({config.WHISPER_MODEL.upper()})")

        # Tier 3: Google Gemini Multimodal SDK
        if not segments:
            segments = transcribe_with_gemini(active_media_path, ext)
            if segments:
                engine_used = segments[0].get("model_used", f"Google Gemini ({config.GEMINI_MODEL})")

        # Tier 4: SpeechRecognition Chunked com Google Speech API (pt-BR)
        if not segments and (wav_extracted or ext in [".wav", ".mp3", ".m4a", ".ogg"]):
            segments = transcribe_with_speech_recognition_chunked(audio_target)
            if segments:
                engine_used = segments[0].get("model_used", f"Google Speech Recognition ({config.GOOGLE_SPEECH_LANGUAGE})")

        # 4. Cálculo de Estatísticas e Métricas
        total_words = 0
        total_segments = len(segments) if segments else 0
        if segments:
            for s in segments:
                total_words += len(s.get("text", "").split())

        duration_sec = meta.get("duration_sec", 0.0)
        wpm_est = round((total_words / (duration_sec / 60.0))) if duration_sec >= 10.0 else 0

        # 5. Montagem do Markdown
        icon = "🎬" if ext in config.VIDEO_EXTENSIONS else "🎙️"
        media_label = "Vídeo" if ext in config.VIDEO_EXTENSIONS else "Áudio"
        
        md_lines = [
            f"# {icon} {src_stem}\n",
            f"**Tipo:** {media_label} ({ext.upper()}) | **Duração:** {meta['duration_formatted']} | **Motor Speech-to-Text:** {engine_used}\n",
            "## Informações Técnicas da Mídia\n",
            "| Propriedade | Detalhe |",
            "| :--- | :--- |",
            f"| **Formato do Contêiner** | `{ext.upper()}` |",
            f"| **Duração Estimada** | `{meta['duration_formatted']}` ({meta['duration_sec']:.1f} segundos) |",
        ]
        
        if ext in config.VIDEO_EXTENSIONS:
            md_lines.append(f"| **Resolução de Vídeo** | `{meta['resolution']}` |")
            md_lines.append(f"| **Taxa de Quadros (FPS)** | `{meta['fps']}` |")
            if meta.get("video_codec") != "N/D":
                md_lines.append(f"| **Codec de Vídeo** | `{meta['video_codec']}` |")
            if meta['frame_count'] > 0:
                md_lines.append(f"| **Total de Quadros** | `{meta['frame_count']:,} quadros` |")
                
        if meta.get("audio_codec") != "N/D":
            md_lines.append(f"| **Codec de Áudio** | `{meta['audio_codec']}` |")
        md_lines.append(f"| **Canais de Áudio** | `{meta['audio_channels']}` |")
        md_lines.append(f"| **Taxa de Amostragem** | `{meta['audio_sample_rate']}` |")
        if meta.get("bitrate") != "N/D":
            md_lines.append(f"| **Taxa de Bits (Bitrate)** | `{meta['bitrate']}` |")
        md_lines.append(f"| **Tamanho do Arquivo** | `{file_size_bytes / (1024*1024):.2f} MB` |")
        md_lines.append(f"| **Motor de Transcrição** | `{engine_used}` |")
        md_lines.append("\n---\n")

        # Métricas da Transcrição
        if segments:
            md_lines.append("## 📊 Métricas da Transcrição\n")
            md_lines.append(f"- **Total de Segmentos:** `{total_segments}` blocos de fala")
            md_lines.append(f"- **Total de Palavras Transcritas:** `{total_words}` palavras")
            if wpm_est > 0:
                md_lines.append(f"- **Velocidade Média de Fala:** ~`{wpm_est}` PPM (palavras por minuto)")
            md_lines.append("\n---\n")

        # Seção de Transcrição com Marcadores Temporais
        md_lines.append("## ⏱️ Transcrição Detalhada com Marcadores Temporais\n")
        
        if segments and len(segments) > 0:
            full_text_paragraphs = []
            
            for seg in segments:
                t_start = seg.get("start_str", "00:00:00")
                t_end = seg.get("end_str", "00:00:00")
                text = seg.get("text", "").strip()
                
                if text:
                    md_lines.append(f"> **`[{t_start} ➔ {t_end}]`**  \n> {text}\n")
                    full_text_paragraphs.append(text)
                    
            md_lines.append("\n---\n")
            md_lines.append("## 📝 Transcrição Contínua (Texto Unificado)\n")
            md_lines.append("\n\n".join(full_text_paragraphs))
        else:
            md_lines.append("> ℹ️ *Nenhuma fala inteligível foi detectada ou a faixa de áudio está silenciosa.*\n")
            md_lines.append("\n> **Dica:** Para transcrição de alta fidelidade com modelos Whisper locais, certifique-se de que o pacote `faster-whisper` e o `ffmpeg` estejam instalados no sistema.")

        return "\n".join(md_lines), src_stem

    finally:
        # Limpeza de arquivos temporários criados dinamicamente
        for f in [temp_media, temp_wav]:
            if f is not None and f.exists():
                try:
                    f.unlink()
                except Exception:
                    pass
