/**
 * MarkItDown Studio v0.2.0 - Frontend Controller
 * Suporte completo a Documentos, Imagens, Vídeos e Áudios com Transcrição Temporal
 */

const state = {
    queue: [],
    selectedId: null,
    outputDir: localStorage.getItem('markitdown_output_dir') || '',
    currentTab: 'formatted',
    isConverting: false,
    theme: localStorage.getItem('markitdown_theme') || 'dark',
    systemInfo: null
};

document.addEventListener('DOMContentLoaded', async () => {
    initTheme();
    setupEventListeners();
    await fetchSystemInfo();
    await loadDefaultOutputDir();
    renderQueue();
    renderInspector();
});

function initTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    updateThemeIcon();
}

function updateThemeIcon() {
    const icon = document.getElementById('themeIcon');
    if (!icon) return;
    if (state.theme === 'dark') {
        icon.innerHTML = '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>';
    } else {
        icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
    }
}

async function fetchSystemInfo() {
    try {
        const response = await fetch('/api/system_info');
        if (response.ok) {
            state.systemInfo = await response.json();
            
            const sysOs = document.getElementById('sysOs');
            if (sysOs) sysOs.textContent = state.systemInfo.os || 'Windows';
            
            const sysPython = document.getElementById('sysPython');
            if (sysPython) sysPython.textContent = `Python ${state.systemInfo.python_version || ''}`;
            
            const sysOcr = document.getElementById('sysOcr');
            if (sysOcr) sysOcr.textContent = `OCR: ${state.systemInfo.ocr_engine || 'RapidOCR'}`;
            
            const sysSpeech = document.getElementById('sysSpeech');
            if (sysSpeech) sysSpeech.textContent = `Speech: ${state.systemInfo.speech_engine || 'Whisper / Google API'}`;
            
            const speechStatus = document.getElementById('speechEngineStatus');
            if (speechStatus && state.systemInfo.speech_engine) {
                speechStatus.textContent = `${state.systemInfo.speech_engine}`;
            }
            
            const studioVer = document.getElementById('studioVersion');
            if (studioVer) studioVer.textContent = `v${state.systemInfo.studio_version || '0.2.0'}`;
        }
    } catch (e) {
        console.warn('Failed to fetch system info:', e);
    }
}

async function loadDefaultOutputDir() {
    const input = document.getElementById('outputDirPathInput');
    if (state.outputDir) {
        if (input) input.value = state.outputDir;
        return;
    }
    try {
        const response = await fetch('/api/get_default_output');
        if (response.ok) {
            const data = await response.json();
            if (data.path) setOutputDir(data.path);
        }
    } catch (e) {
        console.warn("Fetch default output error:", e);
    }
}

function setOutputDir(dir) {
    state.outputDir = dir;
    localStorage.setItem('markitdown_output_dir', dir);
    const input = document.getElementById('outputDirPathInput');
    if (input) input.value = dir;
}

