# 🧠 CONTEXT.MD — Arquitetura do Sistema e Contexto Técnico

Este documento descreve a visão geral da aplicação, stack tecnológica, fluxo de dados, estrutura de diretórios e restrições do sistema operacional do **MarkItDown Studio v0.2.0**.

---

## 1. Visão Geral do Sistema

O **MarkItDown Studio** é uma aplicação desktop local híbrida (Python + HTML5/CSS3/JavaScript) que converte documentos heterogêneos (PDFs, planilhas, apresentações, textos, páginas web, imagens, áudios e vídeos) em arquivos no padrão Markdown (`.md`).

### Pilares de Design
- **Local-First & Privativo:** Todo o processamento padrão ocorre localmente no computador do usuário, sem necessidade de enviar arquivos sensíveis para servidores externos.
- **Zero Configuração Complexa:** Opera com fallbacks inteligentes em cascata quando bibliotecas pesadas ou binários externos (como ffmpeg ou CUDA) não estão presentes.
- **Fidelidade para LLMs:** O Markdown gerado preserva cabeçalhos estruturais, tabelas alinhadas, metadados em blocos estruturados e transcrições sincronizadas com timestamps `[HH:MM:SS ➔ HH:MM:SS]`.

---

## 2. Stack Tecnológica

| Camada | Tecnologia / Biblioteca | Função |
| :--- | :--- | :--- |
| **Interface / Janela** | `Eel` (v0.18.2) + `Bottle` (v0.13.4) | Ponte bidirecional Python <-> JavaScript e servidor HTTP local |
| **Frontend Web** | HTML5 Semântico, CSS3 Moderno (Custom Properties), JavaScript ES6+ Vanilla | Interface reativa, painel duplo, drag & drop, suporte a temas |
| **Markdown Parser** | `marked.min.js` (Standalone Engine) | Renderização em tempo real de Markdown no navegador |
| **Motor de Conversão Base** | `markitdown` (v0.1.7 core) | Pipeline principal para DOCX, XLSX, PPTX, HTML, EPUB, CSV |
| **Processamento de PDF** | `pypdfium2` + `pdfplumber` + `pdfminer.six` | Extração de texto vetorial e rasterização para OCR |
| **Motor OCR** | `rapidocr-onnxruntime` + `Pillow` | Extração de texto de imagens e páginas escaneadas |
| **Motor Audiovisual** | `faster-whisper` (Large-v3/Medium) / `openai-whisper` / `google-genai` / `SpeechRecognition` / `pydub` / `opencv-python` | Extração de áudio, metadados técnicos (FFprobe/OpenCV) e transcrição com timestamps |
| **Diálogos de Sistema** | `tkinter.filedialog` (via subprocesso isolado) | Janelas nativas de seleção de arquivo/pasta no Windows |

---

## 3. Diagrama de Arquitetura e Fluxo de Dados

```
[ Usuário / Navegador Web ]
           |
     (Upload / Drag & Drop / Seleção)
           |
           v
[ Servidor Bottle / Eel (app.py) ]
           |
    +------+----------------------------------------------------------+
    |                                                                 |
    v                                                                 v
[ Rota /api/convert ]                                     [ Rota /api/system_info ]
    |                                                                 |
    v                                                                 v
[ studio/converter.py ] <============================+    [ Coleta de capacidades ]
    |                                                |
    +---> Extensão de Imagem (.png, .jpg, etc.)      |
    |        |                                       |
    |        v                                       |
    |     [ studio/ocr_engine.py ]                   |
    |        |                                       |
    |        +---> RapidOCR ONNX                     |
    |                                                |
    +---> Extensão de Vídeo ou Áudio (.mp4, .mp3)    |
    |        |                                       |
    |        v                                       |
    |     [ studio/media_engine.py ]                 |
    |        |                                       |
    |        +---> Extração de Metadados (FFprobe/CV)|
    |        +---> Demux/Audio (ffmpeg / pydub)      |
    |        +---> Cascata de Transcrição:           |
    |              1. Faster-Whisper (Large-v3)      |
    |              2. OpenAI-Whisper                 |
    |              3. Google Gemini Multimodal       |
    |              4. Google Speech Recognition      |
    |                                                |
    +---> Documentos Gerais (.pdf, .docx, etc.)      |
             |                                       |
             v                                       |
          [ markitdown core / pypdfium2 ]            |
                                                     |
    +------------------------------------------------+
    |
    v
[ Gravação do Arquivo .md (UTF-8) ]
    |
    v
[ Retorno JSON: Markdown, Metadados, Diagnóstico ] ===> [ Atualização da UI e Preview ]
```

