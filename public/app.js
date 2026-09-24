// TalentMatch AI - Frontend Application State & Controller
let currentSessionId = "";
let currentSessionName = "Recruitment_Drive";
let currentCompany = "ABC Corp";
let currentScreeningMode = "persistent";
let currentJdTitle = "";
let currentJdText = "";
let selectedFiles = [];
let sampleJds = [];
let sampleResumes = [];
let currentRankings = [];
let allSessionsList = [];

const MAX_CLIENT_BATCH_BYTES = 10 * 1024 * 1024; // 10 MB total limit

// Helper for resilient Vercel serverless & local API calls
async function safeApiFetch(endpoint, options = {}) {
    try {
        let res = await fetch(endpoint, options);
        if (res.status === 404 && endpoint.includes("/api/")) {
            const fallbackPath = endpoint.replace("/api/", "/");
            res = await fetch(fallbackPath, options);
        }
        return res;
    } catch (e) {
        if (endpoint.includes("/api/")) {
            const fallbackPath = endpoint.replace("/api/", "/");
            return await fetch(fallbackPath, options);
        }
        throw e;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initNavigation();
    initDropzone();
    checkHealth();
    loadSampleData();
    loadSessionsList();
    loadLatestRankings();
    loadEvaluationData();
});

// Tab Switcher
function initNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");
            switchTab(targetTab);
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(el => el.classList.remove("active"));

    const activeNav = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
    const activePane = document.getElementById(tabId);

    if (activeNav) activeNav.classList.add("active");
    if (activePane) activePane.classList.add("active");
}

// Health Check Endpoint
async function checkHealth() {
    try {
        const res = await safeApiFetch("/api/health");
        const data = await res.json();
        const badgeText = document.getElementById("engineStatusText");
        const badgeDot = document.querySelector("#engineStatusBadge .status-dot");
        
        if (data.llm_engine) {
            badgeText.textContent = `Engine: ${data.llm_engine}`;
        } else {
            badgeText.textContent = "Engine: Offline NLP Engine";
        }
        if (badgeDot) badgeDot.className = "status-dot green";
    } catch (e) {
        console.warn("Health check failed:", e);
        document.getElementById("engineStatusText").textContent = "Engine: Offline NLP Engine";
    }
}

// Update Screening Mode Toggle UI
function updateModeUI() {
    const radios = document.getElementsByName("screeningMode");
    for (const r of radios) {
        if (r.checked) {
            currentScreeningMode = r.value;
        }
    }

    const pLbl = document.getElementById("modePersistentLbl");
    const tLbl = document.getElementById("modeTemporaryLbl");

    if (pLbl && tLbl) {
        pLbl.classList.toggle("active", currentScreeningMode === "persistent");
        tLbl.classList.toggle("active", currentScreeningMode === "temporary");
    }
}

// Load Stored Sessions
async function loadSessionsList() {
    try {
        const res = await safeApiFetch("/api/sessions");
        if (!res.ok) return;
        const data = await res.json();
        allSessionsList = data.sessions || [];

        const select = document.getElementById("activeSessionSelect");
        if (!select) return;

        if (allSessionsList.length === 0) {
            select.innerHTML = `<option value="">-- No Active Sessions Found --</option>`;
            return;
        }

        select.innerHTML = `<option value="">-- Select Active Session (${allSessionsList.length}) --</option>` +
            allSessionsList.map(s => `
                <option value="${s.id}" ${s.id === currentSessionId ? 'selected' : ''}>
                    ${s.session_name} (${s.total_candidates} candidates) [${s.mode}]
                </option>
            `).join("");
    } catch (e) {
        console.warn("Error loading sessions list:", e);
    }
}

// Switch Active Session
async function switchSession(sessionId) {
    if (!sessionId) return;
    try {
        const res = await safeApiFetch(`/api/sessions/${sessionId}/rankings`);
        if (!res.ok) return;
        const data = await res.json();
        
        currentSessionId = data.session_id;
        currentSessionName = data.session_name || "Recruitment Session";
        currentCompany = data.company || "Company";
        currentScreeningMode = data.mode || "persistent";
        currentJdTitle = data.jd_title || "";
        currentJdText = data.jd_text || "";
        currentRankings = data.rankings || [];

        // Update UI inputs
        document.getElementById("companyInput").value = currentCompany;
        document.getElementById("jdTitleInput").value = currentJdTitle;
        document.getElementById("sessionNameInput").value = currentSessionName;
        document.getElementById("jdTextInput").value = currentJdText;

        const radios = document.getElementsByName("screeningMode");
        for (const r of radios) {
            if (r.value === currentScreeningMode) r.checked = true;
        }
        updateModeUI();

        renderRankingResults(data);
        switchTab("tab-ranking");
    } catch (e) {
        console.error("Error switching session:", e);
    }
}