function setupEventListeners() {
    const themeBtn = document.getElementById('themeToggleBtn');
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            state.theme = state.theme === 'dark' ? 'light' : 'dark';
            localStorage.setItem('markitdown_theme', state.theme);
            initTheme();
        });
    }

    const outputInput = document.getElementById('outputDirPathInput');
    if (outputInput) {
        outputInput.addEventListener('change', (e) => {
            const val = e.target.value.trim();
            if (val) {
                setOutputDir(val);
                showToast('Pasta de destino atualizada!', 'success');
            }
        });
    }

    const btnSelectOutputDir = document.getElementById('btnSelectOutputDir');
    if (btnSelectOutputDir) {
        btnSelectOutputDir.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/select_directory', { method: 'POST' });
                if (res.ok) {
                    const data = await res.json();
                    if (data.success && data.path) {
                        setOutputDir(data.path);
                        showToast('Pasta de destino atualizada com sucesso!', 'success');
                    }
                }
            } catch (e) { console.warn(e); }
        });
    }

    const btnOpenOutputDir = document.getElementById('btnOpenOutputDir');
    if (btnOpenOutputDir) {
        btnOpenOutputDir.addEventListener('click', async () => {
            const currentDir = (outputInput ? outputInput.value.trim() : '') || state.outputDir;
            if (!currentDir) {
                showToast('Informe uma pasta de destino válida.', 'warning');
                return;
            }
            try {
                await fetch('/api/open_explorer', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: currentDir })
                });
            } catch (e) {}
        });
    }

    const fileInput = document.getElementById('html5FileInput');
    const folderInput = document.getElementById('html5FolderInput');
    const btnSelectFiles = document.getElementById('btnSelectFiles');
    const btnSelectFolder = document.getElementById('btnSelectFolder');

    if (btnSelectFiles && fileInput) {
        btnSelectFiles.addEventListener('click', () => { fileInput.value = ''; fileInput.click(); });
        fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) handleFileObjects(e.target.files);
        });
    }

    if (btnSelectFolder && folderInput) {
        btnSelectFolder.addEventListener('click', () => { folderInput.value = ''; folderInput.click(); });
        folderInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) handleFileObjects(e.target.files);
        });
    }

    setupDragAndDrop();

    const btnConvertAll = document.getElementById('btnConvertAll');
    if (btnConvertAll) btnConvertAll.addEventListener('click', convertAllPending);

    const btnClearCompleted = document.getElementById('btnClearCompleted');
    if (btnClearCompleted) btnClearCompleted.addEventListener('click', clearCompletedQueue);

    const btnClearAll = document.getElementById('btnClearAll');
    if (btnClearAll) btnClearAll.addEventListener('click', clearAllQueue);

    const tabFormattedBtn = document.getElementById('tabFormattedBtn');
    if (tabFormattedBtn) tabFormattedBtn.addEventListener('click', () => switchTab('formatted'));

    const tabRawBtn = document.getElementById('tabRawBtn');
    if (tabRawBtn) tabRawBtn.addEventListener('click', () => switchTab('raw'));

    const btnCopyMarkdown = document.getElementById('btnCopyMarkdown');
    if (btnCopyMarkdown) btnCopyMarkdown.addEventListener('click', copySelectedMarkdown);

    const btnOpenInExplorer = document.getElementById('btnOpenInExplorer');
    if (btnOpenInExplorer) btnOpenInExplorer.addEventListener('click', openSelectedInExplorer);

    const btnOpenDefaultApp = document.getElementById('btnOpenDefaultApp');
    if (btnOpenDefaultApp) btnOpenDefaultApp.addEventListener('click', openSelectedInDefaultApp);

    const btnSaveEdits = document.getElementById('btnSaveEdits');
    if (btnSaveEdits) btnSaveEdits.addEventListener('click', saveSelectedEdits);

    // Atalhos de Teclado
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && !e.shiftKey && e.key.toLowerCase() === 'o') {
            e.preventDefault();
            if (fileInput) { fileInput.value = ''; fileInput.click(); }
        } else if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'o') {
            e.preventDefault();
            if (folderInput) { folderInput.value = ''; folderInput.click(); }
        } else if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            convertAllPending();
        } else if (e.key === 'Delete' && state.selectedId && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
            removeItem(state.selectedId);
        }
    });
}

function setupDragAndDrop() {
    const dropZone = document.getElementById('dropZone');
    if (!dropZone) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        window.addEventListener(eventName, (e) => { e.preventDefault(); e.stopPropagation(); }, false);
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault(); e.stopPropagation();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        window.addEventListener(eventName, (e) => { e.preventDefault(); e.stopPropagation(); }, false);
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault(); e.stopPropagation();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0) handleFileObjects(dt.files);
    });
}

const FORBIDDEN_EXTS = ['exe', 'dll', 'bat', 'cmd', 'sh', 'msi', 'com', 'vbs'];

