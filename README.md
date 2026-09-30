<div align="center">

# 🚀 MarkItDown Studio v0.2.0

### *Estação de Trabalho Universal de Conversão de Documentos, Mídias e Imagens para Markdown*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Faster-Whisper](https://img.shields.io/badge/Speech--to--Text-Whisper%20Large--v3-orange.svg)](https://github.com/SYSTRAN/faster-whisper)
[![RapidOCR](https://img.shields.io/badge/OCR-RapidOCR%20ONNX-blueviolet.svg)](https://github.com/RapidAI/RapidOCR)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini%202.0%20Flash-4285F4.svg)](https://ai.google.dev/)
[![GitHub Pages](https://img.shields.io/badge/Web-GitHub%20Pages%20Live-success.svg)](#-live-demo--github-pages)

---

**O MarkItDown Studio** é uma interface gráfica moderna, desktop e 100% local desenvolvida para transformar qualquer arquivo corporativo, jurídico, técnico ou audiovisual em **Markdown semântico e estruturado**, perfeitamente otimizado para ingestão por Modelos de Linguagem Grande (**LLMs, RAG, Claude, ChatGPT, Gemini**).

[✨ Funcionalidades](#-funcionalidades) • [📥 Instalação](#-instalação-rápida) • [🚀 Como Usar](#-como-usar) • [🎥 Degravação de Vídeos](#-degravação-de-vídeo-e-áudio) • [📑 Arquitetura](#-arquitetura) • [🗺️ Roadmap](#-documentação-de-engenharia)

---

</div>

## 🌟 Destaques da Versão 0.2.0

- 🎙️ **Degravação Inteligente de Vídeo & Áudio (Speech-to-Text):**
  - Motor Whisper **Large-v3** (máxima precisão em pt-BR) com cascata automática para `medium`, `small` e `base`.
  - Timestamps precisos `[00:01:25 ➔ 00:01:32]`, métricas de fala (palavras, velocidade em PPM) e tabela técnica de metadados.
  - Integração nativa com **Google Gemini 2.0 Flash Multimodal** e **Google Speech API**.
- 🔍 **OCR Neural Offline de Alta Velocidade:**
  - `RapidOCR` baseado em redes neurais ONNX com pré-carregamento em background para conversões instantâneas.
  - Multi-estágio inteligente para PDFs (extrai texto nativo, detecta páginas digitalizadas e aplica OCR página a página).
- 💻 **Interface Desktop Moderna (Eel + HTML5/CSS3):**
  - Temas Escuro e Claro com transições suaves.
  - Arraste e solte (*Drag & Drop*) inteligente que se compacta ao receber documentos.
  - Visualização lado a lado: Markdown renderizado em HTML formatado vs. Editor de código puro.
  - Atalhos de teclado rápidos (`Ctrl+O`, `Ctrl+Shift+O`, `Ctrl+Enter`, `Delete`).
  - Suporte a seleção de pasta de destino com abertura direta no Windows Explorer.

---

## 📂 Formatos Suportados

| Categoria | Extensões Suportadas | Motor Principal |
| :--- | :--- | :--- |
| **🎥 Vídeos** | `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.flv`, `.wmv`, `.m4v`, `.3gp`, `.ts`, `.mts`, `.ogv`, `.vob` | Faster-Whisper Large-v3 / Gemini / FFprobe |
| **🎵 Áudios** | `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.aac`, `.wma`, `.opus`, `.aiff`, `.alac`, `.amr` | Faster-Whisper / Google Speech API / PyDub |
| **📑 Documentos** | `.pdf` (digital ou escaneado), `.docx`, `.doc`, `.txt`, `.epub`, `.msg`, `.rtf` | MarkItDown / PyPDFium2 / RapidOCR |
| **📊 Planilhas & Dados**| `.xlsx`, `.xls`, `.csv`, `.tsv`, `.json`, `.xml`, `.yaml` | OpenPyXL / Pandas / Parsers estruturados |
| **📊 Apresentações** | `.pptx`, `.ppt` | Python-PPTX / XML parser |
| **🖼️ Imagens** | `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.gif`, `.tiff` | RapidOCR ONNX / Pillow (Metadados EXIF) |
| **🌐 Web & Feeds** | `.html`, `.htm`, `.xhtml`, `.rss`, `.atom` | BeautifulSoup / Markdownify |
| **📦 Arquivos** | `.zip` | Descompactação recursiva e conversão em lote |

---

## 📥 Instalação Rápida

### 1. Pré-requisitos
- **Python 3.10 ou superior** instalado no seu sistema.
- **Git** para clonar o repositório.
- *(Opcional, mas recomendado)* **FFmpeg** instalado para manipulação avançada de codecs de vídeo/áudio.

### 2. Clonar o Repositório
```bash
git clone https://github.com/SEU_USUARIO/markitdown-studio.git
cd markitdown-studio
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

---

## 🚀 Como Usar

### No Windows (1-Clique):
Basta dar dois cliques no arquivo:
```cmd
iniciar_interface.bat
```

### Via Terminal:
```bash
python -m studio.app
```

O navegador abrirá automaticamente em uma janela desktop em `http://localhost:8080/index.html`.

---

## 🎥 Degravação de Vídeo e Áudio

Ao arrastar um vídeo (ex: gravação de reunião, audiência, depoimento, palestra ou aula), o MarkItDown Studio gera um arquivo `.md` contendo:

```markdown
# 🎥 Apresentacao_Reuniao.mp4

## ℹ️ Informações e Metadados Técnicos
| Propriedade | Valor |
|---|---|
| **Formato / Contêiner** | MP4 |
| **Duração** | 00:04:12 (252.0s) |
| **Resolução / Dimensões** | 1920 x 1080 px |
| **Taxa de Quadros (FPS)** | 30.00 fps |
| **Codecs** | Vídeo: h264 \| Áudio: aac |
| **Taxa de Amostragem de Áudio**| 48000 Hz (2 canais) |
| **Motor de Transcrição** | Faster-Whisper Large-v3 (pt-BR) |

---

## 📊 Métricas de Fala
- **Total de Blocos de Fala:** 18 segmentos
- **Total de Palavras:** 542 palavras
- **Velocidade Estimada:** 129 PPM (Palavras por Minuto)

---

## 🎙️ Transcrição Detalhada com Marcação de Tempo (Timestamps)
- `[00:00:02 ➔ 00:00:08]` Bom dia a todos os presentes, iniciamos agora a nossa reunião de alinhamento trimestral.
- `[00:00:09 ➔ 00:00:18]` Gostaria de apresentar os resultados operacionais do projeto e os avanços na arquitetura do sistema.
- `[00:00:19 ➔ 00:00:32]` Conforme planejado no roadmap, todas as metas de estabilidade e segurança foram atingidas.

---

## 📝 Texto Integral Contínuo
Bom dia a todos os presentes, iniciamos agora a nossa reunião de alinhamento trimestral. Gostaria de apresentar os resultados operacionais do projeto e os avanços na arquitetura do sistema. Conforme planejado no roadmap, todas as metas de estabilidade e segurança foram atingidas...
```

---

## ⌨️ Atalhos de Teclado

| Atalho | Ação |
| :--- | :--- |
| `Ctrl + O` | Abrir caixa de diálogo para selecionar arquivos |
| `Ctrl + Shift + O` | Abrir caixa de diálogo para selecionar pasta inteira |
| `Ctrl + Enter` | Iniciar a conversão de todos os documentos pendentes |
| `Delete` | Remover o documento selecionado da fila |

---

## 🏗️ Arquitetura do Projeto

```
markitdown-studio/
├── .github/
│   └── workflows/          # GitHub Actions (CI & GitHub Pages)
├── docs/                   # Landing Page e Documentação Web (GitHub Pages)
│   ├── index.html
│   ├── style.css
│   └── script.js
├── studio/                 # Pacote Principal da Aplicação
│   ├── app.py              # Servidor REST Bottle e ponte WebSocket Eel
│   ├── config.py           # Configurações centralizadas e extensões
│   ├── converter.py        # Orquestrador universal de conversão
│   ├── media_engine.py     # Motor Speech-to-Text (Whisper Large-v3 & Gemini)
│   ├── ocr_engine.py       # Motor RapidOCR ONNX com pré-aquecimento
│   ├── diagnostics.py      # Diagnóstico estruturado de erros
│   ├── dialog_service.py   # Caixas de diálogo nativas Tkinter em subprocesso
│   └── web/                # Frontend da Interface Desktop
│       ├── index.html
│       ├── css/style.css
│       └── js/app.js
├── AGENTS.MD               # Diretrizes e arquitetura de agentes autônomos
├── ROADMAP.MD              # Linha do tempo e planejamento de versões
├── CONTEXT.MD              # Contexto técnico, stack e fluxos de dados
├── RECOVERY.MD             # Manual de recuperação e troubleshooting
├── MEMORY.MD               # Registro histórico de decisões e preferências
├── test_suite.py           # Suíte de testes automatizados (14 testes)
├── iniciar_interface.bat   # Inicializador nativo do Windows
└── requirements.txt        # Dependências do projeto
```

---

## 📑 Documentação de Engenharia

Para mais detalhes sobre arquitetura e diretrizes, consulte os documentos dedicados:
- 🤖 [AGENTS.MD](AGENTS.MD) — Diretrizes de agentes e protocolos de ferramentas.
- 🗺️ [ROADMAP.MD](ROADMAP.MD) — Fases de desenvolvimento e novas funcionalidades.
- 🏛️ [CONTEXT.MD](CONTEXT.MD) — Detalhamento técnico da arquitetura.
- 🩺 [RECOVERY.MD](RECOVERY.MD) — Solução de problemas comuns e contingência.
- 🧠 [MEMORY.MD](MEMORY.MD) — Decisões de design e histórico de correções.

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [`LICENSE`](LICENSE) para obter mais informações.

<div align="center">

Desenvolvido com foco em alta precisão, privacidade e produtividade local.

</div>
