document.addEventListener('DOMContentLoaded', () => {
    // --- Elements ---
    const providerSelect = document.getElementById('provider-select');
    const saveConfigBtn = document.getElementById('save-config-btn');
    
    // Config Inputs
    const openaiKey = document.getElementById('openai-key');
    const openaiModel = document.getElementById('openai-model');
    const geminiKey = document.getElementById('gemini-key');
    const geminiModel = document.getElementById('gemini-model');
    const ollamaUrl = document.getElementById('ollama-url');
    const ollamaModel = document.getElementById('ollama-model');
    const openrouterKey = document.getElementById('openrouter-key');
    const openrouterModel = document.getElementById('openrouter-model');

    // Upload
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const uploadStatus = document.getElementById('upload-status');
    const clearMemBtn = document.getElementById('clear-mem-btn');

    // Chat
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    
    // UI Panels
    const emptyState = document.getElementById('empty-state');
    const chatWrapper = document.getElementById('chat-wrapper');
    const settingsModal = document.getElementById('settings-modal');
    const openSettingsBtn = document.getElementById('open-settings-btn');
    const closeModalBtn = document.getElementById('close-modal-btn');

    // PDF Viewer
    const pdfContainer = document.getElementById('pdf-container');
    const pdfTitle = document.getElementById('pdf-title');
    const pdfViewerWrapper = document.getElementById('pdf-viewer-wrapper');
    const pageNumSpan = document.getElementById('page-num');
    const pageCountSpan = document.getElementById('page-count');
    const askSelectionBtn = document.getElementById('ask-selection-btn');
    const resizer = document.getElementById('dragMe');
    const leftPane = document.querySelector('.left-pane');
    const rightPane = document.querySelector('.right-pane');

    // State
    let chatHistory = [];
    let isConfigLoaded = false;
    let pdfDoc = null;
    let pageNum = 1;
    let selectedText = "";

    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';

    // --- Modal Logic ---
    openSettingsBtn.addEventListener('click', () => settingsModal.classList.add('show'));
    closeModalBtn.addEventListener('click', () => settingsModal.classList.remove('show'));
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) settingsModal.classList.remove('show');
    });

    // --- Resizer Logic ---
    let isResizing = false;
    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        resizer.classList.add('resizing');
        document.body.style.cursor = 'col-resize';
        e.preventDefault();
    });
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const newWidth = e.clientX - leftPane.getBoundingClientRect().left;
        if (newWidth > 300 && newWidth < window.innerWidth - 300) {
            leftPane.style.flex = 'none';
            leftPane.style.width = `${newWidth}px`;
        }
    });
    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            resizer.classList.remove('resizing');
            document.body.style.cursor = 'default';
        }
    });

    // --- Provider Switching ---
    providerSelect.addEventListener('change', (e) => {
        document.querySelectorAll('.provider-settings').forEach(el => el.classList.remove('active'));
        document.getElementById(`${e.target.value}-settings`).classList.add('active');
        if (isConfigLoaded) fetchModels();
    });

    // --- Initialization ---
    async function loadConfig() {
        try {
            const res = await fetch('/api/config');
            const data = await res.json();
            
            providerSelect.value = data.active_provider || 'openai';
            document.querySelectorAll('.provider-settings').forEach(el => el.classList.remove('active'));
            document.getElementById(`${providerSelect.value}-settings`).classList.add('active');

            if (data.openai) {
                openaiKey.value = data.openai.api_key || '';
                if (data.openai.model) {
                    const opt = document.createElement('option');
                    opt.value = data.openai.model;
                    opt.text = data.openai.model;
                    openaiModel.add(opt);
                    openaiModel.value = data.openai.model;
                }
            }
            if (data.gemini) {
                geminiKey.value = data.gemini.api_key || '';
                if (data.gemini.model) geminiModel.value = data.gemini.model;
            }
            if (data.ollama) {
                ollamaUrl.value = data.ollama.base_url || 'http://localhost:11434';
                if (data.ollama.model) {
                    const opt = document.createElement('option');
                    opt.value = data.ollama.model;
                    opt.text = data.ollama.model;
                    ollamaModel.add(opt);
                    ollamaModel.value = data.ollama.model;
                }
            }
            if (data.openrouter) {
                openrouterKey.value = data.openrouter.api_key || '';
                if (data.openrouter.model) {
                    const opt = document.createElement('option');
                    opt.value = data.openrouter.model;
                    opt.text = data.openrouter.model;
                    openrouterModel.add(opt);
                    openrouterModel.value = data.openrouter.model;
                }
            }
            
            isConfigLoaded = true;
            fetchModels();
            checkDocuments();
        } catch (e) {
            console.error("Failed to load config", e);
        }
    }

    async function fetchModels() {
        const provider = providerSelect.value;
        let url = `/api/models?provider=${provider}`;
        if (provider === 'openai') {
            url += `&api_key=${openaiKey.value}`;
        } else if (provider === 'ollama') {
            url += `&base_url=${encodeURIComponent(ollamaUrl.value)}`;
        } else if (provider === 'openrouter') {
            url += `&api_key=${openrouterKey.value}`;
        }

        try {
            const res = await fetch(url);
            const models = await res.json();
            let selectEl = null;
            if (provider === 'openai') selectEl = openaiModel;
            if (provider === 'ollama') selectEl = ollamaModel;
            if (provider === 'openrouter') selectEl = openrouterModel;
            
            if (selectEl && Array.isArray(models) && models.length > 0) {
                const currentVal = selectEl.value;
                selectEl.innerHTML = '';
                models.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.text = m;
                    selectEl.add(opt);
                });
                if (models.includes(currentVal)) {
                    selectEl.value = currentVal;
                }
            }
        } catch (e) {
            console.error("Failed to fetch models", e);
        }
    }

    saveConfigBtn.addEventListener('click', async () => {
        saveConfigBtn.textContent = 'Saving...';
        const config = {
            active_provider: providerSelect.value,
            openai: {
                api_key: openaiKey.value,
                model: openaiModel.value || 'gpt-4o-mini',
                base_url: ''
            },
            gemini: {
                api_key: geminiKey.value,
                model: geminiModel.value || 'gemini-1.5-flash'
            },
            ollama: {
                base_url: ollamaUrl.value || 'http://localhost:11434',
                model: ollamaModel.value || ''
            },
            openrouter: {
                api_key: openrouterKey.value,
                model: openrouterModel.value || 'google/gemini-2.5-flash',
                base_url: 'https://openrouter.ai/api/v1'
            }
        };

        try {
            await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config })
            });
            saveConfigBtn.textContent = 'Saved!';
            saveConfigBtn.style.backgroundColor = 'var(--success)';
            setTimeout(() => {
                saveConfigBtn.textContent = 'Save Settings';
                saveConfigBtn.style.backgroundColor = '';
                settingsModal.classList.remove('show');
            }, 1000);
            fetchModels();
        } catch (e) {
            alert('Failed to save config');
            saveConfigBtn.textContent = 'Save Settings';
        }
    });

    // --- File Upload ---
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleUpload(e.dataTransfer.files);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleUpload(e.target.files);
        }
    });

    async function handleUpload(files) {
        const formData = new FormData();
        let valid = false;
        for (let i = 0; i < files.length; i++) {
            if (files[i].type === 'application/pdf') {
                formData.append('files', files[i]);
                valid = true;
            }
        }
        if (!valid) {
            uploadStatus.textContent = 'Please select PDF files.';
            uploadStatus.style.color = 'var(--error)';
            return;
        }

        uploadStatus.textContent = 'Uploading and processing...';
        uploadStatus.style.color = 'var(--text-main)';

        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (res.ok) {
                uploadStatus.textContent = `Processed ${data.files} files into ${data.chunks} chunks.`;
                uploadStatus.style.color = 'var(--success)';
                sendBtn.disabled = false;
                if (data.files > 0) {
                    loadPDF('/uploads/' + files[0].name, files[0].name);
                }
            } else {
                throw new Error(data.detail || 'Upload failed');
            }
        } catch (e) {
            uploadStatus.textContent = `Error: ${e.message}`;
            uploadStatus.style.color = 'var(--error)';
        }
    }

    async function checkDocuments() {
        const res = await fetch('/api/documents');
        const data = await res.json();
        if (data.pdf_names && data.pdf_names.length > 0) {
            uploadStatus.textContent = `Loaded: ${data.pdf_names.join(', ')}`;
            uploadStatus.style.color = 'var(--success)';
            sendBtn.disabled = false;
            loadPDF('/uploads/' + data.pdf_names[0], data.pdf_names[0]);
        } else {
            sendBtn.disabled = true;
        }
    }

    clearMemBtn.addEventListener('click', async () => {
        await fetch('/api/clear', { method: 'POST' });
        uploadStatus.textContent = '';
        sendBtn.disabled = true;
        pdfContainer.style.display = 'none';
        resizer.style.display = 'none';
        chatWrapper.style.display = 'none';
        emptyState.style.display = 'flex';
        clearMemBtn.style.display = 'none';
        pdfDoc = null;
        chatHistory = [];
        chatMessages.innerHTML = `
            <div class="message system">
                <div class="message-content">Memory cleared. Upload a PDF to start over.</div>
            </div>
        `;
    });

    // --- PDF Logic ---
    let isRendering = false;
    async function renderPage(num) {
        if (!pdfDoc || num > pdfDoc.numPages) return;
        
        const pageContainer = document.createElement('div');
        pageContainer.className = 'pdf-page-container';
        
        const canvas = document.createElement('canvas');
        canvas.className = 'pdf-canvas';
        const textLayer = document.createElement('div');
        textLayer.className = 'textLayer';
        
        pageContainer.appendChild(canvas);
        pageContainer.appendChild(textLayer);
        pdfViewerWrapper.appendChild(pageContainer);
        
        const page = await pdfDoc.getPage(num);
        const scale = 1.2;
        const viewport = page.getViewport({ scale });
        
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        const renderContext = {
            canvasContext: canvas.getContext('2d'),
            viewport: viewport
        };
        
        await page.render(renderContext).promise;
        
        const textContent = await page.getTextContent();
        textLayer.style.left = canvas.offsetLeft + 'px';
        textLayer.style.top = canvas.offsetTop + 'px';
        textLayer.style.height = canvas.offsetHeight + 'px';
        textLayer.style.width = canvas.offsetWidth + 'px';
        
        pdfjsLib.renderTextLayer({
            textContent: textContent,
            container: textLayer,
            viewport: viewport,
            textDivs: []
        });

        pageNumSpan.textContent = num;
    }

    async function loadMorePages() {
        if (isRendering || pageNum > pdfDoc.numPages) return;
        isRendering = true;
        await renderPage(pageNum);
        pageNum++;
        isRendering = false;
    }

    pdfViewerWrapper.addEventListener('scroll', (e) => {
        const target = e.target;
        if (target.scrollTop + target.clientHeight >= target.scrollHeight - 500) {
            loadMorePages();
        }
    });

    async function loadPDF(url, title) {
        try {
            pdfDoc = await pdfjsLib.getDocument(url).promise;
            pageCountSpan.textContent = pdfDoc.numPages;
            pdfTitle.textContent = title;
            
            // Update UI State
            emptyState.style.display = 'none';
            chatWrapper.style.display = 'flex';
            pdfContainer.style.display = 'flex';
            resizer.style.display = 'block';
            clearMemBtn.style.display = 'flex';
            
            document.getElementById('prev-page').style.display = 'none';
            document.getElementById('next-page').style.display = 'none';

            pdfViewerWrapper.innerHTML = '';
            pageNum = 1;
            
            await loadMorePages();
            if (pdfDoc.numPages > 1) {
                await loadMorePages();
            }
        } catch (e) {
            console.error('Error loading PDF', e);
        }
    }

    document.addEventListener('selectionchange', () => {
        const selection = window.getSelection();
        if (selection.toString().trim().length > 0 && pdfViewerWrapper.contains(selection.anchorNode)) {
            selectedText = selection.toString().trim();
            askSelectionBtn.style.display = 'flex';
        } else {
            selectedText = "";
            askSelectionBtn.style.display = 'none';
        }
    });

    askSelectionBtn.addEventListener('click', () => {
        chatInput.value = `Explain this: "${selectedText}"`;
        chatInput.focus();
    });

    // --- Chat Logic ---
    function addMessage(role, content) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = marked.parse(content || "");
        
        msgDiv.appendChild(contentDiv);
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return contentDiv;
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const prompt = chatInput.value.trim();
        if (!prompt) return;

        addMessage('user', prompt);
        chatInput.value = '';
        sendBtn.disabled = true;

        let apiPrompt = prompt;
        if (selectedText) {
            apiPrompt = `[Selected Context: "${selectedText}"]\n\nUser Question: ${prompt}`;
        }

        const payload = {
            prompt: apiPrompt,
            messages: chatHistory
        };

        chatHistory.push({ role: 'user', content: apiPrompt });
        const botContentDiv = addMessage('bot', '');

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) {
                const err = await res.json();
                botContentDiv.textContent = `Error: ${err.detail}`;
                botContentDiv.parentElement.style.color = 'var(--error)';
                sendBtn.disabled = false;
                return;
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let fullResponse = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                const textChunk = decoder.decode(value, { stream: true });
                fullResponse += textChunk;
                botContentDiv.innerHTML = marked.parse(fullResponse);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            chatHistory.push({ role: 'assistant', content: fullResponse });

        } catch (e) {
            botContentDiv.textContent = `Error: ${e.message}`;
            botContentDiv.parentElement.style.color = 'var(--error)';
        }

        sendBtn.disabled = false;
    });

    // Initial Load
    loadConfig();
    
    // Auto-fetch models on blur for inputs that change model lists
    openaiKey.addEventListener('blur', fetchModels);
    openrouterKey.addEventListener('blur', fetchModels);
    ollamaUrl.addEventListener('blur', fetchModels);
});