function handleFileObjects(filesList) {
    const newItems = [];
    let rejectedCount = 0;

    for (let i = 0; i < filesList.length; i++) {
        const file = filesList[i];
        if (file.name.startsWith('~$') || file.name.startsWith('.')) continue;

        const ext = file.name.includes('.') ? file.name.split('.').pop().toLowerCase() : 'txt';
        if (FORBIDDEN_EXTS.includes(ext)) {
            rejectedCount++;
            continue;
        }

        const baseName = file.name.replace(/\.[^/.]+$/, '');
        newItems.push({
            id: 'file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 7),
            name: file.name,
            baseName: baseName,
            ext: ext.toUpperCase(),
            size: file.size,
            sizeFormatted: formatSize(file.size),
            file: file,
            status: 'pending',
            progress: 0,
            result: null,
            error: null,
            diagnostic: null
        });
    }

    if (rejectedCount > 0) {
        showToast(`Rejeitado(s) ${rejectedCount} arquivo(s) executáveis/binários não suportados.`, 'warning');
    }

    if (newItems.length > 0) {
        addItemsToQueue(newItems);
    }
}

function formatSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function addItemsToQueue(items) {
    let addedCount = 0;
    items.forEach(item => {
        const exists = state.queue.some(existing => existing.name === item.name && existing.size === item.size && existing.status === 'pending');
        if (!exists) {
            state.queue.push(item);
            addedCount++;
        }
    });

    if (addedCount > 0) {
        showToast(`${addedCount} arquivo(s) adicionado(s) à fila!`, 'success');
        renderQueue();
    }
}

function renderQueue() {
    const list = document.getElementById('queueList');
    const counters = document.getElementById('queueCounters');
    if (!list) return;

    if (counters) {
        const success = state.queue.filter(i => i.status === 'success').length;
        const errs = state.queue.filter(i => i.status === 'error').length;
        const pending = state.queue.filter(i => i.status === 'pending' || i.status === 'processing').length;
        
        counters.innerHTML = `
            <span style="color:var(--success); font-weight:600;">${success} ✓</span> | 
            <span style="color:var(--danger); font-weight:600;">${errs} ✗</span> | 
            ${pending} pendentes
        `;
    }

    if (state.queue.length === 0) {
        list.innerHTML = `
            <div class="queue-empty-state" id="queueEmptyState">
                Nenhum arquivo adicionado ainda. Arraste vídeos, áudios ou documentos para a área acima.
            </div>
        `;
        return;
    }

    list.innerHTML = '';

    state.queue.forEach(item => {
        const card = document.createElement('div');
        card.className = `queue-item ${state.selectedId === item.id ? 'active' : ''} ${item.status === 'error' ? 'has-error' : ''}`;
        card.onclick = () => selectItemForPreview(item.id);

        const badgeClass = getBadgeClass(item.ext);
        
        let statusBadgeClass = 'item-progress-fill';
        let statusPercentText = `${item.progress}%`;

        if (item.status === 'success') {
            statusBadgeClass = 'item-progress-fill success';
            statusPercentText = '✓';
        } else if (item.status === 'error') {
            statusBadgeClass = 'item-progress-fill error';
            statusPercentText = '✗';
        }

        card.innerHTML = `
            <div class="queue-item-main">
                <div class="file-ext-badge ${badgeClass}">${escapeHtml(item.ext)}</div>
                <div class="file-details">
                    <div class="file-name" title="${escapeHtml(item.name)}">${escapeHtml(item.name)}</div>
                    <div class="file-meta">
                        <span>${item.sizeFormatted}</span>
                        ${item.result ? `<span>• Saída: ${escapeHtml(item.result.outputName)}</span>` : ''}
                        ${item.status === 'error' ? `<span style="color: var(--danger); font-weight: 600;">• Clique para ver diagnóstico</span>` : ''}
                    </div>
                </div>
            </div>

            <div class="queue-item-status">
                <div class="item-progress-wrapper" id="progressWrapper_${item.id}">
                    <div class="item-progress-track">
                        <div class="${statusBadgeClass}" id="progressFill_${item.id}" style="width: ${item.progress}%"></div>
                    </div>
                    <span class="item-progress-percent" id="progressPercent_${item.id}">${statusPercentText}</span>
                </div>
            </div>

            <div class="queue-item-actions" onclick="event.stopPropagation()">
                ${item.status === 'pending' || item.status === 'error' ? `
                    <button class="btn btn-primary btn-sm" id="btnConvert_${item.id}" onclick="convertSingle('${item.id}')" title="Converter">
                        Converter
                    </button>
                ` : ''}
                ${item.status === 'success' ? `
                    <button class="btn btn-secondary btn-sm" onclick="selectItemForPreview('${item.id}')" title="Visualizar Markdown">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                            <circle cx="12" cy="12" r="3"></circle>
                        </svg>
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="convertSingle('${item.id}')" title="Reconverter">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="23 4 23 10 17 10"></polyline>
                            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                        </svg>
                    </button>
                ` : ''}
                <button class="btn btn-danger-ghost btn-sm" onclick="removeItem('${item.id}')" title="Remover da lista">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
        `;
        list.appendChild(card);
    });
}

