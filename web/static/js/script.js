// Global state
let currentUser = null;
let isAnonymous = true;
let clips = [];
let authToken = localStorage.getItem('auth_token');
let sessionId = localStorage.getItem('session_id');

// API Base URL
const API_BASE = '/api';

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
});

// Handle shared clip view
async function handleSharedClip() {
    try {
        const path = window.location.pathname;
        const shareToken = path.split('/shared/')[1];

        if (!shareToken) {
            showError('Invalid share link');
            return;
        }

        // Hide main navigation and show shared clip view
        document.querySelector('.navbar').style.display = 'none';
        document.querySelector('.welcome-section').style.display = 'none';
        document.querySelector('.clips-section').style.display = 'none';

        // Create shared clip container
        const main = document.querySelector('.main-content');
        main.innerHTML = `
            <div class="shared-clip-container">
                <div class="shared-clip-header">
                    <h1>Shared Clip</h1>
                    <a href="/" class="btn btn-secondary">← Back to CLIP.LRU</a>
                </div>
                <div id="sharedClipContent" class="loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Loading shared clip...</span>
                </div>
            </div>
        `;

        // Fetch shared clip
        const response = await fetch(`${API_BASE}/clips/shared/${shareToken}`);

        if (response.ok) {
            const clip = await response.json();
            renderSharedClip(clip);
        } else if (response.status === 401) {
            // Encrypted clip, need password
            renderPasswordPrompt(shareToken);
        } else {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            showError(error.detail || 'Shared clip not found or has expired');
        }

    } catch (error) {
        console.error('Error loading shared clip:', error);
        showError('Failed to load shared clip');
    }
}

function renderSharedClip(clip) {
    const container = document.getElementById('sharedClipContent');

    container.innerHTML = `
        <div class="clip-card shared">
            <div class="clip-header">
                <div class="clip-type">
                    <i class="fas fa-${getClipIcon(clip.clip_type)}"></i>
                    <span>${clip.clip_type}</span>
                </div>
                <div class="clip-actions">
                    <button class="btn-icon" title="Copy to clipboard" onclick="copySharedClip()">
                        <i class="fas fa-copy"></i>
                    </button>
                </div>
            </div>
            <div class="clip-content">
                ${clip.title ? `<h4>${escapeHtml(clip.title)}</h4>` : ''}
                ${clip.clip_type === 'file' && clip.files && clip.files.length > 0 ?
                    `<div class="file-list">
                        ${clip.files.map(file => `
                            <div class="file-item">
                                <div class="file-info">
                                    <i class="fas fa-file"></i>
                                    <span>${escapeHtml(file.original_filename || file.filename)}</span>
                                    <small>(${formatFileSize(file.file_size || file.size)})</small>
                                </div>
                                <button class="btn-download" onclick="downloadFile(${file.id})" title="Download">
                                    <i class="fas fa-download"></i>
                                </button>
                            </div>
                        `).join('')}
                    </div>` :
                    `<p>${escapeHtml(clip.content || 'No content')}</p>`
                }
            </div>
            <div class="clip-footer">
                <span class="clip-time">Shared ${formatDate(clip.created_at)}</span>
                <span class="clip-access">${clip.access_level}</span>
            </div>
        </div>
    `;

    // Store clip for copying
    window.sharedClip = clip;
}

async function copySharedClip() {
    if (!window.sharedClip) return;

    try {
        let textToCopy = window.sharedClip.content || '';

        if (window.sharedClip.clip_type === 'file' && window.sharedClip.files && window.sharedClip.files.length > 0) {
            textToCopy = window.sharedClip.files.map(file => file.original_filename || file.filename).join('\n');
        }

        await navigator.clipboard.writeText(textToCopy);
        showToast('Copied to clipboard!', 'success');
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        showToast('Failed to copy to clipboard', 'error');
    }
}

function renderPasswordPrompt(shareToken) {
    const container = document.getElementById('sharedClipContent');

    container.innerHTML = `
        <div class="password-prompt">
            <div class="password-content">
                <i class="fas fa-lock"></i>
                <h3>This clip is encrypted</h3>
                <p>Please enter the password to view this clip</p>
                <div class="password-form">
                    <input type="password" id="clipPassword" placeholder="Enter password" />
                    <button class="btn btn-primary" onclick="accessEncryptedClip('${shareToken}')">
                        Access Clip
                    </button>
                </div>
            </div>
        </div>
    `;

    // Focus on password input
    document.getElementById('clipPassword').focus();

    // Handle Enter key
    document.getElementById('clipPassword').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            accessEncryptedClip(shareToken);
        }
    });
}

async function accessEncryptedClip(shareToken) {
    const password = document.getElementById('clipPassword').value;

    if (!password) {
        showToast('Please enter a password', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/clips/shared/${shareToken}/access`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password })
        });

        if (response.ok) {
            const clip = await response.json();
            renderSharedClip(clip);
        } else {
            const error = await response.json();
            showToast(error.detail || 'Incorrect password', 'error');
        }
    } catch (error) {
        console.error('Error accessing encrypted clip:', error);
        showToast('Failed to access clip', 'error');
    }
}

function showError(message) {
    const main = document.querySelector('.main-content');
    main.innerHTML = `
        <div class="error-container">
            <div class="error-content">
                <i class="fas fa-exclamation-triangle"></i>
                <h2>Error</h2>
                <p>${message}</p>
                <a href="/" class="btn btn-primary">← Back to CLIP.LRU</a>
            </div>
        </div>
    `;
}

// Initialize application
async function initializeApp() {
    try {
        // Check if this is a shared clip URL
        const path = window.location.pathname;
        if (path.startsWith('/shared/')) {
            await handleSharedClip();
            return;
        }

        // Check authentication status
        await checkAuthStatus();

        // Load clips
        await loadClips();

        // Update UI based on auth status
        updateUIForAuthStatus();

    } catch (error) {
        console.error('Failed to initialize app:', error);
        showToast('Failed to initialize application', 'error');
    }
}

// Setup event listeners
function setupEventListeners() {
    // Navigation
    document.getElementById('newClipBtn').addEventListener('click', showCreateModal);
    document.getElementById('userMenuBtn').addEventListener('click', toggleUserMenu);
    document.getElementById('loginBtn').addEventListener('click', showLoginModal);
    document.getElementById('registerBtn').addEventListener('click', showRegisterModal);
    document.getElementById('logoutBtn').addEventListener('click', logout);
    document.getElementById('upgradeBtn').addEventListener('click', showRegisterModal);
    
    // Search
    document.getElementById('searchInput').addEventListener('input', debounce(handleSearch, 300));
    
    // Filters
    document.getElementById('typeFilter').addEventListener('change', handleFilterChange);
    document.getElementById('sortFilter').addEventListener('change', handleFilterChange);
    
    // Modals
    document.getElementById('saveClipBtn').addEventListener('click', saveClip);
    document.getElementById('loginSubmitBtn').addEventListener('click', handleLogin);
    document.getElementById('registerSubmitBtn').addEventListener('click', handleRegister);
    
    // Clip form
    document.getElementById('clipType').addEventListener('change', handleClipTypeChange);
    document.getElementById('accessLevel').addEventListener('change', handleAccessLevelChange);
    
    // File upload
    setupFileUpload();

    // Global drag and drop for file upload
    setupGlobalDragDrop();

    // Markdown editor
    setupMarkdownEditor();

    // Close modals on outside click
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            closeModal();
            closeLoginModal();
            closeRegisterModal();
        }
    });
}

// Global drag and drop setup
function setupGlobalDragDrop() {
    let dragCounter = 0;

    // Create drag overlay
    const dragOverlay = document.createElement('div');
    dragOverlay.id = 'dragOverlay';
    dragOverlay.innerHTML = `
        <div class="drag-overlay-content">
            <i class="fas fa-cloud-upload-alt"></i>
            <h2>Drop files here to upload</h2>
            <p>Files will be uploaded and a new clip will be created</p>
        </div>
    `;
    dragOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(59, 130, 246, 0.9);
        color: white;
        display: none;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        backdrop-filter: blur(5px);
    `;

    const overlayContent = dragOverlay.querySelector('.drag-overlay-content');
    overlayContent.style.cssText = `
        text-align: center;
        padding: 2rem;
        border: 3px dashed rgba(255, 255, 255, 0.8);
        border-radius: 1rem;
        background: rgba(255, 255, 255, 0.1);
    `;

    overlayContent.querySelector('i').style.cssText = `
        font-size: 4rem;
        margin-bottom: 1rem;
        display: block;
    `;

    overlayContent.querySelector('h2').style.cssText = `
        margin: 1rem 0;
        font-size: 2rem;
    `;

    overlayContent.querySelector('p').style.cssText = `
        margin: 0;
        opacity: 0.8;
    `;

    document.body.appendChild(dragOverlay);

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        document.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop area
    ['dragenter', 'dragover'].forEach(eventName => {
        document.addEventListener(eventName, handleDragEnter, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        document.addEventListener(eventName, handleDragLeave, false);
    });

    function handleDragEnter(e) {
        dragCounter++;

        // Only show overlay for file drags, not text/other content
        if (e.dataTransfer.types.includes('Files')) {
            dragOverlay.style.display = 'flex';
        }
    }

    function handleDragLeave(e) {
        dragCounter--;

        if (dragCounter === 0) {
            dragOverlay.style.display = 'none';
        }
    }

    // Handle dropped files
    document.addEventListener('drop', handleGlobalDrop, false);

    async function handleGlobalDrop(e) {
        dragCounter = 0;
        dragOverlay.style.display = 'none';

        const files = e.dataTransfer.files;

        if (files.length > 0) {
            // Show create modal with file type selected
            showCreateModal();
            document.getElementById('clipType').value = 'file';
            handleClipTypeChange();

            // Add files to selection
            selectedFiles = Array.from(files);
            updateFileDisplay();

            showToast(`${files.length} file(s) ready for upload`, 'success');
        }
    }
}

// Authentication functions
async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE}/auth/status`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.authenticated && data.user) {
                currentUser = data.user;
                isAnonymous = data.user.is_anonymous;
            } else {
                // Create anonymous session if not authenticated
                await createAnonymousSession();
            }
        } else {
            await createAnonymousSession();
        }
    } catch (error) {
        console.error('Auth status check failed:', error);
        await createAnonymousSession();
    }
}

async function createAnonymousSession() {
    try {
        const response = await fetch(`${API_BASE}/auth/anonymous`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            sessionId = data.session_id;
            currentUser = data.user;
            isAnonymous = true;
            
            localStorage.setItem('session_id', sessionId);
            localStorage.removeItem('auth_token');
        }
    } catch (error) {
        console.error('Failed to create anonymous session:', error);
    }
}

async function handleLogin() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showToast('Please fill in all fields', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            currentUser = data.user;
            isAnonymous = false;
            
            localStorage.setItem('auth_token', authToken);
            localStorage.removeItem('session_id');
            
            closeLoginModal();
            updateUIForAuthStatus();
            await loadClips();
            showToast('Welcome back!', 'success');
        } else {
            const error = await response.json();
            const errorMessage = error.detail || error.message || 'Login failed';
            showToast(errorMessage, 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Login failed', 'error');
    }
}

async function handleRegister() {
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const fullName = document.getElementById('regFullName').value;
    
    if (!username || !email || !password) {
        showToast('Please fill in required fields', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                email,
                password,
                full_name: fullName || undefined
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            currentUser = data.user;
            isAnonymous = false;
            
            localStorage.setItem('auth_token', authToken);
            localStorage.removeItem('session_id');
            
            closeRegisterModal();
            updateUIForAuthStatus();
            await loadClips();
            showToast('Account created successfully!', 'success');
        } else {
            const error = await response.json();
            let errorMessage = error.detail || error.message || 'Registration failed';
            if(Array.isArray(errorMessage)){
                let err_msg = 'Registration failed: <br>';
                for(let i = 0; i < errorMessage.length; i++){
                    err_msg += errorMessage[i].loc[1] + ': ' + errorMessage[i].msg + '<br>';
                }
                errorMessage = err_msg;
            }
            showToast(errorMessage, 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showToast('Registration failed', 'error');
    }
}

async function logout() {
    try {
        authToken = null;
        sessionId = null;
        currentUser = null;
        
        localStorage.removeItem('auth_token');
        localStorage.removeItem('session_id');
        
        await createAnonymousSession();
        updateUIForAuthStatus();
        await loadClips();
        showToast('Signed out successfully', 'info');
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Clip management functions
async function loadClips() {
    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE}/clips/`, {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const data = await response.json();
            clips = data.clips || [];
            renderClips();
        } else {
            console.error('Failed to load clips');
            showEmptyState();
        }
    } catch (error) {
        console.error('Error loading clips:', error);
        showEmptyState();
    } finally {
        showLoading(false);
    }
}