// Load Latest Rankings on Startup
async function loadLatestRankings() {
    try {
        if (window.FirebaseService && window.FirebaseService.isFirebaseConnected()) {
            const cloudData = await window.FirebaseService.getLatestScreeningFromFirebase();
            if (cloudData && cloudData.rankings && cloudData.rankings.length > 0) {
                currentSessionId = cloudData.session_id || cloudData.id || "";
                currentSessionName = cloudData.session_name || "Cloud Session";
                currentCompany = cloudData.company || "Company";
                currentScreeningMode = cloudData.mode || "persistent";
                currentRankings = cloudData.rankings;
                currentJdTitle = cloudData.jd_title || "";
                renderRankingResults(cloudData);
                return;
            }
        }
    } catch (cloudErr) {
        console.warn("Firebase cloud load notice, checking local database:", cloudErr);
    }

    try {
        const res = await safeApiFetch("/api/rankings/latest");
        if (!res.ok) return;
        const data = await res.json();
        if (data && data.rankings && data.rankings.length > 0) {
            currentSessionId = data.session_id || "";
            currentSessionName = data.session_name || "Drive Session";
            currentCompany = data.company || "Company";
            currentScreeningMode = data.mode || "persistent";
            currentRankings = data.rankings;
            currentJdTitle = data.jd_title || "";
            renderRankingResults(data);
        } else {
            renderEmptyRankingState();
        }
    } catch (e) {
        console.error("Error loading saved database rankings:", e);
        renderEmptyRankingState();
    }
}