function updateItemProgress(id, percent, status) {
    const item = state.queue.find(i => i.id === id);
    if (item) {
        item.progress = percent;
        item.status = status;
    }

    const fill = document.getElementById(`progressFill_${id}`);
    const text = document.getElementById(`progressPercent_${id}`);
    const btn = document.getElementById(`btnConvert_${id}`);

    if (fill && text) {
        fill.style.width = `${percent}%`;
        
        if (status === 'success') {
            fill.className = 'item-progress-fill success';
            text.textContent = '✓';
            if (btn) btn.style.display = 'none';
        } else if (status === 'error') {
            fill.className = 'item-progress-fill error';
            text.textContent = '✗';
        } else {
            fill.className = 'item-progress-fill';
            text.textContent = `${percent}%`;
            if (btn) btn.disabled = true;
        }
    }
}

function getBadgeClass(ext) {
    ext = (ext || '').toLowerCase();
    if (['mp4', 'mkv', 'avi', 'mov', 'webm', 'flv', 'wmv', 'm4v'].includes(ext)) return 'ext-mp4';
    if (['mp3', 'wav', 'm4a', 'ogg', 'flac', 'aac', 'wma', 'opus'].includes(ext)) return 'ext-mp3';
    if (ext === 'pdf') return 'ext-pdf';
    if (['docx', 'doc', 'rtf', 'odt'].includes(ext)) return 'ext-docx';
    if (['xlsx', 'xls', 'csv', 'tsv', 'ods'].includes(ext)) return 'ext-xlsx';
    if (['pptx', 'ppt', 'odp'].includes(ext)) return 'ext-pptx';
    if (['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif'].includes(ext)) return 'ext-jpg';
    return 'ext-data';
}

function removeItem(id) {
    state.queue = state.queue.filter(item => item.id !== id);
    if (state.selectedId === id) state.selectedId = null;
    renderQueue();
    renderInspector();
}

function clearCompletedQueue() {
    state.queue = state.queue.filter(item => item.status !== 'success');
    if (state.selectedId && !state.queue.some(item => item.id === state.selectedId)) {
        state.selectedId = null;
    }
    renderQueue();
    renderInspector();
}

function clearAllQueue() {
    state.queue = [];
    state.selectedId = null;
    state.isConverting = false;
    updateConvertingButtonsState(false);

    const progressBarContainer = document.getElementById('progressBarContainer');
    if (progressBarContainer) progressBarContainer.style.display = 'none';

    renderQueue();
    renderInspector();
}