async function saveClip() {
    const title = document.getElementById('clipTitle').value;

    // Get content from CodeMirror or fallback to textarea
    let content = '';
    if (codeMirrorEditor) {
        content = codeMirrorEditor.getValue();
    } else {
        content = document.getElementById('clipContent').value;
    }

    const clipType = document.getElementById('clipType').value;
    const accessLevel = document.getElementById('accessLevel').value;
    const password = document.getElementById('clipPassword').value;
    const isMarkdown = document.getElementById('isMarkdown').checked;
    const fileId = document.getElementById('clipForm').dataset.fileId;
    const fileIds = document.getElementById('clipForm').dataset.fileIds;
    const editId = document.getElementById('clipForm').dataset.editId;

    if (!content && clipType !== 'file') {
        showToast('Please enter content', 'error');
        return;
    }

    if (clipType === 'file' && !fileId && !fileIds && !editId) {
        showToast('Please upload a file', 'error');
        return;
    }

    try {
        const clipData = {
            title: title || undefined,
            content: content || undefined,
            clip_type: clipType,
            access_level: accessLevel,
            password: password || undefined,
            is_markdown: isMarkdown
        };

        // If it's a file clip, associate the uploaded files
        if (clipType === 'file') {
            if (fileIds) {
                // Multiple files uploaded
                try {
                    const parsedFileIds = JSON.parse(fileIds);
                    if (Array.isArray(parsedFileIds) && parsedFileIds.length > 0) {
                        clipData.file_ids = parsedFileIds;
                        console.log('Adding multiple file IDs to clip:', parsedFileIds);
                    } else {
                        console.error('Invalid file IDs array:', parsedFileIds);
                    }
                } catch (error) {
                    console.error('Error parsing file IDs:', error);
                }
            } else if (fileId && fileId !== 'undefined' && fileId !== 'null') {
                // Single file (legacy support)
                const parsedFileId = parseInt(fileId);
                if (!isNaN(parsedFileId)) {
                    clipData.file_ids = [parsedFileId];
                    console.log('Adding single file ID to clip:', parsedFileId);
                } else {
                    console.error('Invalid file ID:', fileId);
                }
            } else if (!editId) {
                console.error('File clip without valid file IDs');
                showToast('No files uploaded for file clip', 'error');
                return;
            }
        }

        console.log('Clip data being sent:', clipData);

        const isEdit = !!editId;
        const url = isEdit ? `${API_BASE}/clips/${editId}` : `${API_BASE}/clips/`;
        const method = isEdit ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: {
                ...getAuthHeaders(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(clipData)
        });

        if (response.ok) {
            const savedClip = await response.json();

            if (isEdit) {
                // Update existing clip in the list
                const index = clips.findIndex(c => c.id === parseInt(editId));
                if (index !== -1) {
                    clips[index] = savedClip;
                }
                showToast('Clip updated successfully!', 'success');
            } else {
                // Add new clip to the beginning
                clips.unshift(savedClip);
                showToast('Clip created successfully!', 'success');
            }

            renderClips();
            closeModal();
        } else {
            const error = await response.json();
            showToast(error.detail || `Failed to ${isEdit ? 'update' : 'create'} clip`, 'error');
        }
    } catch (error) {
        console.error('Error saving clip:', error);
        showToast(`Failed to ${editId ? 'update' : 'create'} clip`, 'error');
    }
}

// UI helper functions
function getAuthHeaders() {
    const headers = {};
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    } else if (sessionId) {
        headers['X-Session-Id'] = sessionId;
    }
    return headers;
}

