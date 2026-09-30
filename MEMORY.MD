# 🧠 MEMORY.MD — Registro de Decisões Arquiteturais e Preferências

Este documento mantém o histórico de decisões técnicas, padrões de design adotados, problemas superados e preferências do usuário para guiar manutenções futuras no **MarkItDown Studio**.

---

## 1. Preferências do Usuário e Requisitos Fundamentais

1. **Modelo de Maior Precisão para Transcrição de Vídeo e Áudio:**
   - O usuário solicitou explicitamente o modelo com maior precisão: configurado `large-v3` como padrão no Whisper (`faster-whisper`), com cascata automática para `medium`, `small` e `base` se houver limitações de VRAM/hardware.
   - Integração com ecossistema Google Gemini Multimodal (`gemini-2.0-flash` / `gemini-1.5-flash`) via `google-genai` / `google.generativeai` quando chave de API estiver presente.
   - Saída estruturada com **timestamps** claros (`[HH:MM:SS]`), métricas de fala (segmentos, palavras, PPM) e tabela técnica detalhada de vídeo/áudio.
2. **Interface em Português do Brasil (pt-BR):**
   - Toda a interface gráfica, mensagens de status, notificações toast e explicações de diagnóstico estão em Português do Brasil claro, profissional e amigável.
3. **Padrão de Versionamento Limpo:**
   - Criação de novas versões em diretórios isolados (`markitdown-0.2.0`) preservando o histórico e garantindo que toda a estrutura de documentação (`AGENTS.MD`, `ROADMAP.MD`, `CONTEXT.MD`, `RECOVERY.MD`, `MEMORY.MD`) esteja devidamente centralizada.

---

## 2. Decisões Arquiteturais Históricas

### 2.1. Adoção da Arquitetura Modular em `studio/`
- **Contexto:** Versões primitivas continham um arquivo monolítico de difícil manutenção.
- **Decisão:** Divisão estrita de responsabilidades:
  - `app.py`: Servidor web Bottle, endpoints REST e bootstrap Eel.
  - `config.py`: Constantes, extensões, configurações e metadados.
  - `converter.py`: Orquestrador universal de conversão com fallbacks.
  - `media_engine.py`: Motor dedicado a vídeo, áudio, extração de metadados e transcrição temporal.
  - `ocr_engine.py`: Gerenciamento do ciclo de vida e thread de background do RapidOCR.
  - `diagnostics.py`: Sistema de análise de causas-raiz de falhas.
  - `dialog_service.py`: Isolamento de diálogos de sistema para evitar deadlocks com o loop gevent.

### 2.2. Estratégia de Fallback em Cascata para Vídeo e Áudio
- **Contexto:** Ambientes heterogêneos exigem resiliência máxima tanto em máquinas sem GPU quanto em servidores de alto desempenho.
- **Decisão:** Implementação de 4 níveis de transcrição:
  1. *Faster-Whisper (Local ONNX/CTranslate2)*: Execução rápida com modelo `large-v3` ou `medium` e fallback de CPU `compute_type="int8"` para prevenir falha de float16 no Windows.
  2. *OpenAI-Whisper (Local Torch)*: Alternativa padrão PyTorch.
  3. *Google Gemini Multimodal (Google Cloud / GenAI Ecosystem)*: Transcrição e enriquecimento multimodal caso chave `GEMINI_API_KEY` ou `GOOGLE_API_KEY` esteja presente.
  4. *SpeechRecognition + Google Speech API (Cloud/Local)*: Transcrição segmentada em chunks com divisão temporal incremental sem consumir memória excessiva.

### 2.3. Otimização de Memória RAM para Vídeos Grandes
- **Contexto:** Carregar vídeos de 1 GB a 4 GB inteiramente em `bytes` de RAM em Python causa picos de memória desnecessários.
- **Decisão:** O `process_conversion` e `process_media_to_markdown` aceitam `file_path` direto do disco, evitando duplicação em memória e gravando apenas o áudio temporário reduzido mono 16kHz.

### 2.4. Resolução de Bugs e Melhorias da v0.2.0
- **Adicionado Endpoint `/api/select_files` e `/api/get_default_output` no `app.py`:** Permite diálogo nativo e detecção dinâmica de pasta padrão.
- **Correção de Parser Markdown Standalone:** Correção de fechamento da tag `<tbody>` no `marked.min.js`.
- **Suporte Abrangente a Codecs e Formatos:** Inclusão de `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.flv`, `.wmv`, `.m4v`, `.3gp`, `.ts`, `.mts`, `.ogv`, `.vob` e áudios `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.aac`, `.wma`, `.opus`, `.aiff`, `.alac`, `.amr`.
- **Extração de Metadados via FFprobe + OpenCV + PyDub:** Captura codec de vídeo, áudio, resolução, FPS, bitrate e taxa de amostragem.