function executeConversion(item, outputDir) {
    return new Promise(async (resolve) => {
        updateItemProgress(item.id, 10, 'processing');

        const formData = new FormData();
        formData.append('output_dir', outputDir);
        formData.append('file_name', item.name);

        if (item.file) {
            formData.append('file', item.file, item.name);
        } else if (item.path) {
            formData.append('file_path', item.path);
        }

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/convert', true);

        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const uploadPercent = Math.round((e.loaded / e.total) * 45) + 10;
                updateItemProgress(item.id, Math.min(uploadPercent, 55), 'processing');
            }
        };

        let progressInterval = setInterval(() => {
            if (item.status === 'processing' && item.progress < 92) {
                updateItemProgress(item.id, item.progress + 4, 'processing');
            }
        }, 300);

        xhr.onload = () => {
            clearInterval(progressInterval);
            if (xhr.status === 200) {
                try {
                    const res = JSON.parse(xhr.responseText);
                    if (res && res.success) {
                        updateItemProgress(item.id, 100, 'success');
                        item.result = res;
                        item.error = null;
                        item.diagnostic = null;
                        renderQueue();
                        selectItemForPreview(item.id);
                        resolve({ success: true, item: item });
                    } else {
                        updateItemProgress(item.id, 100, 'error');
                        item.error = res ? res.error : 'Erro na conversão';
                        item.diagnostic = res ? res.diagnostic : null;
                        renderQueue();
                        selectItemForPreview(item.id);
                        resolve({ success: false, item: item, error: item.error });
                    }
                } catch (err) {
                    updateItemProgress(item.id, 100, 'error');
                    resolve({ success: false, item: item, error: 'Resposta inválida do servidor' });
                }
            } else {
                updateItemProgress(item.id, 100, 'error');
                resolve({ success: false, item: item, error: `Erro HTTP ${xhr.status}` });
            }
        };

        xhr.onerror = () => {
            clearInterval(progressInterval);
            updateItemProgress(item.id, 100, 'error');
            resolve({ success: false, item: item, error: 'Falha de comunicação com o servidor' });
        };

        xhr.send(formData);
    });
}

async function convertSingle(id) {
    const item = state.queue.find(i => i.id === id);
    if (!item || state.isConverting) return;

    const outputInput = document.getElementById('outputDirPathInput');
    const currentDest = (outputInput ? outputInput.value.trim() : '') || state.outputDir;
    if (!currentDest) {
        showToast('Informe a pasta de destino antes de converter.', 'warning');
        return;
    }

    const result = await executeConversion(item, currentDest);
    if (result.success) {
        showToast(`Convertido com sucesso: ${item.name}`, 'success');
    } else {
        showToast(`Falha ao converter ${item.name}.`, 'error');
    }
}

async function convertAllPending() {
    const pendingItems = state.queue.filter(i => i.status === 'pending' || i.status === 'error');
    if (pendingItems.length === 0) return;

    const outputInput = document.getElementById('outputDirPathInput');
    const currentDest = (outputInput ? outputInput.value.trim() : '') || state.outputDir;
    if (!currentDest) {
        showToast('Configure a pasta de destino.', 'warning');
        return;
    }

    state.isConverting = true;
    updateConvertingButtonsState(true);

    const progressBarContainer = document.getElementById('progressBarContainer');
    const progressBar = document.getElementById('progressBar');
    if (progressBarContainer && progressBar) {
        progressBarContainer.style.display = 'block';
        progressBar.style.width = '0%';
    }

    let completedCount = 0;
    let successCount = 0;
    const total = pendingItems.length;

    for (const item of pendingItems) {
        const result = await executeConversion(item, currentDest);
        if (result.success) successCount++;
        completedCount++;
        if (progressBar) progressBar.style.width = `${Math.round((completedCount / total) * 100)}%`;
    }

    state.isConverting = false;
    updateConvertingButtonsState(false);
    setTimeout(() => {
        if (progressBarContainer) progressBarContainer.style.display = 'none';
    }, 1200);

    if (successCount === total) showToast(`Todos os ${total} arquivos foram convertidos com sucesso!`, 'success');
    else showToast(`Lote finalizado: ${successCount} de ${total} convertidos.`, 'warning');
}