function updateUIForAuthStatus() {
    const userInfo = document.getElementById('userInfo');
    const loginBtn = document.getElementById('loginBtn');
    const registerBtn = document.getElementById('registerBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const anonymousPrompt = document.getElementById('anonymousPrompt');
    
    if (isAnonymous) {
        userInfo.innerHTML = `
            <div class="user-name">Anonymous User</div>
            <div class="user-status">Limited features</div>
        `;
        loginBtn.style.display = 'block';
        registerBtn.style.display = 'block';
        logoutBtn.style.display = 'none';
        anonymousPrompt.style.display = 'block';
    } else {
        userInfo.innerHTML = `
            <div class="user-name">${currentUser.full_name || currentUser.username}</div>
            <div class="user-status">${currentUser.email}</div>
        `;
        loginBtn.style.display = 'none';
        registerBtn.style.display = 'none';
        logoutBtn.style.display = 'block';
        anonymousPrompt.style.display = 'none';
    }
}

function renderClips() {
    const clipsGrid = document.getElementById('clipsGrid');
    const emptyState = document.getElementById('emptyState');
    
    if (clips.length === 0) {
        clipsGrid.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    clipsGrid.style.display = 'grid';
    emptyState.style.display = 'none';
    
    clipsGrid.innerHTML = clips.map(clip => `
        <div class="clip-card ${clip.is_pinned ? 'pinned' : ''} ${clip.access_level}" data-id="${clip.id}">
            <div class="clip-header">
                <div class="clip-type">
                    <i class="fas fa-${getClipIcon(clip.clip_type)}"></i>
                    <span>${clip.clip_type}</span>
                </div>
                <div class="clip-actions">
                    <button class="btn-icon" title="Copy to clipboard" onclick="copyToClipboard(${clip.id})">
                        <i class="fas fa-copy"></i>
                    </button>
                    <button class="btn-icon" title="Edit" onclick="editClip(${clip.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon" title="${clip.is_pinned ? 'Unpin' : 'Pin'}" onclick="togglePin(${clip.id})">
                        <i class="fas fa-thumbtack ${clip.is_pinned ? 'pinned' : ''}"></i>
                    </button>
                    ${clip.share_token ? `
                        <button class="btn-icon" title="Share" onclick="shareClip('${clip.share_token}')">
                            <i class="fas fa-share"></i>
                        </button>
                    ` : ''}
                    <button class="btn-icon" title="Delete" onclick="deleteClip(${clip.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="clip-content">
                ${clip.title ? `<h4>${escapeHtml(clip.title)}</h4>` : ''}
                ${clip.clip_type === 'file' && clip.files && clip.files.length > 0 ?
                    `<div class="file-list">
                        ${clip.files.map(file => `
                            <div class="file-item">
                                <div class="file-info">
                                    <i class="fas fa-file"></i>
                                    <span>${escapeHtml(file.original_filename || file.filename)}</span>
                                    <small>(${formatFileSize(file.file_size || file.size)})</small>
                                </div>
                                <button class="btn-download" onclick="downloadFile(${file.id})" title="Download">
                                    <i class="fas fa-download"></i>
                                </button>
                            </div>
                        `).join('')}
                    </div>` :
                    clip.is_markdown && clip.content ?
                        renderClipContent(clip) :
                        renderTextContent(clip.content)
                }
            </div>
            <div class="clip-footer">
                <span class="clip-time">${formatDate(clip.created_at)}</span>
                <span class="clip-access">${clip.access_level}</span>
            </div>
        </div>
    `).join('');
}

function showLoading(show) {
    const loading = document.getElementById('loading');
    loading.style.display = show ? 'flex' : 'none';
}

function showEmptyState() {
    const clipsGrid = document.getElementById('clipsGrid');
    const emptyState = document.getElementById('emptyState');
    
    clipsGrid.style.display = 'none';
    emptyState.style.display = 'block';
}

// Modal functions
function showCreateModal() {
    document.getElementById('clipModal').classList.add('show');
    document.getElementById('modalTitle').textContent = 'Create New Clip';

    // Reset form
    const form = document.getElementById('clipForm');
    form.reset();
    form.removeAttribute('data-file-id');
    form.removeAttribute('data-edit-id');

    // Reset file upload area
    const fileUpload = document.getElementById('fileUpload');
    fileUpload.innerHTML = `
        <i class="fas fa-cloud-upload-alt"></i>
        <p>Drag & drop files here or click to browse</p>
        <input type="file" id="fileInput" multiple>
    `;

    // Re-setup file upload listeners
    setupFileUpload();

    handleClipTypeChange();
    handleAccessLevelChange();
}

function closeModal() {
    document.getElementById('clipModal').classList.remove('show');

    // Reset form
    document.getElementById('clipForm').reset();

    // Clear stored file IDs and edit ID
    delete document.getElementById('clipForm').dataset.fileId;
    delete document.getElementById('clipForm').dataset.fileIds;
    delete document.getElementById('clipForm').dataset.editId;

    // Clear selected files
    selectedFiles = [];

    // Reset modal title
    document.getElementById('modalTitle').textContent = 'Create New Clip';

    // Reset file upload area
    const fileUpload = document.getElementById('fileUpload');
    fileUpload.innerHTML = `
        <i class="fas fa-cloud-upload-alt"></i>
        <p>Drag & drop files here or click to browse</p>
        <input type="file" id="fileInput" multiple>
    `;

    // Re-setup file upload events
    setupFileUpload();

    // Reset markdown state
    document.getElementById('isMarkdown').checked = false;
    // Close any open preview modal
    closeEditorPreview();
    toggleMarkdownMode(); // Reset markdown UI

    // Clear CodeMirror content
    if (codeMirrorEditor) {
        codeMirrorEditor.setValue('');
    }

    // Hide password group
    document.getElementById('passwordGroup').style.display = 'none';

    // Show content group for text clips
    document.getElementById('contentGroup').style.display = 'block';
    document.getElementById('fileGroup').style.display = 'none';

    // Reset clip type to text
    document.getElementById('clipType').value = 'text';
    document.getElementById('accessLevel').value = 'private';
}

function showLoginModal() {
    document.getElementById('loginModal').classList.add('show');
    document.getElementById('loginForm').reset();
}

function closeLoginModal() {
    document.getElementById('loginModal').classList.remove('show');
}

function showRegisterModal() {
    document.getElementById('registerModal').classList.add('show');
    document.getElementById('registerForm').reset();
}

function closeRegisterModal() {
    document.getElementById('registerModal').classList.remove('show');
}

function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('show');
}

// Form handlers
function handleClipTypeChange() {
    const clipType = document.getElementById('clipType').value;
    const contentGroup = document.getElementById('contentGroup');
    const fileGroup = document.getElementById('fileGroup');
    const markdownCheckbox = document.getElementById('isMarkdown');
    const editorControls = document.getElementById('editorControls');
    const editorStatus = document.getElementById('editorStatus');

    if (clipType === 'file') {
        contentGroup.style.display = 'none';
        fileGroup.style.display = 'block';

        // 隐藏 Markdown 相关功能
        if (markdownCheckbox) {
            markdownCheckbox.checked = false;
            markdownCheckbox.closest('.checkbox-label').style.display = 'none';
        }
        if (editorControls) editorControls.style.display = 'none';
        if (editorStatus) editorStatus.style.display = 'none';

        // 重置编辑器模式
        resetEditorToPlainText();

    } else {
        contentGroup.style.display = 'block';
        fileGroup.style.display = 'none';

        // 显示 Markdown 相关功能（仅对 text 和 markdown 类型）
        if (markdownCheckbox) {
            if (clipType === 'markdown') {
                // markdown 类型自动启用 markdown
                markdownCheckbox.checked = true;
                markdownCheckbox.closest('.checkbox-label').style.display = 'flex';
                toggleMarkdownMode();
            } else if (clipType === 'text') {
                // text 类型显示 markdown 选项但不自动启用
                markdownCheckbox.closest('.checkbox-label').style.display = 'flex';
                // 如果之前没有选中，保持当前状态
                toggleMarkdownMode();
            } else {
                // 其他类型隐藏 markdown 选项
                markdownCheckbox.checked = false;
                markdownCheckbox.closest('.checkbox-label').style.display = 'none';
                if (editorControls) editorControls.style.display = 'none';
                if (editorStatus) editorStatus.style.display = 'none';
                resetEditorToPlainText();
            }
        }
    }
}

function resetEditorToPlainText() {
    const editorContainer = document.querySelector('.editor-container');

    // 重置编辑器状态
    closeEditorPreview(); // Close any open preview modal
    if (isFullscreen) {
        toggleFullscreen();
    }

    // 重置编辑器模式
    if (codeMirrorEditor) {
        codeMirrorEditor.setOption('mode', 'text/plain');
        setTimeout(() => codeMirrorEditor.refresh(), 100);
    }

    // 移除 markdown 模式样式
    if (editorContainer) {
        editorContainer.classList.remove('markdown-mode');
    }
}

function handleAccessLevelChange() {
    const accessLevel = document.getElementById('accessLevel').value;
    const passwordGroup = document.getElementById('passwordGroup');
    
    passwordGroup.style.display = accessLevel === 'encrypted' ? 'block' : 'none';
}

// File upload setup
function setupFileUpload() {
    const fileUpload = document.getElementById('fileUpload');
    const fileInput = document.getElementById('fileInput');

    if (!fileUpload || !fileInput) return;

    // Remove existing event listeners to prevent duplicates
    const newFileUpload = fileUpload.cloneNode(true);
    fileUpload.parentNode.replaceChild(newFileUpload, fileUpload);

    // Get the new file input after cloning
    const newFileInput = document.getElementById('fileInput');

    // Add click handler only to the upload area, not the input
    newFileUpload.addEventListener('click', (e) => {
        // Only trigger file input if clicking on the upload area itself, not buttons
        if (e.target === newFileUpload || e.target.tagName === 'I' || e.target.tagName === 'P') {
            newFileInput.click();
        }
    });

    newFileUpload.addEventListener('dragover', (e) => {
        e.preventDefault();
        newFileUpload.classList.add('drag-over');
    });

    newFileUpload.addEventListener('dragleave', () => {
        newFileUpload.classList.remove('drag-over');
    });

    newFileUpload.addEventListener('drop', (e) => {
        e.preventDefault();
        newFileUpload.classList.remove('drag-over');
        handleFileSelect(e.dataTransfer.files);
    });

    newFileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files);
    });
}

// Global variable to store selected files
let selectedFiles = [];

async function handleFileSelect(files) {
    if (files.length > 0) {
        // Add new files to the selected files array
        for (let file of files) {
            // Check if file already exists (by name and size)
            const exists = selectedFiles.some(f => f.name === file.name && f.size === file.size);
            if (!exists) {
                selectedFiles.push(file);
            }
        }

        showToast(`Selected ${files.length} file(s). Total: ${selectedFiles.length}`, 'info');
        updateFileDisplay();
    }
}