---

## 4. Estrutura de Diretórios

```
markitdown-0.2.0/
├── AGENTS.MD                 # Diretrizes e arquitetura de agentes
├── ROADMAP.MD                # Linha do tempo e próximos marcos
├── CONTEXT.MD                # Arquitetura e documentação técnica
├── RECOVERY.MD               # Guia de recuperação de falhas e troubleshooting
├── MEMORY.MD                 # Registro histórico de decisões e preferências
├── README.md                 # Documentação do usuário e instalação
├── LICENSE                   # Licença do projeto (MIT)
├── Dockerfile                # Configuração para execução em contêiner
├── iniciar_interface.bat     # Inicializador gráfico Windows com suporte a UTF-8
├── test_suite.py             # Suíte de testes unitários e de integração
├── studio/                   # Módulo principal da aplicação desktop
│   ├── __init__.py           # Inicializador do pacote studio
│   ├── app.py                # Servidor Bottle, rotas REST e inicializador Eel
│   ├── config.py             # Configurações centralizadas, extensões e versões
│   ├── converter.py          # Orquestrador de conversão universal
│   ├── media_engine.py       # Motor avançado de vídeo, áudio e speech-to-text
│   ├── ocr_engine.py         # Motor OCR com pré-carregamento em background
│   ├── diagnostics.py        # Classificador e diagnosticador amigável de erros
│   ├── dialog_service.py     # Diálogos de sistema em subprocessos isolados
│   └── web/                  # Frontend estático servido pelo Eel
│       ├── index.html        # Estrutura HTML5 da interface
│       ├── css/
│       │   └── style.css     # Estilização completa e temas claro/escuro
│       └── js/
│           ├── app.js        # Lógica de controle do frontend
│           └── marked.min.js # Motor standalone de parse de Markdown
└── packages/                 # Pacotes base do núcleo MarkItDown
    └── markitdown/           # Código-fonte do conversor base
```

---

## 5. Restrições e Padrões de Sistema Operacional (Windows)

1. **Codificação do Terminal e Console:**
   O script `iniciar_interface.bat` executa `chcp 65001 > nul` para forçar UTF-8 no prompt de comando do Windows, prevenindo quebras em caminhos de arquivos com acentos ou caracteres especiais.
2. **Terminações de Linha (CRLF):**
   Arquivos `.bat` no Windows exigem terminações de linha no formato CRLF (`\r\n`). Arquivos de código Python e Markdown utilizam UTF-8 limpo.
3. **Limite de Upload de Arquivos Grandes:**
   `MEMFILE_MAX` está configurado para 1 GB em `bottle.BaseRequest` e `eel.btl.BaseRequest` para suportar grandes arquivos de vídeo e gravações de áudio sem quebra de memória do buffer.
4. **Isolamento de Concorrência Gevent/Tkinter:**
   O Eel utiliza o loop assíncrono do `gevent`. Invocar `tkinter` na mesma thread causa congelamento do processo no Windows. Por isso, todas as chamadas de diálogo (`dialog_service.py`) rodam em um processo Python descartável filho via `subprocess.run()`.
5. **Streaming de Arquivos Locais:**
   O conversor processa caminhos locais diretamente do disco para evitar retenção redundante de arquivos multimídia gigantescos em memória RAM.