function updateConvertingButtonsState(isConverting) {
    const btnConvertAll = document.getElementById('btnConvertAll');
    if (btnConvertAll) btnConvertAll.disabled = isConverting;
}

function selectItemForPreview(id) {
    state.selectedId = id;
    renderQueue();
    renderInspector();
}

function renderInspector() {
    const item = state.queue.find(i => i.id === state.selectedId);
    const emptyState = document.getElementById('inspectorEmptyState');
    const formattedView = document.getElementById('formattedView');
    const rawView = document.getElementById('rawView');
    const diagnosticView = document.getElementById('diagnosticView');
    const actionsBar = document.getElementById('inspectorActionsBar');
    const tabsGroup = document.getElementById('inspectorTabsGroup');
    const fileNameEl = document.getElementById('inspectorFileName');
    const extBadgeEl = document.getElementById('inspectorExtBadge');

    if (!item) {
        if (emptyState) emptyState.style.display = 'flex';
        if (formattedView) formattedView.style.display = 'none';
        if (rawView) rawView.style.display = 'none';
        if (diagnosticView) { diagnosticView.style.display = 'none'; diagnosticView.innerHTML = ''; }
        if (actionsBar) actionsBar.style.display = 'none';
        if (tabsGroup) tabsGroup.style.display = 'none';
        if (fileNameEl) fileNameEl.textContent = 'Nenhum documento selecionado';
        if (extBadgeEl) {
            extBadgeEl.textContent = 'MD';
            extBadgeEl.className = 'file-ext-badge ext-data';
        }
        return;
    }

    if (fileNameEl) fileNameEl.textContent = item.name;
    if (extBadgeEl) {
        extBadgeEl.textContent = item.ext;
        extBadgeEl.className = `file-ext-badge ${getBadgeClass(item.ext)}`;
    }

    if (item.status === 'error') {
        if (emptyState) emptyState.style.display = 'none';
        if (formattedView) formattedView.style.display = 'none';
        if (rawView) rawView.style.display = 'none';
        if (actionsBar) actionsBar.style.display = 'none';
        if (tabsGroup) tabsGroup.style.display = 'none';
        
        if (diagnosticView) {
            diagnosticView.style.display = 'flex';
            const diag = item.diagnostic || { title: "Erro de Conversão", explanation: item.error, category: "ERROR", suggestion: "Verifique o formato do arquivo." };
            diagnosticView.innerHTML = `
                <div class="diagnostic-card">
                    <div class="diagnostic-header">
                        <div class="diagnostic-header-main">
                            <div class="diagnostic-icon">⚠️</div>
                            <div>
                                <div class="diagnostic-title">${escapeHtml(diag.title)}</div>
                                <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">Arquivo: ${escapeHtml(item.name)}</div>
                            </div>
                        </div>
                        <span class="diagnostic-category-badge">${escapeHtml(diag.category)}</span>
                    </div>
                    <div class="diagnostic-section">
                        <div class="diagnostic-section-title">📌 O que aconteceu</div>
                        <div class="diagnostic-text">${escapeHtml(diag.explanation)}</div>
                    </div>
                    <div class="diagnostic-section">
                        <div class="diagnostic-section-title">💡 Como resolver</div>
                        <div class="diagnostic-suggestion-box">${escapeHtml(diag.suggestion)}</div>
                    </div>
                </div>
            `;
        }
        return;
    }

    if (item.status === 'success' && item.result) {
        if (emptyState) emptyState.style.display = 'none';
        if (diagnosticView) diagnosticView.style.display = 'none';
        if (actionsBar) actionsBar.style.display = 'flex';
        if (tabsGroup) tabsGroup.style.display = 'flex';

        if (fileNameEl) fileNameEl.textContent = item.result.outputName;
        
        const statWords = document.getElementById('statWords');
        if (statWords) statWords.textContent = `${item.result.wordCount || 0} palavras`;
        
        const statChars = document.getElementById('statChars');
        if (statChars) statChars.textContent = `${item.result.charCount || 0} caracteres`;
        
        const statSize = document.getElementById('statSize');
        if (statSize) statSize.textContent = item.result.outputSize || '0 KB';
        
        const statDuration = document.getElementById('statDuration');
        if (statDuration) statDuration.textContent = `${item.result.duration || 0}s`;

        const markdown = item.result.markdown || '';
        if (rawView) rawView.value = markdown;

        if (formattedView) {
            if (window.marked && window.marked.parse) {
                formattedView.innerHTML = window.marked.parse(markdown);
            } else {
                formattedView.innerHTML = `<pre>${escapeHtml(markdown)}</pre>`;
            }
        }

        switchTab(state.currentTab);
        return;
    }

    if (emptyState) emptyState.style.display = 'flex';
    if (formattedView) formattedView.style.display = 'none';
    if (rawView) rawView.style.display = 'none';
    if (diagnosticView) diagnosticView.style.display = 'none';
    if (actionsBar) actionsBar.style.display = 'none';
    if (tabsGroup) tabsGroup.style.display = 'none';
}