function updateFileDisplay() {
    const fileUpload = document.getElementById('fileUpload');

    if (selectedFiles.length === 0) {
        // Show default upload area
        fileUpload.innerHTML = `
            <i class="fas fa-cloud-upload-alt"></i>
            <p>Drag & drop files here or click to browse</p>
            <input type="file" id="fileInput" multiple>
        `;
        setupFileUpload();
        return;
    }

    // Show selected files
    fileUpload.innerHTML = `
        <div class="selected-files">
            <div class="files-header">
                <h4><i class="fas fa-files"></i> Selected Files (${selectedFiles.length})</h4>
                <div class="files-actions">
                    <button type="button" class="btn btn-sm btn-primary" onclick="smartUpload()">
                        <i class="fas fa-upload"></i> Upload All
                    </button>
                    <button type="button" class="btn btn-sm btn-secondary" onclick="addMoreFiles()">
                        <i class="fas fa-plus"></i> Add More
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="clearSelectedFiles()">
                        <i class="fas fa-trash"></i> Clear All
                    </button>
                </div>
            </div>
            <div class="files-list">
                ${selectedFiles.map((file, index) => `
                    <div class="file-item" data-index="${index}">
                        <div class="file-info">
                            <i class="fas fa-file"></i>
                            <div class="file-details">
                                <div class="file-name">${escapeHtml(file.name)}</div>
                                <div class="file-size">${formatFileSize(file.size)} • ${file.type || 'Unknown type'}</div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFile(${index})">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `).join('')}
            </div>
            <div class="upload-progress" id="uploadProgress" style="display: none;">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="progress-text" id="progressText">Uploading...</div>
            </div>
        </div>
    `;
}

function addMoreFiles() {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.addEventListener('change', (e) => {
        handleFileSelect(e.target.files);
    });
    input.click();
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileDisplay();
    showToast('File removed', 'info');
}

function clearSelectedFiles() {
    selectedFiles = [];
    updateFileDisplay();
    showToast('All files cleared', 'info');
}

// Stream upload function with real progress tracking
async function uploadFileWithProgress(file, index, total) {
    return new Promise((resolve, reject) => {
        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();
        
        // Create progress container for this file
        const progressContainer = document.createElement('div');
        progressContainer.className = 'file-upload-progress';
        progressContainer.innerHTML = `
            <div class="file-progress-info">
                <div class="file-name">${escapeHtml(file.name)}</div>
                <div class="file-status">Preparing...</div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
            <div class="progress-details">
                <span class="progress-percent">0%</span>
                <span class="progress-speed"></span>
                <span class="progress-eta"></span>
            </div>
        `;
        
        // Add to progress display
        const uploadProgress = document.getElementById('uploadProgress');
        if (!uploadProgress.querySelector('.files-progress-container')) {
            const container = document.createElement('div');
            container.className = 'files-progress-container';
            uploadProgress.appendChild(container);
        }
        uploadProgress.querySelector('.files-progress-container').appendChild(progressContainer);
        
        const progressFill = progressContainer.querySelector('.progress-fill');
        const progressPercent = progressContainer.querySelector('.progress-percent');
        const progressSpeed = progressContainer.querySelector('.progress-speed');
        const progressEta = progressContainer.querySelector('.progress-eta');
        const fileStatus = progressContainer.querySelector('.file-status');
        
        let startTime = Date.now();
        let lastLoaded = 0;
        let lastTime = startTime;
        
        // Upload progress tracking
        xhr.upload.addEventListener('progress', (event) => {
            if (event.lengthComputable) {
                const percent = Math.round((event.loaded / event.total) * 100);
                const currentTime = Date.now();
                const timeElapsed = (currentTime - startTime) / 1000;
                const timeSinceLastUpdate = (currentTime - lastTime) / 1000;
                
                // Update progress bar
                progressFill.style.width = `${percent}%`;
                progressPercent.textContent = `${percent}%`;
                
                // Calculate speed
                if (timeSinceLastUpdate > 0.5) { // Update speed every 0.5 seconds
                    const bytesThisUpdate = event.loaded - lastLoaded;
                    const speed = bytesThisUpdate / timeSinceLastUpdate;
                    progressSpeed.textContent = `${formatFileSize(speed)}/s`;
                    
                    // Calculate ETA
                    if (speed > 0) {
                        const remainingBytes = event.total - event.loaded;
                        const eta = remainingBytes / speed;
                        if (eta > 60) {
                            progressEta.textContent = `ETA: ${Math.ceil(eta / 60)}m`;
                        } else {
                            progressEta.textContent = `ETA: ${Math.ceil(eta)}s`;
                        }
                    }
                    
                    lastLoaded = event.loaded;
                    lastTime = currentTime;
                }
                
                fileStatus.textContent = `Uploading... ${formatFileSize(event.loaded)} / ${formatFileSize(event.total)}`;
            }
        });
        
        // Handle upload completion
        xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                const response = JSON.parse(xhr.responseText);
                progressFill.style.width = '100%';
                progressPercent.textContent = '100%';
                fileStatus.textContent = 'Upload complete!';
                fileStatus.style.color = 'green';
                progressContainer.classList.add('completed');
                
                // Hide cancel button
                const cancelBtn = progressContainer.querySelector('.cancel-file-btn');
                if (cancelBtn) {
                    cancelBtn.style.display = 'none';
                }
                
                resolve(response.file);
            } else {
                let errorMessage = 'Upload failed!';
                try {
                    const errorResponse = JSON.parse(xhr.responseText);
                    errorMessage = errorResponse.detail || errorMessage;
                } catch (e) {
                    errorMessage = `HTTP ${xhr.status}: ${xhr.statusText}`;
                }
                
                fileStatus.textContent = errorMessage;
                fileStatus.style.color = 'red';
                progressContainer.classList.add('failed');
                
                // Hide cancel button
                const cancelBtn = progressContainer.querySelector('.cancel-file-btn');
                if (cancelBtn) {
                    cancelBtn.style.display = 'none';
                }
                
                reject(new Error(errorMessage));
            }
        });
        
        // Handle upload error
        xhr.addEventListener('error', () => {
            fileStatus.textContent = 'Network error occurred!';
            fileStatus.style.color = 'red';
            progressContainer.classList.add('failed');
            
            // Hide cancel button
            const cancelBtn = progressContainer.querySelector('.cancel-file-btn');
            if (cancelBtn) {
                cancelBtn.style.display = 'none';
            }
            
            reject(new Error('Network error'));
        });
        
        // Handle upload abort
        xhr.addEventListener('abort', () => {
            fileStatus.textContent = 'Upload cancelled!';
            fileStatus.style.color = 'orange';
            progressContainer.classList.add('cancelled');
            
            // Hide cancel button
            const cancelBtn = progressContainer.querySelector('.cancel-file-btn');
            if (cancelBtn) {
                cancelBtn.style.display = 'none';
            }
            
            reject(new Error('Upload cancelled'));
        });
        
        // Start upload
        xhr.open('POST', `${API_BASE}/files/stream-upload`);
        
        // Add authentication headers
        const authHeaders = getAuthHeaders();
        for (const [key, value] of Object.entries(authHeaders)) {
            xhr.setRequestHeader(key, value);
        }
        
        fileStatus.textContent = 'Starting upload...';
        xhr.send(formData);
        
        // Store xhr for potential cancellation
        progressContainer.xhr = xhr;

        // Add cancel button for individual file
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'btn btn-sm btn-outline-danger cancel-file-btn';
        cancelBtn.innerHTML = '<i class="fas fa-times"></i>';
        cancelBtn.title = 'Cancel upload';
        cancelBtn.onclick = () => {
            if (xhr) {
                xhr.abort();
            }
        };
        progressContainer.querySelector('.file-progress-info').appendChild(cancelBtn);
    });
}

// New streaming upload function with detailed progress
async function uploadAllFilesWithProgress() {
    if (selectedFiles.length === 0) {
        showToast('No files selected', 'error');
        return;
    }

    const uploadProgress = document.getElementById('uploadProgress');
    const progressText = document.getElementById('progressText');
    
    // Clear previous progress containers
    const existingContainer = uploadProgress.querySelector('.files-progress-container');
    if (existingContainer) {
        existingContainer.remove();
    }
    
    // Update main progress text
    progressText.textContent = `Uploading ${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''}...`;
    uploadProgress.style.display = 'block';
    
    // Add cancel all button
    if (!uploadProgress.querySelector('.cancel-all-btn')) {
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'btn btn-sm btn-outline-danger cancel-all-btn';
        cancelBtn.innerHTML = '<i class="fas fa-times"></i> Cancel All';
        cancelBtn.onclick = cancelAllUploads;
        uploadProgress.appendChild(cancelBtn);
    }

    const uploadedFiles = [];
    let successCount = 0;
    let failCount = 0;
    let cancelCount = 0;

    try {
        // Upload files concurrently (limit to 3 concurrent uploads)
        const concurrentLimit = 3;
        const uploadPromises = [];
        
        for (let i = 0; i < selectedFiles.length; i += concurrentLimit) {
            const batch = selectedFiles.slice(i, i + concurrentLimit);
            const batchPromises = batch.map((file, batchIndex) => 
                uploadFileWithProgress(file, i + batchIndex, selectedFiles.length)
                    .then(fileData => {
                        uploadedFiles.push(fileData);
                        successCount++;
                        console.log(`✅ Uploaded: ${fileData.original_filename} (ID: ${fileData.id})`);
                        return fileData;
                    })
                    .catch(error => {
                        console.error(`❌ Failed to upload ${file.name}:`, error);
                        if (error.message === 'Upload cancelled') {
                            cancelCount++;
                        } else {
                            failCount++;
                        }
                        return null;
                    })
            );
            
            uploadPromises.push(...batchPromises);
            
            // Wait for this batch to complete before starting the next
            await Promise.allSettled(batchPromises);
        }

        // Wait for all uploads to complete
        await Promise.allSettled(uploadPromises);

        // Update main progress text
        progressText.textContent = `Upload complete: ${successCount} successful, ${failCount} failed, ${cancelCount} cancelled`;

        // Show results
        if (successCount > 0) {
            showToast(`Successfully uploaded ${successCount} file(s)`, 'success');

            // Store file IDs for clip creation
            const fileIds = uploadedFiles.map(f => f.id);
            document.getElementById('clipForm').dataset.fileIds = JSON.stringify(fileIds);

            // Auto-fill clip title with first filename or "Multiple files"
            const titleInput = document.getElementById('clipTitle');
            if (uploadedFiles.length === 1) {
                titleInput.value = uploadedFiles[0].original_filename;
            } else {
                titleInput.value = `Multiple files (${uploadedFiles.length})`;
            }

            // Show uploaded files
            showUploadedFiles(uploadedFiles);
        }

        if (failCount > 0) {
            showToast(`Failed to upload ${failCount} file(s)`, 'error');
        }
        
        if (cancelCount > 0) {
            showToast(`Cancelled ${cancelCount} upload(s)`, 'warning');
        }

    } finally {
        // Remove cancel button
        const cancelBtn = uploadProgress.querySelector('.cancel-all-btn');
        if (cancelBtn) {
            cancelBtn.remove();
        }
        
        // Hide progress after 5 seconds if all completed
        setTimeout(() => {
            const hasActiveUploads = uploadProgress.querySelectorAll('.file-upload-progress:not(.completed):not(.failed):not(.cancelled)').length > 0;
            if (!hasActiveUploads) {
                uploadProgress.style.display = 'none';
            }
        }, 5000);
    }
}

// Function to cancel all ongoing uploads
function cancelAllUploads() {
    const progressContainers = document.querySelectorAll('.file-upload-progress:not(.completed):not(.failed):not(.cancelled)');
    progressContainers.forEach(container => {
        if (container.xhr) {
            container.xhr.abort();
        }
    });
    showToast('All uploads cancelled', 'warning');
}

// Legacy upload function (fallback)
async function uploadAllFiles() {
    if (selectedFiles.length === 0) {
        showToast('No files selected', 'error');
        return;
    }

    const uploadProgress = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    uploadProgress.style.display = 'block';

    const uploadedFiles = [];
    let successCount = 0;
    let failCount = 0;

    try {
        for (let i = 0; i < selectedFiles.length; i++) {
            const file = selectedFiles[i];

            // Update progress
            const progress = ((i + 1) / selectedFiles.length) * 100;
            progressFill.style.width = `${progress}%`;
            progressText.textContent = `Uploading ${i + 1}/${selectedFiles.length}: ${file.name}`;

            try {
                // Create FormData for file upload
                const formData = new FormData();
                formData.append('file', file);

                // Upload file using legacy endpoint
                const response = await fetch(`${API_BASE}/files/upload`, {
                    method: 'POST',
                    headers: getAuthHeaders(),
                    body: formData
                });

                if (response.ok) {
                    const uploadResponse = await response.json();
                    const fileData = uploadResponse.file;
                    uploadedFiles.push(fileData);
                    successCount++;

                    console.log(`✅ Uploaded: ${fileData.original_filename} (ID: ${fileData.id})`);
                } else {
                    const error = await response.json();
                    console.error(`❌ Failed to upload ${file.name}:`, error);
                    failCount++;
                }
            } catch (error) {
                console.error(`❌ Error uploading ${file.name}:`, error);
                failCount++;
            }

            // Small delay between uploads
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        // Show results
        if (successCount > 0) {
            showToast(`Successfully uploaded ${successCount} file(s)`, 'success');

            // Store file IDs for clip creation
            const fileIds = uploadedFiles.map(f => f.id);
            document.getElementById('clipForm').dataset.fileIds = JSON.stringify(fileIds);

            // Auto-fill clip title with first filename or "Multiple files"
            const titleInput = document.getElementById('clipTitle');
            if (uploadedFiles.length === 1) {
                titleInput.value = uploadedFiles[0].original_filename;
            } else {
                titleInput.value = `Multiple files (${uploadedFiles.length})`;
            }

            // Show uploaded files
            showUploadedFiles(uploadedFiles);
        }

        if (failCount > 0) {
            showToast(`Failed to upload ${failCount} file(s)`, 'error');
        }

    } finally {
        uploadProgress.style.display = 'none';
    }
}

// Smart upload function that chooses the best method
async function smartUpload() {
    // Try enhanced upload first, fallback to legacy if it fails
    try {
        console.log('Attempting enhanced stream upload with progress tracking');
        return await uploadAllFilesWithProgress();
    } catch (error) {
        console.warn('Enhanced upload failed, falling back to legacy method:', error);
        showToast('Using fallback upload method', 'info');
        return await uploadAllFiles();
    }
}



function showUploadedFiles(files) {
    const fileUpload = document.getElementById('fileUpload');

    fileUpload.innerHTML = `
        <div class="uploaded-files">
            <div class="files-header">
                <h4><i class="fas fa-check-circle" style="color: green;"></i> Uploaded Files (${files.length})</h4>
                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="replaceAllFiles()">
                    <i class="fas fa-upload"></i> Replace All
                </button>
            </div>
            <div class="files-list">
                ${files.map(file => `
                    <div class="file-item uploaded">
                        <div class="file-info">
                            <i class="fas fa-file" style="color: green;"></i>
                            <div class="file-details">
                                <div class="file-name">${escapeHtml(file.original_filename)}</div>
                                <div class="file-size">${formatFileSize(file.file_size)} • ${file.mime_type}</div>
                                <div class="file-id">ID: ${file.id}</div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-primary" onclick="downloadFile(${file.id})">
                            <i class="fas fa-download"></i>
                        </button>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function replaceAllFiles() {
    selectedFiles = [];
    document.getElementById('clipForm').removeAttribute('data-file-ids');
    updateFileDisplay();
}

// Utility functions
function getClipIcon(type) {
    const icons = {
        text: 'file-text',
        markdown: 'file-code',
        file: 'file',
        image: 'image',
        video: 'video',
        audio: 'music'
    };
    return icons[type] || 'file';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    return date.toLocaleDateString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Markdown rendering functions
function renderMarkdown(content) {
    if (!content) return '';

    // Configure marked options
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                try {
                    return hljs.highlight(code, { language: lang }).value;
                } catch (err) {}
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true,
        gfm: true
    });

    const html = marked.parse(content);

    // 为代码块添加复制按钮
    return addCopyButtonsToCodeBlocks(html);
}

// 为代码块添加复制按钮
function addCopyButtonsToCodeBlocks(html) {
    // 创建临时DOM元素来处理HTML
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = html;

    // 查找所有的pre元素（代码块）
    const preElements = tempDiv.querySelectorAll('pre');

    preElements.forEach((pre, index) => {
        // 检查是否已经有复制按钮
        if (pre.querySelector('.copy-code-btn')) return;

        // 获取代码内容
        const codeElement = pre.querySelector('code');
        if (!codeElement) return;

        // 创建复制按钮
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-code-btn';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i><span>Copy</span>';
        copyBtn.setAttribute('data-code-index', index);

        // 添加按钮到pre元素
        pre.appendChild(copyBtn);
    });

    return tempDiv.innerHTML;
}

// 复制代码到剪贴板
async function copyCodeToClipboard(button, code) {
    try {
        await navigator.clipboard.writeText(code);

        // 更新按钮状态
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-check"></i><span>Copied!</span>';
        button.classList.add('copied');

        // 2秒后恢复原状
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.classList.remove('copied');
        }, 2000);

        showToast('Code copied to clipboard!', 'success');
    } catch (error) {
        console.error('Failed to copy code:', error);
        showToast('Failed to copy code', 'error');
    }
}

// 全局事件委托处理代码复制按钮
document.addEventListener('click', function(e) {
    if (e.target.closest('.copy-code-btn')) {
        e.preventDefault();
        e.stopPropagation();

        const button = e.target.closest('.copy-code-btn');
        const pre = button.closest('pre');
        const codeElement = pre.querySelector('code');

        if (codeElement) {
            copyCodeToClipboard(button, codeElement.textContent);
        }
    }
});

// 渲染 Markdown 内容（带截断）
function renderClipContent(clip) {
    const maxLength = 500; // 最大字符数
    const content = clip.content || '';

    if (content.length <= maxLength) {
        return `<div class="markdown-content">${renderMarkdown(content)}</div>`;
    }

    // 截断内容
    const truncatedContent = content.substring(0, maxLength);
    const lastLineBreak = truncatedContent.lastIndexOf('\n');
    const finalContent = lastLineBreak > maxLength * 0.7 ?
        truncatedContent.substring(0, lastLineBreak) :
        truncatedContent;

    return `
        <div class="markdown-content truncated" id="content-${clip.id}">
            ${renderMarkdown(finalContent)}
            <div class="content-fade"></div>
        </div>
        <div class="content-actions">
            <button class="btn btn-sm btn-outline" onclick="showFullContent(${clip.id}, 'markdown')">
                <i class="fas fa-expand"></i> Show Full Content
            </button>
        </div>
    `;
}

// 渲染普通文本内容（带截断）
function renderTextContent(content) {
    const maxLength = 300; // 普通文本的最大字符数
    const text = content || 'No content';

    if (text.length <= maxLength) {
        return `<p>${escapeHtml(text)}</p>`;
    }

    const truncatedText = text.substring(0, maxLength);
    const lastSpace = truncatedText.lastIndexOf(' ');
    const finalText = lastSpace > maxLength * 0.8 ?
        truncatedText.substring(0, lastSpace) :
        truncatedText;

    return `
        <div class="text-content truncated">
            <p>${escapeHtml(finalText)}...</p>
        </div>
        <div class="content-actions">
            <button class="btn btn-sm btn-outline" onclick="showFullContent(null, 'text', \`${escapeHtml(text).replace(/`/g, '\\`')}\`)">
                <i class="fas fa-expand"></i> Show Full Content
            </button>
        </div>
    `;
}

// 显示完整内容的模态框
function showFullContent(clipId, type, textContent = null) {
    let content = '';
    let title = 'Full Content';

    if (type === 'markdown' && clipId) {
        const clip = clips.find(c => c.id === clipId);
        if (clip) {
            content = `<div class="markdown-content fullscreen-content">${renderMarkdown(clip.content)}</div>`;
            title = clip.title || 'Markdown Content';
        }
    } else if (type === 'text' && textContent) {
        content = `<div class="text-content fullscreen-content"><p>${escapeHtml(textContent)}</p></div>`;
        title = 'Text Content';
    }

    // 创建全屏内容模态框
    const modal = document.createElement('div');
    modal.className = 'modal fullscreen-content-modal';
    modal.innerHTML = `
        <div class="modal-content fullscreen-modal-content">
            <div class="modal-header">
                <h3>${escapeHtml(title)}</h3>
                <button class="btn-close" onclick="closeFullContentModal()">&times;</button>
            </div>
            <div class="modal-body fullscreen-modal-body">
                ${content}
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.style.display = 'flex';

    // ESC 键关闭
    const handleEsc = (e) => {
        if (e.key === 'Escape') {
            closeFullContentModal();
            document.removeEventListener('keydown', handleEsc);
        }
    };
    document.addEventListener('keydown', handleEsc);
}

// 关闭全屏内容模态框
function closeFullContentModal() {
    const modal = document.querySelector('.fullscreen-content-modal');
    if (modal) {
        modal.remove();
    }
}

function detectMarkdown(content) {
    if (!content) return false;

    // Simple markdown detection patterns
    const markdownPatterns = [
        /^#{1,6}\s+/m,           // Headers
        /\*\*.*?\*\*/,           // Bold
        /\*.*?\*/,               // Italic
        /`.*?`/,                 // Inline code
        /```[\s\S]*?```/,        // Code blocks
        /^\s*[-*+]\s+/m,         // Unordered lists
        /^\s*\d+\.\s+/m,         // Ordered lists
        /\[.*?\]\(.*?\)/,        // Links
        /^\s*>\s+/m,             // Blockquotes
        /\|.*?\|/,               // Tables
    ];

    return markdownPatterns.some(pattern => pattern.test(content));
}

function autoDetectMarkdown() {
    const markdownCheckbox = document.getElementById('isMarkdown');
    const clipType = document.getElementById('clipType').value;

    // 只在 text 类型且 Markdown 选项可见时才自动检测
    if (!markdownCheckbox || markdownCheckbox.checked) return;
    if (clipType !== 'text') return;
    if (markdownCheckbox.closest('.checkbox-label').style.display === 'none') return;

    let content = '';
    if (codeMirrorEditor) {
        content = codeMirrorEditor.getValue();
    } else {
        const textarea = document.getElementById('clipContent');
        content = textarea ? textarea.value : '';
    }

    if (detectMarkdown(content)) {
        markdownCheckbox.checked = true;
        toggleMarkdownMode();
        showToast('Markdown syntax detected - enabled Markdown rendering', 'info');
    }
}

// CodeMirror Editor
let codeMirrorEditor = null;

// Enhanced Markdown editor functionality
function setupMarkdownEditor() {
    const contentTextarea = document.getElementById('clipContent');
    const markdownCheckbox = document.getElementById('isMarkdown');
    const previewToggle = document.getElementById('previewToggle');
    const fullscreenToggle = document.getElementById('fullscreenToggle');
    const editorTheme = document.getElementById('editorTheme');
    const editorControls = document.getElementById('editorControls');
    const editorStatus = document.getElementById('editorStatus');

    if (!contentTextarea || !markdownCheckbox) return;

    // Initialize CodeMirror
    initializeCodeMirror(contentTextarea);

    // Toggle markdown mode
    markdownCheckbox.addEventListener('change', toggleMarkdownMode);

    // Preview toggle
    if (previewToggle) {
        previewToggle.addEventListener('click', togglePreview);
    }

    // Fullscreen toggle
    if (fullscreenToggle) {
        fullscreenToggle.addEventListener('click', toggleFullscreen);
    }

    // Theme selector
    if (editorTheme) {
        editorTheme.addEventListener('change', changeEditorTheme);
    }

    // ESC key to exit fullscreen
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && isFullscreen) {
            toggleFullscreen();
        }
    });
}

