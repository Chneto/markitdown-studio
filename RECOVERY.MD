# 🛠️ RECOVERY.MD — Guia de Recuperação de Falhas e Solução de Problemas

Este documento fornece instruções passo a passo para diagnosticar, mitigar e recuperar a aplicação **MarkItDown Studio** diante de falhas de ambiente, dependências ausentes, conflitos de porta e erros de conversão.

---

## 1. Tabela Rápida de Diagnóstico e Recuperação

| Sintoma / Erro | Causa Mais Provável | Solução Imediata |
| :--- | :--- | :--- |
| **Interface não abre ao executar `iniciar_interface.bat`** | Python não encontrado no PATH ou versão incompatível (< 3.10). | Verifique se o comando `python --version` funciona. Instale o Python 3.10+ marcando *"Add Python to PATH"*. |
| **Porta em uso (`OSError: [Errno 98/10048] Address already in use`)** | Outro processo está ocupando a porta 8080. | O MarkItDown Studio possui busca dinâmica automática em `get_free_port()`, tentando as portas de 8080 até 8130 automaticamente. |
| **Erro ao transcrever vídeo/áudio longo** | Arquivo de áudio excede buffer de memória simples. | O motor `studio/media_engine.py` divide o áudio em chunks temporais e processa incrementalmente. |
| **Ausência do FFMPEG no sistema** | Utilitário `ffmpeg` não instalado no PATH. | O `media_engine.py` utiliza fallbacks em Python puro (`opencv-python`, `wave`, `pydub`, `speech_recognition`) sem travar a conversão. |
| **Falha de float16 no Faster-Whisper no Windows CPU** | CTranslate2 exige INT8 quando executado em CPU sem CUDA. | O sistema possui fallback automático embutido para `device="cpu", compute_type="int8"`. |
| **Falha no OCR (`RapidOCR ONNX not found`)** | Pacote `rapidocr-onnxruntime` não instalado ou modelo corrompido. | O sistema entra em modo de texto puro com aviso no card de diagnóstico. Instale via `pip install rapidocr-onnxruntime`. |
| **Caracteres corrompidos no terminal Windows (Mojibake)** | Prompt de comando configurado para tabela de páginas legada (CP1252/CP850). | O script `iniciar_interface.bat` força `chcp 65001` (UTF-8 universal) na inicialização. |
| **Permissão negada ao salvar o arquivo `.md`** | Pasta de destino protegida (ex: `C:\Program Files` ou `C:\Windows`). | Selecione a pasta *"Documentos"* ou *"Área de Trabalho"* no seletor de pastas da interface. |

---

## 2. Procedimentos Detalhados de Recuperação

### 2.1. Configuração do Modelo de Maior Precisão (Whisper Large-v3 & Google Gemini)
Para obter a máxima fidelidade na transcrição em Português do Brasil (`pt-BR`):
1. **Faster-Whisper com Large-v3:**
   ```bash
   pip install faster-whisper
   ```
   Por padrão, `studio/config.py` tentará carregar `large-v3`. Caso o computador não tenha VRAM/RAM suficiente para o modelo Large, o motor desce automaticamente para `medium` -> `small` -> `base`.
2. **Ativação do Google Gemini Multimodal:**
   Defina sua chave de API no terminal ou variáveis de ambiente do Windows:
   ```cmd
   set GEMINI_API_KEY=sua_chave_aqui
   ```
   O sistema detectará automaticamente a chave ativa no rodapé e utilizará o Gemini 2.0 Flash / 1.5 Flash como motor de transcrição e estruturação.

### 2.2. Recuperação do Motor OCR (RapidOCR)
Se os documentos escaneados ou imagens retornarem *"Nenhum texto detectado"*:
1. Verifique se o módulo `rapidocr-onnxruntime` está acessível no ambiente Python:
   ```bash
   python -c "import rapidocr_onnxruntime; print('OCR OK')"
   ```
2. Caso ocorra erro de importação do runtime ONNX:
   ```bash
   pip install onnxruntime rapidocr-onnxruntime opencv-python pillow
   ```

### 2.3. Resolução de Travamentos em Janelas de Diálogo (Tkinter / Windows)
Se ao clicar em *"Selecionar Arquivos"* ou *"Alterar Pasta"* a aplicação travar:
- O módulo `studio/dialog_service.py` executa o seletor em um processo separado (`subprocess.run([PYTHON_EXE, "-c", ...])`).
- Se houver bloqueio por antivírus ou restrições de subprocesso corporativo, o usuário pode digitar diretamente o caminho absoluto no campo de texto *"Salvar arquivos .md em:"* ou arrastar os arquivos para a zona de Drop.

### 2.4. Limpeza de Cache e Reset de Estado
Se o estado do frontend estiver inconsistente no navegador:
1. No navegador ou janela do Eel, pressione `F12` (DevTools).
2. Vá em **Application** -> **Storage** -> clique em **Clear site data**.
3. Pressione `CTRL + F5` para recarregar a interface limpa.