function switchTab(tab) {
    state.currentTab = tab;
    const formattedBtn = document.getElementById('tabFormattedBtn');
    const rawBtn = document.getElementById('tabRawBtn');
    const formattedView = document.getElementById('formattedView');
    const rawView = document.getElementById('rawView');
    const btnSaveEdits = document.getElementById('btnSaveEdits');

    if (tab === 'formatted') {
        if (formattedBtn) formattedBtn.classList.add('active');
        if (rawBtn) rawBtn.classList.remove('active');
        if (formattedView) formattedView.style.display = 'block';
        if (rawView) rawView.style.display = 'none';
        if (btnSaveEdits) btnSaveEdits.style.display = 'none';
        if (formattedView && rawView && window.marked && window.marked.parse) {
            formattedView.innerHTML = window.marked.parse(rawView.value);
        }
    } else {
        if (rawBtn) rawBtn.classList.add('active');
        if (formattedBtn) formattedBtn.classList.remove('active');
        if (formattedView) formattedView.style.display = 'none';
        if (rawView) rawView.style.display = 'block';
        if (btnSaveEdits) btnSaveEdits.style.display = 'inline-flex';
    }
}

async function copySelectedMarkdown() {
    const rawView = document.getElementById('rawView');
    if (!rawView || !rawView.value) return;
    try {
        await navigator.clipboard.writeText(rawView.value);
        showToast('Markdown copiado para a área de transferência!', 'success');
    } catch (e) {
        showToast('Não foi possível copiar automaticamente.', 'warning');
    }
}

async function openSelectedInExplorer() {
    const item = state.queue.find(i => i.id === state.selectedId);
    if (item && item.result) {
        await fetch('/api/open_explorer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: item.result.outputPath })
        });
    }
}

async function openSelectedInDefaultApp() {
    const item = state.queue.find(i => i.id === state.selectedId);
    if (item && item.result) {
        await fetch('/api/open_editor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: item.result.outputPath })
        });
    }
}

async function saveSelectedEdits() {
    const item = state.queue.find(i => i.id === state.selectedId);
    const rawView = document.getElementById('rawView');
    if (!item || !item.result || !rawView) return;

    try {
        const res = await fetch('/api/save_markdown', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: item.result.outputPath, content: rawView.value })
        });
        if (res.ok) {
            const data = await res.json();
            if (data.success) {
                item.result.markdown = rawView.value;
                item.result.charCount = data.charCount;
                item.result.wordCount = data.wordCount;
                item.result.outputSize = data.outputSize;
                showToast('Alterações salvas com sucesso no arquivo .md!', 'success');
                renderInspector();
            }
        }
    } catch (e) {
        showToast('Falha ao salvar edições.', 'error');
    }
}

function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toastSlideOut 0.25s ease forwards';
        setTimeout(() => toast.remove(), 250);
    }, duration);
}

function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