function initializeCodeMirror(textarea) {
    if (typeof CodeMirror === 'undefined') {
        console.warn('CodeMirror not loaded, falling back to textarea');
        return;
    }

    codeMirrorEditor = CodeMirror.fromTextArea(textarea, {
        mode: 'text/plain',
        theme: 'default',
        lineNumbers: true,
        lineWrapping: true,
        autoCloseBrackets: true,
        matchBrackets: true,
        styleActiveLine: true,
        foldGutter: false, // 暂时禁用折叠功能
        gutters: ["CodeMirror-linenumbers"], // 只保留行号
        viewportMargin: Infinity, // 改善大文档性能
        extraKeys: {
            "Ctrl-Space": "autocomplete",
            "Ctrl-/": "toggleComment",
            "Ctrl-F": "findPersistent",
            "F11": function(cm) {
                toggleFullscreen();
            },
            "Esc": function(cm) {
                if (isFullscreen) {
                    toggleFullscreen();
                }
            },
            "Tab": function(cm) {
                if (cm.somethingSelected()) {
                    cm.indentSelection("add");
                } else {
                    cm.replaceSelection("    ");
                }
            },
            "Ctrl-Enter": function(cm) {
                // 快速保存
                if (typeof saveClip === 'function') {
                    saveClip();
                }
            }
        },
        placeholder: "Paste or type your content here..."
    });

    // Update status bar
    codeMirrorEditor.on('cursorActivity', updateEditorStatus);
    codeMirrorEditor.on('change', function() {
        updateEditorStatus();
        // Auto-detect markdown
        setTimeout(autoDetectMarkdown, 500);
    });

    updateEditorStatus();

    // 强制刷新布局以确保行号正确显示
    setTimeout(() => {
        if (codeMirrorEditor) {
            codeMirrorEditor.refresh();
            // 强制重新计算布局
            const gutters = codeMirrorEditor.getWrapperElement().querySelector('.CodeMirror-gutters');
            if (gutters) {
                gutters.style.left = '0px';
                gutters.style.position = 'absolute';
                gutters.style.height = '100%';
                gutters.style.maxHeight = 'none';
                gutters.style.overflow = 'visible';
            }
        }
    }, 100);
}