function renderEmptyRankingState() {
    const subTitle = document.getElementById("rankingSubTitle");
    const countBadge = document.getElementById("candidateCountBadge");
    const activeBadge = document.getElementById("activeSessionBadge");
    const tbody = document.getElementById("rankingTableBody");

    if (subTitle) subTitle.textContent = "Select a Job Description and upload resumes to view candidate rankings.";
    if (countBadge) countBadge.textContent = "0 Candidates Ranked";
    if (activeBadge) activeBadge.textContent = "Session: None";
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-muted">
                    <i class="fa-solid fa-inbox me-2" style="font-size:1.2rem; color:var(--text-muted);"></i>
                    No screening results found in database. Click <strong>"1-Click Examiner Demo"</strong> or upload resumes to run screening.
                </td>
            </tr>
        `;
    }
}

// Load Samples from API
async function loadSampleData() {
    try {
        const [jdRes, resRes] = await Promise.all([
            safeApiFetch("/api/sample-jds"),
            safeApiFetch("/api/sample-resumes")
        ]);

        const jdData = await jdRes.json();
        const resData = await resRes.json();

        sampleJds = jdData.sample_jds || [];
        sampleResumes = resData.sample_resumes || [];

        renderSampleJds();
        renderSampleResumes();

        if (sampleJds.length > 0 && !currentJdTitle) {
            selectSampleJd(0);
        }
    } catch (e) {
        console.error("Error loading sample data:", e);
    }
}

function renderSampleJds() {
    const container = document.getElementById("sampleJdList");
    if (!container) return;

    container.innerHTML = sampleJds.map((jd, idx) => `
        <button class="sample-jd-btn" onclick="selectSampleJd(${idx})">
            <strong>${jd.title}</strong>
            <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:0.2rem;">${jd.experience_required || 'Campus Placement'} | ${jd.department || 'Engineering'}</div>
        </button>
    `).join("");
}

function selectSampleJd(index) {
    const jd = sampleJds[index];
    if (!jd) return;

    currentJdTitle = jd.title;
    currentJdText = jd.text;
    currentCompany = "ABC Corp";
    currentSessionName = `ABC_${jd.title.replace(/[^a-zA-Z0-9]/g, "")}_2026`;

    document.getElementById("companyInput").value = currentCompany;
    document.getElementById("jdTitleInput").value = jd.title || "";
    document.getElementById("sessionNameInput").value = currentSessionName;
    document.getElementById("jdTextInput").value = jd.text || "";
}

function renderSampleResumes() {
    const container = document.getElementById("sampleResumesList");
    if (!container) return;

    container.innerHTML = sampleResumes.map(cand => `
        <div class="file-item mb-2">
            <div>
                <strong>${cand.name}</strong>
                <div style="font-size:0.75rem; color:var(--text-secondary);">${cand.education}</div>
            </div>
            <span class="pill pill-green">${(cand.skills || []).slice(0, 3).join(", ")}</span>
        </div>
    `).join("");
}

// Session Setup Confirmation
function confirmSessionSetup() {
    const jdTitle = document.getElementById("jdTitleInput").value.trim();
    const jdText = document.getElementById("jdTextInput").value.trim();
    const company = document.getElementById("companyInput").value.trim() || "ABC Corp";
    const sessionName = document.getElementById("sessionNameInput").value.trim() || `${company}_${jdTitle.replace(/[^a-zA-Z0-9]/g, "")}_2026`;

    if (!jdText) {
        alert("Please enter or select a Job Description text first.");
        return;
    }

    currentJdTitle = jdTitle || "Job Position";
    currentJdText = jdText;
    currentCompany = company;
    currentSessionName = sessionName;
    updateModeUI();

    switchTab("tab-upload");
}

// // File Upload & Multi-File Validation
function initDropzone() {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("pdfFileInput");
    if (!dropzone || !fileInput) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.style.borderColor = "var(--accent-color)";
            dropzone.style.background = "var(--accent-light)";
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.style.borderColor = "var(--border-color)";
            dropzone.style.background = "transparent";
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0) {
            processSelectedFilesArray(Array.from(dt.files));
        }
    }, false);
}

function handleFileSelect(event) {
    if (event.target && event.target.files) {
        processSelectedFilesArray(Array.from(event.target.files));
    }
}

function processSelectedFilesArray(newFiles) {
    const errBox = document.getElementById("uploadValidationError");
    if (errBox) {
        errBox.style.display = "none";
        errBox.textContent = "";
    }

    for (const f of newFiles) {
        if (!selectedFiles.some(existing => existing.name === f.name && existing.size === f.size)) {
            if (!f.name.toLowerCase().endsWith(".pdf")) {
                showUploadError(`File '${f.name}' is not a PDF document. Only PDF resumes are supported.`);
                continue;
            }
            if (f.size === 0) {
                showUploadError(`File '${f.name}' is empty (0 bytes). Skipping.`);
                continue;
            }
            selectedFiles.push(f);
        }
    }

    renderSelectedFiles();
}

function showUploadError(msg) {
    const errBox = document.getElementById("uploadValidationError");
    if (errBox) {
        errBox.style.display = "block";
        errBox.textContent = msg;
    }
}

function renderSelectedFiles() {
    const container = document.getElementById("selectedFileList");
    const summaryHeader = document.getElementById("selectedFilesSummaryHeader");
    const clearBtn = document.getElementById("btnClearFiles");
    const errBox = document.getElementById("uploadValidationError");

    if (selectedFiles.length === 0) {
        container.innerHTML = `<span class="no-files">No files uploaded yet.</span>`;
        if (summaryHeader) summaryHeader.textContent = "Selected Resumes: 0 files";
        if (clearBtn) clearBtn.style.display = "none";
        return;
    }

    const totalBytes = selectedFiles.reduce((acc, f) => acc + f.size, 0);
    const totalMb = (totalBytes / (1024 * 1024)).toFixed(2);

    if (summaryHeader) {
        summaryHeader.innerHTML = `Selected Resumes: <strong>${selectedFiles.length} files</strong> (${totalMb} MB total)`;
    }
    if (clearBtn) clearBtn.style.display = "inline-block";

    // Total size limit check
    if (totalBytes > MAX_CLIENT_BATCH_BYTES) {
        showUploadError(`Maximum upload size exceeded (Total: ${totalMb} MB, Limit: 10 MB). Please upload fewer or smaller files.`);
    }

    container.innerHTML = selectedFiles.map((file, idx) => {
        const fileKb = (file.size / 1024).toFixed(1);
        return `
            <div class="file-item">
                <div class="file-info">
                    <i class="fa-solid fa-file-pdf text-red" style="font-size:1.1rem;"></i>
                    <div>
                        <strong>${file.name}</strong>
                        <div class="file-size">${fileKb} KB</div>
                    </div>
                </div>
                <button style="background:none; border:none; color:var(--red); font-size:1.2rem; cursor:pointer;" onclick="removeFile(${idx})" title="Remove file">&times;</button>
            </div>
        `;
    }).join("");
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderSelectedFiles();
}

function clearSelectedFiles() {
    selectedFiles = [];
    document.getElementById("pdfFileInput").value = "";
    renderSelectedFiles();
}

async function parseResponseError(res, defaultMsg) {
    try {
        const text = await res.text();
        try {
            const json = JSON.parse(text);
            return json.detail || json.message || text || defaultMsg;
        } catch {
            return text || defaultMsg;
        }
    } catch {
        return `HTTP ${res.status} Error`;
    }
}

// Screen Uploaded Resumes
async function processScreening() {
    const jdTitle = document.getElementById("jdTitleInput").value.trim() || currentJdTitle || "Specified Job Position";
    const jdText = document.getElementById("jdTextInput").value.trim() || currentJdText;
    const company = document.getElementById("companyInput").value.trim() || currentCompany || "Company";
    const sessionName = document.getElementById("sessionNameInput").value.trim() || currentSessionName || `${company}_${jdTitle.replace(/[^a-zA-Z0-9]/g, "")}_2026`;

    if (!jdText) {
        alert("Please enter or select a Job Description text first.");
        switchTab("tab-jd");
        return;
    }

    if (selectedFiles.length === 0 && (!currentRankings || currentRankings.length === 0)) {
        alert("Please select at least one PDF resume file to upload or click '1-Click Examiner Demo'.");
        return;
    }

    switchTab("tab-ranking");
    document.getElementById("resultsLoader").style.display = "block";
    document.getElementById("resultsContent").style.display = "none";
    
    const progressNotice = document.getElementById("uploadProgressNotice");
    if (progressNotice) progressNotice.style.display = "block";

    const formData = new FormData();
    formData.append("jd_title", jdTitle);
    formData.append("jd_text", jdText);
    formData.append("company", company);
    formData.append("session_name", sessionName);
    formData.append("mode", currentScreeningMode);
    if (currentSessionId) {
        formData.append("session_id", currentSessionId);
    }

    selectedFiles.forEach(file => {
        formData.append("files", file);
    });

    try {
        const res = await safeApiFetch("/api/screen-resumes", {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            const errMsg = await parseResponseError(res, "Screening failed");
            throw new Error(errMsg);
        }

        const data = await res.json();
        currentSessionId = data.session_id;
        currentSessionName = data.session_name;
        currentCompany = data.company;
        currentScreeningMode = data.mode;
        currentRankings = data.rankings || [];
        currentJdTitle = data.jd_title || jdTitle;

        renderRankingResults(data);
        loadSessionsList();
        clearSelectedFiles();

        // Auto-save session payload to Firebase Cloud
        autoSaveToFirebase(data);
    } catch (e) {
        alert("Error screening resumes: " + e.message);
    } finally {
        document.getElementById("resultsLoader").style.display = "none";
        document.getElementById("resultsContent").style.display = "block";
        if (progressNotice) progressNotice.style.display = "none";
    }
}

// 1-Click Examiner Demo
async function runOneClickDemo() {
    switchTab("tab-ranking");
    document.getElementById("resultsLoader").style.display = "block";
    document.getElementById("resultsContent").style.display = "none";

    try {
        const res = await safeApiFetch("/api/screen-sample-demo", { method: "POST" });
        if (!res.ok) {
            const errMsg = await parseResponseError(res, "Demo failed");
            throw new Error(errMsg);
        }
        const data = await res.json();

        currentSessionId = data.session_id;
        currentSessionName = data.session_name;
        currentCompany = data.company;
        currentScreeningMode = data.mode;
        currentRankings = data.rankings || [];
        currentJdTitle = data.jd_title || "Senior Software Engineer (SDE)";

        renderRankingResults(data);
        loadSessionsList();

        // Auto-save demo screening to Firebase Cloud
        autoSaveToFirebase(data);
    } catch (e) {
        alert("Error running demo: " + e.message);
    } finally {
        document.getElementById("resultsLoader").style.display = "none";
        document.getElementById("resultsContent").style.display = "block";
    }
}

// Auto-Save helper to sync screening payload to Firebase
function autoSaveToFirebase(data) {
    const mode = (data && data.mode) ? data.mode : currentScreeningMode;
    
    // In Temporary Screening Mode, do NOT automatically store session to Firebase Cloud
    if (mode === "temporary") {
        console.log("ℹ️ Temporary screening mode active. Skipping automatic Firebase Cloud save.");
        const countBadge = document.getElementById("candidateCountBadge");
        if (countBadge) {
            const total = (data && data.total_candidates !== undefined) ? data.total_candidates : (currentRankings ? currentRankings.length : 0);
            countBadge.innerHTML = `${total} Candidates Ranked <span style="font-size:0.7rem; color:var(--amber); margin-left:4px;"><i class="fa-solid fa-bolt"></i> Temporary Session</span>`;
        }
        return;
    }

    if (window.FirebaseService && window.FirebaseService.isFirebaseConnected()) {
        const payload = {
            session_id: data.session_id || currentSessionId,
            session_name: data.session_name || currentSessionName,
            company: data.company || currentCompany,
            mode: mode,
            jd_title: data.jd_title || currentJdTitle,
            required_skills: data.required_skills || [],
            total_candidates: data.total_candidates || (data.rankings ? data.rankings.length : 0),
            rankings: data.rankings || currentRankings
        };

        window.FirebaseService.saveScreeningToFirebase(payload).then(docId => {
            if (docId) {
                console.log("☁️ Auto-synced screening session to Firebase Firestore!");
                const countBadge = document.getElementById("candidateCountBadge");
                if (countBadge) {
                    countBadge.innerHTML = `${payload.total_candidates} Candidates Ranked <span style="font-size:0.7rem; color:var(--amber); margin-left:4px;"><i class="fa-solid fa-cloud-check"></i> Cloud Synced</span>`;
                }
            }
        });
    }
}

// Firebase History Modal Functions
async function saveCurrentSessionToCloud() {
    if (!currentRankings || currentRankings.length === 0) {
        alert("No candidate rankings available in current session to save.");
        return;
    }

    if (!window.FirebaseService || !window.FirebaseService.isFirebaseConnected()) {
        alert("Firebase Cloud Service is currently initializing or offline. Please check your connection.");
        return;
    }

    const payload = {
        session_id: currentSessionId,
        session_name: currentSessionName,
        company: currentCompany,
        mode: currentScreeningMode,
        jd_title: currentJdTitle || "Job Position",
        total_candidates: currentRankings.length,
        rankings: currentRankings
    };

    const docId = await window.FirebaseService.saveScreeningToFirebase(payload);
    if (docId) {
        alert(`✅ Successfully saved recruitment session '${currentSessionName}' to Firebase Firestore Cloud!\n\nDocument ID: ${docId}`);
        const countBadge = document.getElementById("candidateCountBadge");
        if (countBadge) {
            countBadge.innerHTML = `${currentRankings.length} Candidates Ranked <span style="font-size:0.7rem; color:var(--amber); margin-left:4px;"><i class="fa-solid fa-cloud-check"></i> Saved to Cloud</span>`;
        }
    } else {
        alert("Failed to save session to Firebase.");
    }
}

async function openFirebaseHistoryModal() {
    const modal = document.getElementById("firebaseHistoryModal");
    if (modal) modal.style.display = "flex";

    const loader = document.getElementById("firebaseHistoryLoading");
    const listContainer = document.getElementById("firebaseHistoryList");
    if (loader) loader.style.display = "block";
    if (listContainer) listContainer.innerHTML = "";

    if (!window.FirebaseService || !window.FirebaseService.isFirebaseConnected()) {
        if (loader) loader.style.display = "none";
        if (listContainer) listContainer.innerHTML = `<div class="text-center text-red py-3"><i class="fa-solid fa-triangle-exclamation"></i> Firebase Cloud is offline or initializing. Please retry in a moment.</div>`;
        return;
    }

    const sessions = await window.FirebaseService.getAllScreeningsFromFirebase();
    if (loader) loader.style.display = "none";

    if (!sessions || sessions.length === 0) {
        listContainer.innerHTML = `
            <div class="text-center py-4 text-muted">
                <i class="fa-solid fa-inbox mb-2" style="font-size:1.5rem; color:var(--text-muted);"></i>
                <p>No screening sessions stored in Firebase Firestore yet.</p>
                <div style="font-size:0.8rem; margin-top:0.4rem;">Run screening or 1-Click Demo to populate Firebase Cloud!</div>
            </div>
        `;
        return;
    }

    window._firebaseSessionsCache = sessions;

    listContainer.innerHTML = sessions.map((sess) => {
        const total = sess.total_candidates || (sess.rankings ? sess.rankings.length : 0);
        const dateStr = sess.created_at ? new Date(sess.created_at).toLocaleString() : 'Recent';
        const modeColor = sess.mode === 'temporary' ? 'var(--amber)' : 'var(--green)';

        return `
            <div class="card p-3 mb-2" style="background:var(--bg-dark); border:1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center; gap:1rem;">
                <div>
                    <h4 style="font-size:0.95rem; margin-bottom:0.2rem; color:var(--text-primary);">
                        <i class="fa-solid fa-briefcase text-blue"></i> ${sess.session_name || sess.jd_title || 'Position'}
                    </h4>
                    <div style="font-size:0.75rem; color:var(--text-secondary);">
                        <i class="fa-solid fa-users text-amber"></i> ${total} Candidates &nbsp;|&nbsp; 
                        <span style="color:${modeColor}; font-weight:600;">${(sess.mode || 'persistent').toUpperCase()}</span> &nbsp;|&nbsp;
                        <i class="fa-solid fa-clock"></i> ${dateStr}
                    </div>
                </div>
                <button class="btn btn-primary" style="padding:0.35rem 0.75rem; font-size:0.8rem;" onclick="loadFirebaseSession('${sess.id}')">
                    <i class="fa-solid fa-folder-open"></i> Load
                </button>
            </div>
        `;
    }).join("");
}

function loadFirebaseSession(sessionId) {
    if (!window._firebaseSessionsCache) return;
    const sess = window._firebaseSessionsCache.find(s => s.id === sessionId);
    if (!sess) return;

    currentSessionId = sess.session_id || sess.id;
    currentSessionName = sess.session_name || "Cloud Session";
    currentCompany = sess.company || "Company";
    currentScreeningMode = sess.mode || "persistent";
    currentRankings = sess.rankings || [];
    currentJdTitle = sess.jd_title || "Job Position";

    renderRankingResults(sess);
    closeFirebaseModal();

    const countBadge = document.getElementById("candidateCountBadge");
    if (countBadge) {
        countBadge.innerHTML = `${sess.total_candidates || currentRankings.length} Candidates Ranked <span style="font-size:0.7rem; color:var(--amber); margin-left:4px;"><i class="fa-solid fa-cloud-check"></i> Loaded from Firebase</span>`;
    }
}

function closeFirebaseModal() {
    const modal = document.getElementById("firebaseHistoryModal");
    if (modal) modal.style.display = "none";
}

// Render Leaderboard & Table
function renderRankingResults(data) {
    const totalCandidates = (data && data.total_candidates !== undefined) ? data.total_candidates : (currentRankings ? currentRankings.length : 0);
    const jdTitle = (data && data.jd_title) ? data.jd_title : (currentJdTitle || "Job Position");
    const sessionName = (data && data.session_name) ? data.session_name : (currentSessionName || "Recruitment Drive");
    const mode = (data && data.mode) ? data.mode : currentScreeningMode;

    const subTitle = document.getElementById("rankingSubTitle");
    if (subTitle) {
        subTitle.textContent = `Screened ${totalCandidates} candidates for ${jdTitle} (${sessionName})`;
    }

    const countBadge = document.getElementById("candidateCountBadge");
    if (countBadge) {
        countBadge.textContent = `${totalCandidates} Candidates Ranked`;
    }

    const activeBadge = document.getElementById("activeSessionBadge");
    if (activeBadge) {
        const modeBadgeColor = mode === 'temporary' ? 'var(--amber)' : 'var(--green)';
        activeBadge.innerHTML = `Session: <strong>${sessionName}</strong> | Mode: <span style="color:${modeBadgeColor}; font-weight:700;">${mode.toUpperCase()}</span>`;
    }

    renderTableRows(currentRankings);
}

function renderTableRows(rankingsList) {
    const tbody = document.getElementById("rankingTableBody");
    if (!tbody) return;

    if (!rankingsList || rankingsList.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4">No candidates found for this session.</td></tr>`;
        return;
    }

    tbody.innerHTML = rankingsList.map(cand => {
        const rankClass = cand.rank === 1 ? "top-1" : cand.rank === 2 ? "top-2" : cand.rank === 3 ? "top-3" : "normal";
        const matchingPills = (cand.matching_skills || []).map(s => `<span class="pill pill-green">${s}</span>`).join(" ");
        const missingPills = (cand.missing_skills || []).map(s => `<span class="pill pill-red">${s}</span>`).join(" ");
        const semanticSim = cand.scores_breakdown ? (cand.scores_breakdown.semantic_similarity ?? 0) : 0;

        return `
            <tr>
                <td><span class="rank-badge ${rankClass}">#${cand.rank}</span></td>
                <td>
                    <strong>${cand.candidate_name || 'Candidate'}</strong>
                    <div style="font-size:0.75rem; color:var(--text-secondary);">${cand.filename || 'PDF Resume'}</div>
                </td>
                <td>
                    <strong style="color:var(--green); font-size:1.1rem;">${cand.overall_match_percentage}%</strong>
                    <div style="font-size:0.7rem; color:var(--text-muted);">Similarity: ${semanticSim}%</div>
                </td>
                <td><div class="pills-container">${matchingPills || '<span class="text-muted">None</span>'}</div></td>
                <td><div class="pills-container">${missingPills || '<span class="text-muted">None</span>'}</div></td>
                <td>
                    <button class="btn btn-secondary" style="padding:0.35rem 0.75rem; font-size:0.8rem;" onclick="openCandidateModal('${cand.candidate_id}')">
                        <i class="fa-solid fa-eye"></i> View Details
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

// Real-time Leaderboard Filter
function filterCandidateTable() {
    const q = document.getElementById("candidateSearchInput").value.toLowerCase().trim();
    if (!q) {
        renderTableRows(currentRankings);
        return;
    }

    const filtered = currentRankings.filter(c => {
        const nameMatch = (c.candidate_name || "").toLowerCase().includes(q);
        const fileMatch = (c.filename || "").toLowerCase().includes(q);
        const skillMatch = (c.matching_skills || []).some(s => s.toLowerCase().includes(q));
        return nameMatch || fileMatch || skillMatch;
    });

    renderTableRows(filtered);
}

// Candidate Detail View Modal
function openCandidateModal(candId) {
    const cand = currentRankings.find(c => String(c.candidate_id) === String(candId));
    if (!cand) return;

    const breakdown = cand.scores_breakdown || {};

    document.getElementById("modalCandName").textContent = cand.candidate_name || "Unknown Candidate";
    document.getElementById("modalCandRank").textContent = `Rank #${cand.rank}`;
    document.getElementById("modalOverallScore").textContent = `${cand.overall_match_percentage}%`;
    
    document.getElementById("modalSemScore").textContent = `${breakdown.semantic_similarity ?? 0}%`;
    document.getElementById("modalSkillScore").textContent = `${breakdown.skill_coverage ?? breakdown.skill_match ?? 0}%`;
    document.getElementById("modalEduScore").textContent = `${breakdown.education ?? breakdown.qualification_match ?? 0}%`;
    document.getElementById("modalExpScore").textContent = `${breakdown.experience ?? 60}%`;
    document.getElementById("modalProjScore").textContent = `${breakdown.project_relevance ?? 50}%`;

    document.getElementById("modalExplanationText").textContent = cand.explanation || "No explanation rationale available.";

    document.getElementById("modalMatchingPills").innerHTML = (cand.matching_skills && cand.matching_skills.length > 0)
        ? cand.matching_skills.map(s => `<span class="pill pill-green">${s}</span>`).join(" ")
        : "<span class='text-muted'>None identified</span>";

    document.getElementById("modalMissingPills").innerHTML = (cand.missing_skills && cand.missing_skills.length > 0)
        ? cand.missing_skills.map(s => `<span class="pill pill-red">${s}</span>`).join(" ")
        : "<span class='text-muted'>None (Fully Matched)</span>";

    const eduList = (cand.education && cand.education.length > 0) ? cand.education.join(", ") : "Bachelor's Degree (Inferred)";
    const expYears = (cand.experience_years !== undefined && cand.experience_years !== null) ? cand.experience_years : 0;
    const projList = (cand.projects && cand.projects.length > 0) ? `<div class="mt-2"><strong>Projects:</strong> ${cand.projects.slice(0, 3).join("; ")}</div>` : "";

    document.getElementById("modalEducationText").innerHTML = `
        <div><strong>Education:</strong> ${eduList}</div>
        <div class="mt-1"><strong>Experience:</strong> ${expYears} Years</div>
        ${projList}
    `;

    document.getElementById("candidateModal").style.display = "flex";
}

function closeModal() {
    document.getElementById("candidateModal").style.display = "none";
}

// Recruiter Actions: Excel & CSV Exporters
function toggleExportCountInput() {
    const scope = document.querySelector('input[name="exportScope"]:checked').value;
    const input = document.getElementById("exportTopNInput");
    if (input) {
        input.style.display = scope === "top_n" ? "inline-block" : "none";
    }
}

function getExportData() {
    if (!currentRankings || currentRankings.length === 0) return [];
    
    const scope = document.querySelector('input[name="exportScope"]:checked').value;
    let list = [...currentRankings];

    if (scope === "top_n") {
        const topNVal = parseInt(document.getElementById("exportTopNInput").value, 10) || 50;
        list = list.slice(0, topNVal);
    }
    return list;
}

function exportResults(format) {
    const candidates = getExportData();
    if (candidates.length === 0) {
        alert("No candidate rankings available to export.");
        return;
    }

    const dateStr = new Date().toISOString().split("T")[0];
    const safeTitle = (currentJdTitle || "Position").replace(/[^a-zA-Z0-9]/g, "_");
    const fileName = `Recruitment_Rankings_${safeTitle}_${dateStr}.${format === 'excel' ? 'xls' : 'csv'}`;

    if (format === 'csv') {
        exportToCSV(candidates, fileName);
    } else {
        exportToExcel(candidates, fileName);
    }
}

function exportToCSV(candidates, fileName) {
    const headers = [
        "Rank", "Candidate Name", "Resume Filename", "Match Score (%)", 
        "Semantic Similarity (%)", "Matched Skills", "Missing Skills", 
        "Job Title", "Recruitment Session", "Screening Date"
    ];

    const rows = candidates.map(c => [
        c.rank,
        `"${(c.candidate_name || '').replace(/"/g, '""')}"`,
        `"${(c.filename || '').replace(/"/g, '""')}"`,
        c.overall_match_percentage,
        c.scores_breakdown ? c.scores_breakdown.semantic_similarity : 0,
        `"${(c.matching_skills || []).join(', ').replace(/"/g, '""')}"`,
        `"${(c.missing_skills || []).join(', ').replace(/"/g, '""')}"`,
        `"${(currentJdTitle || '').replace(/"/g, '""')}"`,
        `"${(currentSessionName || '').replace(/"/g, '""')}"`,
        new Date().toLocaleDateString()
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function exportToExcel(candidates, fileName) {
    // Generates Excel-compatible HTML spreadsheet format
    let tableHtml = `
        <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
        <head>
            <!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet>
            <x:Name>Candidates Ranking</x:Name>
            <x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions>
            </x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]-->
            <meta charset="utf-8">
            <style>
                th { background-color: #1e293b; color: #ffffff; font-weight: bold; border: 1px solid #334155; padding: 8px; }
                td { border: 1px solid #cbd5e1; padding: 8px; vertical-align: top; }
                .rank { font-weight: bold; text-align: center; }
                .score { font-weight: bold; color: #10b981; text-align: right; }
            </style>
        </head>
        <body>
            <h2>Recruitment Ranking Report — ${currentJdTitle || 'Job Position'}</h2>
            <p><strong>Session:</strong> ${currentSessionName} | <strong>Mode:</strong> ${currentScreeningMode.toUpperCase()} | <strong>Date:</strong> ${new Date().toLocaleString()}</p>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Candidate Name</th>
                        <th>Resume Filename</th>
                        <th>Matching Score (%)</th>
                        <th>Semantic Similarity (%)</th>
                        <th>Matched Skills</th>
                        <th>Missing Skills</th>
                        <th>Job Position</th>
                    </tr>
                </thead>
                <tbody>
    `;

    candidates.forEach(c => {
        tableHtml += `
            <tr>
                <td class="rank">#${c.rank}</td>
                <td>${c.candidate_name || 'Candidate'}</td>
                <td>${c.filename || ''}</td>
                <td class="score">${c.overall_match_percentage}%</td>
                <td>${c.scores_breakdown ? c.scores_breakdown.semantic_similarity : 0}%</td>
                <td>${(c.matching_skills || []).join(', ')}</td>
                <td>${(c.missing_skills || []).join(', ')}</td>
                <td>${currentJdTitle || ''}</td>
            </tr>
        `;
    });

    tableHtml += `</tbody></table></body></html>`;

    const blob = new Blob([tableHtml], { type: 'application/vnd.ms-excel' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Clear Session Cleanup Actions
function confirmClearSession() {
    if (!currentSessionId) {
        alert("No active screening session to clear.");
        return;
    }
    const nameEl = document.getElementById("clearSessionNameText");
    if (nameEl) nameEl.textContent = `'${currentSessionName}'`;
    document.getElementById("clearSessionModal").style.display = "flex";
}

function closeClearSessionModal() {
    document.getElementById("clearSessionModal").style.display = "none";
}

async function exportAndClearSession() {
    exportResults('excel');
    closeClearSessionModal();
    await executeClearSession();
}

async function executeClearSession() {
    closeClearSessionModal();
    if (!currentSessionId) return;

    try {
        const res = await safeApiFetch(`/api/sessions/${currentSessionId}/clear`, { method: "POST" });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Clear session failed");
        }

        if (window.FirebaseService) {
            await window.FirebaseService.deleteSessionFromFirebase(currentSessionId);
        }

        alert(`✅ Recruitment session '${currentSessionName}' cleared successfully.`);
        currentRankings = [];
        currentSessionId = "";
        renderEmptyRankingState();
        loadSessionsList();
    } catch (e) {
        alert("Error clearing session: " + e.message);
    }
}

function confirmClearAll() {
    document.getElementById("clearAllModal").style.display = "flex";
}

function closeClearAllModal() {
    document.getElementById("clearAllModal").style.display = "none";
}

async function executeClearAll() {
    closeClearAllModal();
    try {
        const res = await safeApiFetch("/api/sessions/clear-all", { method: "DELETE" });
        if (!res.ok) throw new Error("Clear all failed");

        if (window.FirebaseService) {
            await window.FirebaseService.deleteAllSessionsFromFirebase();
        }

        alert("✅ All recruitment screening data cleared successfully.");
        currentRankings = [];
        currentSessionId = "";
        renderEmptyRankingState();
        loadSessionsList();
    } catch (e) {
        alert("Error clearing all data: " + e.message);
    }
}

// Model Evaluation Benchmark Data
async function loadEvaluationData() {
    try {
        const res = await safeApiFetch("/api/evaluation");
        const data = await res.json();

        if (data.total_evaluated_pairs !== undefined) {
            const pairSpan = document.getElementById("valTotalPairs");
            if (pairSpan) pairSpan.textContent = data.total_evaluated_pairs;
        }
        if (data.total_test_jobs !== undefined) {
            const jobSpan = document.getElementById("valTotalJobs");
            if (jobSpan) jobSpan.textContent = data.total_test_jobs;
        }

        if (data.metrics) {
            document.getElementById("valPrecision").textContent = `${(data.metrics.precision * 100).toFixed(1)}%`;
            document.getElementById("valRecall").textContent = `${(data.metrics.recall * 100).toFixed(1)}%`;
            document.getElementById("valF1").textContent = `${(data.metrics.f1_score * 100).toFixed(1)}%`;
            document.getElementById("valTop1").textContent = `${(data.metrics.top_1_accuracy * 100).toFixed(1)}%`;
            document.getElementById("valTop3").textContent = `${(data.metrics.top_3_accuracy * 100).toFixed(1)}%`;

            if (data.confusion_matrix) {
                document.getElementById("cmTP").textContent = data.confusion_matrix.TP;
                document.getElementById("cmFP").textContent = data.confusion_matrix.FP;
                document.getElementById("cmFN").textContent = data.confusion_matrix.FN;
                document.getElementById("cmTN").textContent = data.confusion_matrix.TN;
            }

            const evalTbody = document.getElementById("evalTableBody");
            if (evalTbody && data.case_breakdown) {
                evalTbody.innerHTML = data.case_breakdown.map(c => `
                    <tr>
                        <td><strong>${c.job_title}</strong></td>
                        <td>${c.ground_truth_top}</td>
                        <td>${c.predicted_top}</td>
                        <td><span class="pill ${c.top_1_matched ? 'pill-green' : 'pill-red'}">${c.top_1_matched ? 'MATCH' : 'MISMATCH'}</span></td>
                        <td><span class="pill ${c.top_3_matched ? 'pill-green' : 'pill-red'}">${c.top_3_matched ? 'MATCH' : 'MISMATCH'}</span></td>
                    </tr>
                `).join("");
            }
        }
    } catch (e) {
        console.error("Evaluation load error:", e);
    }
}
