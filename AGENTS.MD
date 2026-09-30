# 🤖 AGENTS.MD — Diretrizes e Arquitetura de Agentes

Este documento define os papéis, responsabilidades, fluxos de trabalho, ferramentas (MCPs, APIs locais e serviços Google) e protocolos de interação para agentes autônomos e desenvolvedores operando no ecossistema **MarkItDown Studio v0.2.0**.

---

## 1. Visão Geral da Arquitetura de Agentes

O MarkItDown Studio opera sob um modelo híbrido com agentes especializados e pipelines modulares. As tarefas são distribuídas entre agentes baseados em papéis para garantir alta precisão na extração de texto, OCR, transcrição audiovisual e geração de Markdown limpo para consumo por LLMs.

```
+-------------------------------------------------------------------+
|                        ORCHESTRATOR AGENT                         |
|  - Roteamento inteligente de tipos de arquivo (MIME / Extensão)  |
|  - Gerenciamento de ciclo de vida e concorrência                  |
|  - Fallback automático e diagnóstico estruturado de falhas        |
+---------------------------------+---------------------------------+
                                  |
         +------------------------+------------------------+
         |                                                 |
+--------v--------+                              +---------v-------+
|  DOCUMENT AGENT |                              |  MEDIA AGENT    |
| (PDF, Office,   |                              | (Vídeo & Áudio  |
|  HTML, EPub,    |                              |  Speech-to-Text |
|  RapidOCR ONNX) |                              |  Whisper / VAD) |
+-----------------+                              +-----------------+
```

---

## 2. Papéis e Responsabilidades dos Agentes

### 2.1. Orchestrator Agent (Agente Orquestrador)
- **Função:** Receber requisições da interface Eel/Bottle ou CLI e determinar o pipeline ótimo de conversão.
- **Responsabilidades:**
  - Validação e sanitização de nomes de arquivos e caminhos no Windows (UTF-8 / Latin-1).
  - Isolamento de execução e prevenção de deadlocks em diálogos e subprocessos.
  - Seleção do motor de fallback (MarkItDown Nativo -> PyPDFium2 -> RapidOCR -> MediaEngine -> Google Ecosystem).
  - Coleta de métricas (tempo de execução, tamanho, contagem de palavras/caracteres).

### 2.2. Media & Speech Agent (Agente Audiovisual)
- **Função:** Transcrição de arquivos de vídeo e áudio com máxima fidelidade.
- **Modelos e Precisão:**
  - **Tier 1 (Alta Precisão Local):** `faster-whisper` com modelo `large-v3` (padrão) com cascata automática para `medium`, `small` e `base`, otimizado para Português Brasileiro (`pt-BR`), VAD filter ativo e beam size = 5.
  - **Tier 2 (Fallback Local Torch):** `openai-whisper` padrão em FP16/FP32.
  - **Tier 3 (Google Gemini Ecosystem):** Transcrição multimodal e sumarização quando `GEMINI_API_KEY` ou `GOOGLE_API_KEY` estiver configurada.
  - **Tier 4 (Google Speech API / SpeechRecognition):** Transcrição segmentada e chunking dinâmico para arquivos longos sem necessidade de download pesado de pesos.
- **Saída:** Markdown estruturado com metadados técnicos (duração, FPS, resolução, taxa de amostragem, codecs), métricas de fala e timestamps por segmento `[HH:MM:SS ➔ HH:MM:SS]`.

### 2.3. Document & Vision Agent (Agente de Documentos e OCR)
- **Função:** Processamento de PDFs complexos, digitalizados e imagens.
- **Motores:**
  - RapidOCR ONNX Runtime para imagens (`.png`, `.jpg`, `.webp`, `.bmp`, `.gif`, `.tiff`, `.svg`).
  - PyPdfium2 para renderização de páginas rasterizadas em PDFs híbridos.
  - Extração de metadados visuais (resolução, canais de cor, EXIF).

### 2.4. Diagnostic & Recovery Agent (Agente de Diagnóstico)
- **Função:** Monitorar exceções em tempo real e fornecer soluções acionáveis.
- **Categorias:** `ENCRYPTED_FILE`, `PERMISSION_DENIED`, `CORRUPT_OR_MALFORMED`, `FFMPEG_MISSING`, `WHISPER_MODEL_ERROR`, `MEMORY_ERROR`, `AUDIO_EXTRACTION_FAILED`.

---

## 3. Protocolos de Ferramentas e MCPs (Model Context Protocol)

Os agentes devem utilizar as ferramentas adequadas para cada escopo de operação:

| Ferramenta / Protocolo | Finalidade | Escopo de Uso |
| :--- | :--- | :--- |
| **File I/O Tools** | Leitura e escrita direta no sistema de arquivos | `write_to_file`, `view_file`, `replace_file_content` |
| **Subprocess Runner** | Execução de utilitários de sistema | Diálogos Tkinter isolados, sondagem ffmpeg / ffprobe |
| **Google GenAI SDK** | Processamento multimodal e sumarização avançada | Modelos Gemini 2.0 Flash / 1.5 Flash para áudio/vídeo longo |
| **RapidOCR ONNX** | OCR local sem necessidade de GPU pesada | Extração textual em imagens e PDFs digitalizados |
| **Faster-Whisper** | Transcrição local ultrarrápida CTranslate2 | Transcrição de alta fidelidade Large-v3 com timestamps |

---

## 4. Regras de Conduta e Padrões de Código dos Agentes

1. **Codificação UTF-8 Obrigatória:** Todas as leituras e gravações de arquivos de texto (.md, .py, .json) devem especificar explicitamente `encoding="utf-8"`.
2. **Resiliência e Fallback Silencioso:** Nenhuma falha de motor individual (ex: ausência de ffmpeg ou falha no download do modelo Whisper) deve abortar a conversão inteira; o sistema deve recorrer ao próximo nível de fallback e registrar o diagnóstico.
3. **Imutabilidade de Arquivos Originais:** O conversor nunca altera ou apaga arquivos de entrada fornecidos pelo usuário.
4. **Isolamento de Interface (UI Responsiveness):** Operações pesadas (OCR, download de modelos, decodificação de vídeo) devem rodar em threads de background ou subprocessos para nunca travar a UI web/Eel.
5. **Streaming de Baixo Consumo de RAM:** Evitar ler arquivos binários de vídeo inteiros em arrays de bytes na memória; utilizar caminhos de arquivo locais quando disponíveis.