let isFullscreen = false;

function toggleMarkdownMode() {
    const markdownCheckbox = document.getElementById('isMarkdown');
    const editorControls = document.getElementById('editorControls');
    const editorStatus = document.getElementById('editorStatus');
    const editorContainer = document.querySelector('.editor-container');

    if (markdownCheckbox.checked) {
        editorControls.style.display = 'flex';
        editorStatus.style.display = 'flex';
        editorContainer.classList.add('markdown-mode');

        // Switch to markdown mode
        if (codeMirrorEditor) {
            codeMirrorEditor.setOption('mode', 'gfm');
            codeMirrorEditor.setOption('extraKeys', {
                ...codeMirrorEditor.getOption('extraKeys'),
                "Enter": "newlineAndIndentContinueMarkdownList"
            });
            // 刷新编辑器以应用新的高度
            setTimeout(() => codeMirrorEditor.refresh(), 100);
        }
    } else {
        editorControls.style.display = 'none';
        editorStatus.style.display = 'none';
        editorContainer.classList.remove('markdown-mode');

        // Switch back to plain text
        if (codeMirrorEditor) {
            codeMirrorEditor.setOption('mode', 'text/plain');
            setTimeout(() => codeMirrorEditor.refresh(), 100);
        }

        // Close any open preview modal
        closeEditorPreview();
    }
}

function togglePreview() {
    // 获取当前编辑器内容
    let content = '';
    if (codeMirrorEditor) {
        content = codeMirrorEditor.getValue();
    } else {
        const textarea = document.getElementById('clipContent');
        content = textarea ? textarea.value : '';
    }

    if (!content.trim()) {
        showToast('No content to preview', 'warning');
        return;
    }

    // 使用全屏模态框显示预览
    showEditorPreview(content);
}

