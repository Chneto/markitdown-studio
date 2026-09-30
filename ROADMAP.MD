# 🗺️ ROADMAP.MD — Plano de Desenvolvimento e Evolução

Este documento delineia as fases de desenvolvimento, recursos implementados, marcos alcançados e planos futuros para o **MarkItDown Studio**.

---

## 🎯 Visão Geral do Produto

O **MarkItDown Studio** é uma estação de trabalho local de alta produtividade focada na conversão universal de documentos corporativos, mídias audiovisuais, planilhas e imagens em Markdown limpo, semântico e pronto para consumo por Modelos de Linguagem Grande (LLMs).

---

## 📅 Linha do Tempo e Marcos

### ✅ Fase 1 — Fundação & Interface Modular (v0.1.0 - v0.1.7)
- [x] Estrutura modular desacoplada em `studio/` (`app.py`, `config.py`, `converter.py`, `diagnostics.py`, `ocr_engine.py`, `dialog_service.py`).
- [x] Frontend moderno com tema claro/escuro, drag & drop de múltiplos arquivos e pastas.
- [x] Pré-visualização lado a lado: Markdown renderizado em HTML vs. Editor de código fonte puro.
- [x] Motor de OCR local baseado em `rapidocr-onnxruntime` com inicialização e pré-aquecimento em background.
- [x] Pipeline multi-estágio para PDFs (MarkItDown nativo -> PyPDFium2 -> Detecção de páginas digitalizadas -> OCR individual).
- [x] Diálogos nativos do Windows executados em subprocessos isolados para evitar travamentos de concorrência com Eel/Gevent.
- [x] Sistema de diagnóstico estruturado com sugestões e classificação de erros.

---

### 🚀 Fase 2 — Audiovisual de Alta Precisão & Estabilidade (v0.2.0 — Versão Atual)
- [x] **Suporte Completo a Formatos de Vídeo:** `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.flv`, `.wmv`, `.m4v`, `.3gp`, `.ts`, `.mts`, `.ogv`, `.vob`.
- [x] **Suporte Completo a Formatos de Áudio:** `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.aac`, `.wma`, `.opus`, `.aiff`, `.alac`, `.amr`.
- [x] **Motor Speech-to-Text de Máxima Precisão:**
  - Suporte a `faster-whisper` com modelo `large-v3` por padrão (máxima fidelidade em Português pt-BR) e fallback em cascata para `medium`, `small` e `base`.
  - Fallback automático para `compute_type="int8"` em CPUs sem suporte a float16 no Windows.
  - Suporte ao motor `openai-whisper` nativo (PyTorch).
  - Integração nativa com `google-genai` e `google-generativeai` (Google Gemini 2.0 Flash / 1.5 Flash Multimodal) para transcrição e sumarização com chave de API.
  - Motor de contingência inteligente com `SpeechRecognition` e Google Speech API (`pt-BR`) com fatiamento dinâmico em chunks temporais.
- [x] **Estruturação Temporal (Timestamps) & Métricas:**
  - Segmentação precisa em intervalos `[HH:MM:SS ➔ HH:MM:SS]`.
  - Métricas de fala: total de blocos, total de palavras e velocidade estimada em PPM.
  - Tabela técnica com metadados do arquivo via FFprobe, OpenCV e PyDub (resolução, FPS, duração, codecs de vídeo/áudio, taxa de amostragem, canais, bitrate).
- [x] **Otimização de Desempenho e Memória:**
  - Processamento direto de caminhos de arquivos locais sem clonagem de arquivos gigantes em RAM.
- [x] **Refinamento do Frontend & UX:**
  - Badges dedicados para extensões de vídeo (`MP4`, `MKV`, `AVI`, `MOV`, `WEBM`, etc.).
  - Correção de renderização de tabelas e blocos no parser Markdown standalone (`marked.min.js`).
  - Endpoints REST da API Bottle: `/api/convert`, `/api/get_default_output`, `/api/select_directory`, `/api/select_files`, `/api/open_explorer`, `/api/open_editor`, `/api/save_markdown`.
- [x] **Documentação de Engenharia Completa:** `AGENTS.MD`, `ROADMAP.MD`, `CONTEXT.MD`, `RECOVERY.MD`, `MEMORY.MD`.

---

### 🔮 Fase 3 — Diarização, IA Multimodal & Recursos Avançados (v0.2.5 - v0.3.0)
- [ ] **Diarização de Locutores (Speaker Diarization):** Identificação de múltiplos falantes (ex: *Locutor 1*, *Locutor 2*) usando `pyannote.audio` ou análise de embeddings acústicos.
- [ ] **Extração de Quadros-Chave de Vídeo (Keyframe OCR):** Captura automática de slides e textos embutidos no vídeo com OCR síncrono aos timestamps do áudio.
- [ ] **Sumarização Automática por Capítulos:** Geração automática de sumário e tópicos com marcação de tempo para vídeos longos (palestras, reuniões, aulas).
- [ ] **Suporte a Aceleração de Hardware Avançada:** Detecção automática de CUDA, DirectML e OpenVINO com alternância dinâmica de precisão (FP16 / INT8).

---

### 🌟 Fase 4 — Ecossistema Corporativo & Plugins (v1.0.0)
- [ ] Suporte a plugins externos via MCP (Model Context Protocol).
- [ ] Exportação em múltiplos formatos semânticos (JSON AST, HTML Standalone, PDF estruturado).
- [ ] API Headless em modo servidor CLI/Docker para processamento em lote e esteiras de CI/CD.
