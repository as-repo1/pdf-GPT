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
    const clearChatBtn = document.getElementById('clear-chat-btn');

    // State
    let chatHistory = [];
    let isConfigLoaded = false;

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
            }, 2000);
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
        } else {
            sendBtn.disabled = true;
        }
    }

    clearMemBtn.addEventListener('click', async () => {
        await fetch('/api/clear', { method: 'POST' });
        uploadStatus.textContent = '';
        sendBtn.disabled = true;
    });

    // --- Chat Logic ---
    function addMessage(role, content) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
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

        const payload = {
            prompt: prompt,
            messages: chatHistory
        };

        chatHistory.push({ role: 'user', content: prompt });
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
                botContentDiv.textContent = fullResponse;
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            chatHistory.push({ role: 'assistant', content: fullResponse });

        } catch (e) {
            botContentDiv.textContent = `Error: ${e.message}`;
            botContentDiv.parentElement.style.color = 'var(--error)';
        }

        sendBtn.disabled = false;
    });

    clearChatBtn.addEventListener('click', () => {
        chatHistory = [];
        chatMessages.innerHTML = `
            <div class="message system">
                <div class="message-content">Chat history cleared.</div>
            </div>
        `;
    });

    // Initial Load
    loadConfig();
    
    // Auto-fetch models on blur for inputs that change model lists
    openaiKey.addEventListener('blur', fetchModels);
    openrouterKey.addEventListener('blur', fetchModels);
    ollamaUrl.addEventListener('blur', fetchModels);
});