// 显示编辑器预览的全屏模态框
function showEditorPreview(content) {
    const title = 'Markdown Preview';
    const renderedContent = `<div class="markdown-content fullscreen-content">${renderMarkdown(content)}</div>`;

    // 创建全屏预览模态框
    const modal = document.createElement('div');
    modal.className = 'modal fullscreen-content-modal editor-preview-modal';
    modal.innerHTML = `
        <div class="modal-content fullscreen-modal-content">
            <div class="modal-header">
                <h3>${escapeHtml(title)}</h3>
                <div class="preview-actions">
                    <button class="btn btn-sm btn-outline" onclick="refreshEditorPreview()">
                        <i class="fas fa-sync"></i> Refresh
                    </button>
                    <button class="btn-close" onclick="closeEditorPreview()">&times;</button>
                </div>
            </div>
            <div class="modal-body fullscreen-modal-body">
                <div id="editorPreviewContent">
                    ${renderedContent}
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.style.display = 'flex';

    // ESC 键关闭
    const handleEsc = (e) => {
        if (e.key === 'Escape') {
            closeEditorPreview();
            document.removeEventListener('keydown', handleEsc);
        }
    };
    document.addEventListener('keydown', handleEsc);
}

// 刷新编辑器预览内容
function refreshEditorPreview() {
    let content = '';
    if (codeMirrorEditor) {
        content = codeMirrorEditor.getValue();
    } else {
        const textarea = document.getElementById('clipContent');
        content = textarea ? textarea.value : '';
    }

    const previewContent = document.getElementById('editorPreviewContent');
    if (previewContent) {
        if (content.trim()) {
            previewContent.innerHTML = `<div class="markdown-content fullscreen-content">${renderMarkdown(content)}</div>`;
        } else {
            previewContent.innerHTML = '<p style="color: var(--text-secondary); font-style: italic; text-align: center; margin-top: 2rem;">No content to preview...</p>';
        }
    }
}

// 关闭编辑器预览模态框
function closeEditorPreview() {
    const modal = document.querySelector('.editor-preview-modal');
    if (modal) {
        modal.remove();
    }
}

function toggleFullscreen() {
    const editorContainer = document.querySelector('.editor-container');
    const fullscreenToggle = document.getElementById('fullscreenToggle');

    isFullscreen = !isFullscreen;

    if (isFullscreen) {
        editorContainer.classList.add('fullscreen');
        fullscreenToggle.innerHTML = '<i class="fas fa-compress"></i>';
        fullscreenToggle.title = 'Exit Fullscreen (ESC)';

        // 创建全屏工具栏
        createFullscreenToolbar();

        // 刷新编辑器
        if (codeMirrorEditor) {
            setTimeout(() => {
                codeMirrorEditor.refresh();
                codeMirrorEditor.focus();
            }, 100);
        }
    } else {
        editorContainer.classList.remove('fullscreen');
        fullscreenToggle.innerHTML = '<i class="fas fa-expand"></i>';
        fullscreenToggle.title = 'Fullscreen (F11)';

        // 移除全屏工具栏
        removeFullscreenToolbar();

        // 刷新编辑器
        if (codeMirrorEditor) {
            setTimeout(() => codeMirrorEditor.refresh(), 100);
        }
    }
}

function createFullscreenToolbar() {
    const editorContainer = document.querySelector('.editor-container');
    const existingToolbar = editorContainer.querySelector('.fullscreen-toolbar');

    if (existingToolbar) {
        existingToolbar.remove();
    }

    const toolbar = document.createElement('div');
    toolbar.className = 'fullscreen-toolbar';

    toolbar.innerHTML = `
        <button type="button" id="fullscreenPreviewToggle" class="btn btn-sm btn-outline">
            <i class="fas fa-eye"></i> Preview
        </button>
        <select id="fullscreenEditorTheme" class="form-select-sm">
            <option value="default">Light</option>
            <option value="material">Dark</option>
        </select>
        <button type="button" onclick="toggleFullscreen()" class="btn btn-sm btn-outline">
            <i class="fas fa-times"></i> Exit
        </button>
    `;

    editorContainer.appendChild(toolbar);

    // 绑定事件
    const fullscreenPreviewToggle = toolbar.querySelector('#fullscreenPreviewToggle');
    const fullscreenEditorTheme = toolbar.querySelector('#fullscreenEditorTheme');

    if (fullscreenPreviewToggle) {
        fullscreenPreviewToggle.addEventListener('click', togglePreview);
    }

    if (fullscreenEditorTheme) {
        fullscreenEditorTheme.value = document.getElementById('editorTheme').value;
        fullscreenEditorTheme.addEventListener('change', function() {
            document.getElementById('editorTheme').value = this.value;
            changeEditorTheme();
        });
    }
}

function removeFullscreenToolbar() {
    const toolbar = document.querySelector('.fullscreen-toolbar');
    if (toolbar) {
        toolbar.remove();
    }
}

function changeEditorTheme() {
    const editorTheme = document.getElementById('editorTheme');
    const theme = editorTheme.value;

    if (codeMirrorEditor) {
        codeMirrorEditor.setOption('theme', theme);
    }
}

function updateEditorStatus() {
    const editorInfo = document.getElementById('editorInfo');
    const editorPosition = document.getElementById('editorPosition');

    if (!codeMirrorEditor || !editorInfo || !editorPosition) return;

    const cursor = codeMirrorEditor.getCursor();
    const selection = codeMirrorEditor.getSelection();
    const lineCount = codeMirrorEditor.lineCount();
    const content = codeMirrorEditor.getValue();

    // Update position info
    editorPosition.textContent = `Line ${cursor.line + 1}, Col ${cursor.ch + 1}`;

    // Update general info
    let info = `${lineCount} lines, ${content.length} chars`;
    if (selection) {
        info += `, ${selection.length} selected`;
    }
    editorInfo.textContent = info;
}

function setEditorMode(mode) {
    const contentEditor = document.getElementById('contentEditor');
    const markdownPreview = document.getElementById('markdownPreview');
    const editorContainer = document.querySelector('.content-editor-container');
    const editBtn = document.getElementById('editBtn');
    const previewBtn = document.getElementById('previewBtn');
    const splitBtn = document.getElementById('splitBtn');

    currentEditorMode = mode;

    // Reset button states
    [editBtn, previewBtn, splitBtn].forEach(btn => {
        if (btn) btn.classList.remove('active');
    });

    // Reset container classes
    editorContainer.classList.remove('split-view');

    switch (mode) {
        case 'edit':
            contentEditor.style.display = 'block';
            markdownPreview.style.display = 'none';
            if (editBtn) editBtn.classList.add('active');
            break;

        case 'preview':
            updatePreview();
            contentEditor.style.display = 'none';
            markdownPreview.style.display = 'block';
            if (previewBtn) previewBtn.classList.add('active');
            break;

        case 'split':
            updatePreview();
            contentEditor.style.display = 'block';
            markdownPreview.style.display = 'block';
            editorContainer.classList.add('split-view');
            if (splitBtn) splitBtn.classList.add('active');
            break;
    }
}

function updatePreview() {
    const previewContent = document.querySelector('#markdownPreview .preview-content');

    if (!previewContent) return;

    let content = '';
    if (codeMirrorEditor) {
        content = codeMirrorEditor.getValue();
    } else {
        const textarea = document.getElementById('clipContent');
        content = textarea ? textarea.value : '';
    }

    if (content.trim()) {
        previewContent.innerHTML = renderMarkdown(content);
    } else {
        previewContent.innerHTML = '<p style="color: var(--text-secondary); font-style: italic;">Nothing to preview...</p>';
    }
}

function handleMarkdownShortcuts(e) {
    if (!e.ctrlKey && !e.metaKey) return;

    const textarea = e.target;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);

    let replacement = null;

    switch (e.key) {
        case 'b': // Bold
            e.preventDefault();
            replacement = `**${selectedText || 'bold text'}**`;
            break;
        case 'i': // Italic
            e.preventDefault();
            replacement = `*${selectedText || 'italic text'}*`;
            break;
        case 'k': // Link
            e.preventDefault();
            const url = prompt('Enter URL:');
            if (url) {
                replacement = `[${selectedText || 'link text'}](${url})`;
            }
            break;
        case '`': // Code
            e.preventDefault();
            replacement = `\`${selectedText || 'code'}\``;
            break;
    }

    if (replacement) {
        insertTextAtCursor(textarea, replacement, start, end);
    }
}

function insertTextAtCursor(textarea, text, start, end) {
    const before = textarea.value.substring(0, start);
    const after = textarea.value.substring(end);

    textarea.value = before + text + after;

    // Set cursor position
    const newCursorPos = start + text.length;
    textarea.setSelectionRange(newCursorPos, newCursorPos);
    textarea.focus();

    // Update preview if needed
    if (currentEditorMode === 'preview' || currentEditorMode === 'split') {
        updatePreview();
    }
}

// Toolbar functions
function insertMarkdown(before, after, placeholder) {
    const textarea = document.getElementById('clipContent');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);

    let replacement;
    if (selectedText) {
        replacement = before + selectedText + after;
    } else {
        replacement = before + placeholder + after;
    }

    insertTextAtCursor(textarea, replacement, start, end);

    // Select the placeholder text if no text was selected
    if (!selectedText && placeholder) {
        const placeholderStart = start + before.length;
        const placeholderEnd = placeholderStart + placeholder.length;
        textarea.setSelectionRange(placeholderStart, placeholderEnd);
    }
}

function insertLink() {
    const textarea = document.getElementById('clipContent');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = textarea.value.substring(start, end);

    const url = prompt('Enter URL:', 'https://');
    if (url) {
        const linkText = selectedText || 'link text';
        const replacement = `[${linkText}](${url})`;
        insertTextAtCursor(textarea, replacement, start, end);
    }
}

function insertTable() {
    const textarea = document.getElementById('clipContent');
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;

    const table = `| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |`;

    insertTextAtCursor(textarea, table, start, end);
}

function handleTabKey(e) {
    if (e.key === 'Tab') {
        e.preventDefault();
        const textarea = e.target;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;

        // Insert tab character
        insertTextAtCursor(textarea, '    ', start, end);
    }
}

function toggleMarkdownHelp() {
    const helpText = document.querySelector('.markdown-help small');
    const isExpanded = helpText.innerHTML.includes('Show less');

    if (isExpanded) {
        helpText.innerHTML = `
            <strong>Markdown Quick Reference:</strong>
            **bold** *italic* \`code\` [link](url) # Header
            <a href="#" onclick="toggleMarkdownHelp(); return false;">Show more...</a>
        `;
    } else {
        helpText.innerHTML = `
            <strong>Markdown Quick Reference:</strong><br>
            **bold** *italic* \`code\` [link](url)<br>
            # Header 1 ## Header 2 ### Header 3<br>
            - List item 1<br>
            1. Numbered list<br>
            > Blockquote<br>
            \`\`\`code block\`\`\`<br>
            | Table | Header |<br>
            |-------|--------|<br>
            | Cell  | Cell   |<br>
            <strong>Shortcuts:</strong> Ctrl+B (bold), Ctrl+I (italic), Ctrl+K (link), Ctrl+\` (code)<br>
            <a href="#" onclick="toggleMarkdownHelp(); return false;">Show less...</a>
        `;
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
            <i class="fas fa-${getToastIcon(type)}"></i>
            <span>${message}</span>
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Search and filter handlers
async function handleSearch(e) {
    const query = e.target.value.toLowerCase();

    if (!query.trim()) {
        // If search is empty, reload all clips
        await loadClips();
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/clips/search?q=${encodeURIComponent(query)}`, {
            headers: getAuthHeaders()
        });

        if (response.ok) {
            const data = await response.json();
            clips = data.clips || [];
            renderClips();
        } else {
            // Fallback to client-side search if server search fails
            const filteredClips = clips.filter(clip =>
                (clip.title && clip.title.toLowerCase().includes(query)) ||
                (clip.content && clip.content.toLowerCase().includes(query))
            );
            const originalClips = clips;
            clips = filteredClips;
            renderClips();
            // Restore original clips for next search
            setTimeout(() => { clips = originalClips; }, 100);
        }
    } catch (error) {
        console.error('Search error:', error);
        // Fallback to client-side search
        const filteredClips = clips.filter(clip =>
            (clip.title && clip.title.toLowerCase().includes(query)) ||
            (clip.content && clip.content.toLowerCase().includes(query))
        );
        const originalClips = clips;
        clips = filteredClips;
        renderClips();
        setTimeout(() => { clips = originalClips; }, 100);
    }
}

function handleFilterChange() {
    const typeFilter = document.getElementById('typeFilter').value;
    const sortFilter = document.getElementById('sortFilter').value;

    // Apply filters and sorting
    applyFiltersAndSort(typeFilter, sortFilter);
}

function applyFiltersAndSort(typeFilter, sortFilter) {
    let filteredClips = [...clips];

    // Apply type filter
    if (typeFilter) {
        filteredClips = filteredClips.filter(clip => clip.clip_type === typeFilter);
    }

    // Apply sorting
    switch (sortFilter) {
        case 'recent':
            filteredClips.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            break;
        case 'accessed':
            filteredClips.sort((a, b) => new Date(b.last_accessed) - new Date(a.last_accessed));
            break;
        case 'pinned':
            filteredClips.sort((a, b) => {
                if (a.is_pinned && !b.is_pinned) return -1;
                if (!a.is_pinned && b.is_pinned) return 1;
                return new Date(b.created_at) - new Date(a.created_at);
            });
            break;
        default:
            filteredClips.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }

    // Temporarily replace clips for rendering
    const originalClips = clips;
    clips = filteredClips;
    renderClips();
    clips = originalClips;
}

// Clip actions
async function copyToClipboard(clipId) {
    try {
        const clip = clips.find(c => c.id === clipId);
        if (!clip) return;

        let textToCopy = clip.content || '';

        // If it's a file clip, copy the file names
        if (clip.clip_type === 'file' && clip.files && clip.files.length > 0) {
            textToCopy = clip.files.map(file => file.original_filename || file.filename).join('\n');
        }

        await navigator.clipboard.writeText(textToCopy);
        showToast('Copied to clipboard!', 'success');
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        showToast('Failed to copy to clipboard', 'error');
    }
}

async function downloadFile(fileId) {
    try {
        // Fetch file with authentication headers
        const response = await fetch(`${API_BASE}/files/${fileId}/download`, {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error(`Download failed: ${response.status}`);
        }

        // Get filename from response headers or use default
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'download';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }

        // Create blob and download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        showToast('File downloaded successfully!', 'success');
    } catch (error) {
        console.error('Download error:', error);
        showToast('Failed to download file', 'error');
    }
}

function editClip(clipId) {
    const clip = clips.find(c => c.id === clipId);
    if (!clip) return;

    // Open modal in edit mode
    document.getElementById('clipModal').classList.add('show');
    document.getElementById('modalTitle').textContent = 'Edit Clip';

    // Fill form with clip data
    document.getElementById('clipTitle').value = clip.title || '';

    // Set content in CodeMirror or textarea
    if (codeMirrorEditor) {
        codeMirrorEditor.setValue(clip.content || '');
    } else {
        document.getElementById('clipContent').value = clip.content || '';
    }

    document.getElementById('clipType').value = clip.clip_type;
    document.getElementById('accessLevel').value = clip.access_level;

    // 只有在支持 Markdown 的类型时才设置 Markdown 状态
    if (clip.clip_type === 'text' || clip.clip_type === 'markdown') {
        document.getElementById('isMarkdown').checked = clip.is_markdown || false;
    } else {
        document.getElementById('isMarkdown').checked = false;
    }

    // Store clip ID for update
    document.getElementById('clipForm').dataset.editId = clipId;

    // Handle files if it's a file clip
    if (clip.clip_type === 'file' && clip.files && clip.files.length > 0) {
        showExistingFiles(clip.files);
    }

    // 先处理类型变化，再处理 Markdown 模式
    handleClipTypeChange();
    handleAccessLevelChange();

    // 只有在显示 Markdown 选项时才更新 Markdown UI 状态
    const markdownCheckbox = document.getElementById('isMarkdown');
    if (markdownCheckbox && markdownCheckbox.closest('.checkbox-label').style.display !== 'none') {
        toggleMarkdownMode();
    }
}

function showExistingFiles(files) {
    const fileUpload = document.getElementById('fileUpload');

    if (files.length === 1) {
        const file = files[0];
        fileUpload.innerHTML = `
            <div class="existing-file">
                <i class="fas fa-file" style="color: #007bff; font-size: 2rem; margin-bottom: 0.5rem;"></i>
                <p><strong>Current file:</strong> ${escapeHtml(file.original_filename)}</p>
                <small>${formatFileSize(file.file_size)} • ${file.mime_type}</small>
                <div style="margin-top: 1rem;">
                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="downloadFile(${file.id})">
                        <i class="fas fa-download"></i> Download
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="replaceFile()">
                        <i class="fas fa-upload"></i> Replace
                    </button>
                </div>
            </div>
        `;
    } else {
        fileUpload.innerHTML = `
            <div class="existing-files">
                <i class="fas fa-files" style="color: #007bff; font-size: 2rem; margin-bottom: 0.5rem;"></i>
                <p><strong>Current files:</strong> ${files.length} files</p>
                <div class="file-list" style="max-height: 150px; overflow-y: auto; margin: 1rem 0;">
                    ${files.map(file => `
                        <div class="file-item" style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; border: 1px solid #ddd; border-radius: 0.25rem; margin-bottom: 0.5rem;">
                            <div>
                                <strong>${escapeHtml(file.original_filename)}</strong><br>
                                <small>${formatFileSize(file.file_size)} • ${file.mime_type}</small>
                            </div>
                            <button type="button" class="btn btn-sm btn-outline-primary" onclick="downloadFile(${file.id})">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                    `).join('')}
                </div>
                <button type="button" class="btn btn-sm btn-outline-secondary" onclick="replaceFile()">
                    <i class="fas fa-upload"></i> Replace All Files
                </button>
            </div>
        `;
    }
}

function replaceFile() {
    const fileUpload = document.getElementById('fileUpload');
    fileUpload.innerHTML = `
        <i class="fas fa-cloud-upload-alt"></i>
        <p>Drag & drop files here or click to browse</p>
        <input type="file" id="fileInput" multiple>
    `;

    // Re-setup file upload events
    setupFileUpload();
}

async function togglePin(clipId) {
    try {
        const clip = clips.find(c => c.id === clipId);
        const endpoint = clip.is_pinned ? 'unpin' : 'pin';
        const method = clip.is_pinned ? 'DELETE' : 'POST';
        
        const response = await fetch(`${API_BASE}/clips/${clipId}/pin`, {
            method,
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const updatedClip = await response.json();
            const index = clips.findIndex(c => c.id === clipId);
            clips[index] = updatedClip;
            renderClips();
            showToast(`Clip ${updatedClip.is_pinned ? 'pinned' : 'unpinned'}`, 'success');
        }
    } catch (error) {
        console.error('Error toggling pin:', error);
        showToast('Failed to update pin status', 'error');
    }
}

async function shareClip(shareToken) {
    const shareUrl = `${window.location.origin}/shared/${shareToken}`;

    try {
        // Create a modal to show the share link
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'block';

        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Share Clip</h3>
                    <button class="close-btn" onclick="this.parentNode.parentNode.parentNode.remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <p>Share this link with others:</p>
                    <div class="share-link-container">
                        <input type="text" id="shareUrlInput" value="${shareUrl}" readonly class="share-input" />
                        <button class="btn btn-primary" onclick="copyShareLink()">
                            <i class="fas fa-copy"></i> Copy
                        </button>
                    </div>
                    <div class="share-info">
                        <i class="fas fa-info-circle"></i>
                        <span>Anyone with this link can access this clip</span>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Select the input for easy copying
        const input = document.getElementById('shareUrlInput');
        input.select();

        // Add copy function to window
        window.copyShareLink = function() {
            input.select();
            document.execCommand('copy');
            showToast('Share link copied to clipboard!', 'success');
        };

        // Also copy to clipboard automatically
        await navigator.clipboard.writeText(shareUrl);
        showToast('Share link copied to clipboard!', 'success');
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        showToast('Failed to copy share link', 'error');
    }
}

async function deleteClip(clipId) {
    if (!confirm('Are you sure you want to delete this clip?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/clips/${clipId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            clips = clips.filter(c => c.id !== clipId);
            renderClips();
            showToast('Clip deleted successfully', 'success');
        }
    } catch (error) {
        console.error('Error deleting clip:', error);
        showToast('Failed to delete clip', 'error');
    }
}
