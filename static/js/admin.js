// Admin Controller
let adminPin = ""; // Requirement 1: Never keep open sessions, require PIN verification on every visit/reload
let currentQuestionDuration = 15;
let currentTransitionDelay = 5;
let isAutoMode = false;
let activeFolderId = "default";
let cachedFolders = [];

// Check / Prompt Admin PIN
function showAdminAuthModal(errorMsg = "") {
    const modal = document.getElementById("modal-admin-auth");
    if (!modal) return;
    modal.style.display = "flex";
    modal.classList.remove("hidden");
    modal.classList.add("flex");
    const errorEl = document.getElementById("admin-auth-error");
    if (errorEl) {
        if (errorMsg) {
            errorEl.innerText = errorMsg;
            errorEl.classList.remove("hidden");
        } else {
            errorEl.classList.add("hidden");
        }
    }
    const input = document.getElementById("input-admin-pin");
    if (input) {
        input.value = "";
        setTimeout(() => input.focus(), 100);
    }
}

function hideAdminAuthModal() {
    const modal = document.getElementById("modal-admin-auth");
    if (!modal) return;
    modal.style.display = "none";
    modal.classList.add("hidden");
    modal.classList.remove("flex");
    const errorEl = document.getElementById("admin-auth-error");
    if (errorEl) errorEl.classList.add("hidden");
}

async function checkAdminAuth() {
    // Clear any previous session; require PIN entry every time
    adminPin = "";
    sessionStorage.removeItem("aura_admin_pin");
    showAdminAuthModal();
}

async function handleAdminAuth(e) {
    if (e && e.preventDefault) e.preventDefault();
    const pinInput = document.getElementById("input-admin-pin");
    const pin = pinInput ? pinInput.value.trim() : "";
    const btn = document.getElementById("btn-admin-login");
    const errorEl = document.getElementById("admin-auth-error");

    if (!pin) {
        if (errorEl) {
            errorEl.innerText = "Lütfen Admin PIN kodunuzu giriniz.";
            errorEl.classList.remove("hidden");
        }
        return;
    }

    if (btn) {
        btn.disabled = true;
        btn.innerText = "Doğrulanıyor...";
    }
    if (errorEl) errorEl.classList.add("hidden");

    try {
        const res = await fetch("/api/admin/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ admin_pin: pin })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            adminPin = pin;
            hideAdminAuthModal();

            try {
                if (window.soundManager && typeof window.soundManager.playCorrect === "function") {
                    window.soundManager.playCorrect();
                }
            } catch(se) {}

            try { loadFolders(); } catch(fe) { console.error(fe); }
            try { loadQuestions(); } catch(qe) { console.error(qe); }
            try { refreshAdminPlayers(); } catch(pe) { console.error(pe); }
        } else {
            const msg = data.detail || "Hatalı Admin PIN kodu!";
            if (errorEl) {
                errorEl.innerText = msg;
                errorEl.classList.remove("hidden");
            } else {
                alert(msg);
            }
        }
    } catch(err) {
        const msg = "Sunucuya bağlanırken bağlantı hatası oluştu.";
        if (errorEl) {
            errorEl.innerText = msg;
            errorEl.classList.remove("hidden");
        } else {
            alert(msg);
        }
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "Giriş Yap";
        }
    }
}

function adminLogout() {
    adminPin = "";
    sessionStorage.removeItem("aura_admin_pin");
    showAdminAuthModal();
    try {
        if (window.soundManager && typeof window.soundManager.playClick === "function") {
            window.soundManager.playClick();
        }
    } catch(e) {}
}

// Tab Switching
function switchAdminTab(tabName) {
    const tabs = ["control", "quizzes", "reports", "security"];
    tabs.forEach(t => {
        const btn = document.getElementById(`tab-btn-${t}`);
        const sec = document.getElementById(`tab-section-${t}`);
        if (t === tabName) {
            btn.className = "admin-tab-btn flex-shrink-0 flex items-center space-x-2 px-5 py-3 rounded-2xl text-xs sm:text-sm font-extrabold bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 transition-all whitespace-nowrap";
            sec.classList.remove("hidden");
        } else {
            btn.className = "admin-tab-btn flex-shrink-0 flex items-center space-x-2 px-5 py-3 rounded-2xl text-xs sm:text-sm font-bold text-slate-400 hover:text-white hover:bg-slate-800/60 transition-all whitespace-nowrap";
            sec.classList.add("hidden");
        }
    });

    if (tabName === "quizzes") {
        loadFolders();
        loadQuestions();
    }
    if (tabName === "security") loadBannedUsers();
    if (tabName === "control") refreshAdminPlayers();
    window.soundManager.playClick();
}

// Admin PIN Change
function openChangePinModal() {
    document.getElementById("modal-change-admin-pin").classList.remove("hidden");
    window.soundManager.playClick();
}

function closeChangePinModal() {
    document.getElementById("modal-change-admin-pin").classList.add("hidden");
    window.soundManager.playClick();
}

async function handleChangeAdminPin(e) {
    e.preventDefault();
    const currPin = document.getElementById("input-current-admin-pin").value.trim();
    const newPin = document.getElementById("input-new-admin-pin").value.trim();
    const confirmPin = document.getElementById("input-confirm-admin-pin").value.trim();

    if (newPin !== confirmPin) {
        alert("Yeni PIN ile PIN tekrarı uyuşmuyor!");
        return;
    }

    const btn = document.getElementById("btn-save-admin-pin");
    btn.disabled = true;
    btn.innerText = "Güncelleniyor...";

    try {
        const res = await fetch("/api/admin/change-pin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                current_pin: currPin,
                new_pin: newPin
            })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            adminPin = newPin;
            sessionStorage.setItem("aura_admin_pin", adminPin);
            closeChangePinModal();
            document.getElementById("input-current-admin-pin").value = "";
            document.getElementById("input-new-admin-pin").value = "";
            document.getElementById("input-confirm-admin-pin").value = "";
            window.soundManager.playCorrect();
            alert("Admin PIN başarıyla güncellendi!");
        } else {
            alert(data.detail || "Admin PIN güncellenemedi!");
        }
    } catch(err) {
        alert("Bağlantı hatası!");
    } finally {
        btn.disabled = false;
        btn.innerText = "Yeni Şifreyi Kaydet";
    }
}

// Room PIN Management
async function generateRandomRoomPin() {
    if (!adminPin) {
        checkAdminAuth();
        return;
    }

    try {
        const res = await fetch("/api/admin/random-pin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ admin_pin: adminPin })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            document.getElementById("admin-pin-display").innerText = data.room_pin;
            window.soundManager.playCorrect();
            alert("Yeni 6 Haneli Rastgele Oda PIN oluşturuldu: " + data.room_pin);
        } else {
            alert(data.detail || "Rastgele PIN üretilemedi!");
        }
    } catch(err) {
        alert("Ağ hatası!");
    }
}

async function updateRoomPin(e) {
    e.preventDefault();
    const newPin = document.getElementById("admin-new-pin").value.trim();
    if (!newPin) return;

    try {
        const res = await fetch("/api/admin/pin", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                admin_pin: adminPin,
                new_room_pin: newPin
            })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            document.getElementById("admin-pin-display").innerText = data.room_pin;
            document.getElementById("admin-new-pin").value = "";
            window.soundManager.playCorrect();
            alert("Oda PIN başarıyla güncellendi: " + data.room_pin);
        } else {
            alert(data.detail || "PIN güncellenemedi!");
        }
    } catch(err) {
        alert("Ağ hatası!");
    }
}

// Independent Question Duration Setting (5s, 10s, 15s, 20s, 30s)
async function setQuestionDuration(seconds) {
    currentQuestionDuration = seconds;
    const btns = [5, 10, 15, 20, 30];
    btns.forEach(sec => {
        const b = document.getElementById(`btn-q-timer-${sec}`);
        if (b) {
            if (sec === seconds) {
                b.className = "py-2 rounded-xl border border-indigo-500 bg-indigo-600/20 text-xs font-black text-indigo-300 transition-all";
            } else {
                b.className = "py-2 rounded-xl border border-slate-700 text-xs font-black text-slate-300 hover:border-indigo-500 transition-all";
            }
        }
    });

    try {
        await fetch("/api/admin/timer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                admin_pin: adminPin,
                question_duration: seconds,
                auto_mode: isAutoMode
            })
        });
        window.soundManager.playClick();
    } catch(e) {}
}

// Independent Transition Delay Setting (3s, 5s, 10s)
async function setTransitionDelay(seconds) {
    currentTransitionDelay = seconds;
    const btns = [3, 5, 10];
    btns.forEach(sec => {
        const b = document.getElementById(`btn-trans-${sec}`);
        if (b) {
            if (sec === seconds) {
                b.className = "py-2 rounded-xl border border-indigo-500 bg-indigo-600/20 text-xs font-black text-indigo-300 transition-all";
            } else {
                b.className = "py-2 rounded-xl border border-slate-700 text-xs font-black text-slate-300 hover:border-indigo-500 transition-all";
            }
        }
    });

    try {
        await fetch("/api/admin/timer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                admin_pin: adminPin,
                transition_delay: seconds,
                auto_mode: isAutoMode
            })
        });
        window.soundManager.playClick();
    } catch(e) {}
}

// Toggle Auto Mode
async function toggleAutoMode(checked) {
    isAutoMode = checked;
    try {
        await fetch("/api/admin/timer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                admin_pin: adminPin,
                question_duration: currentQuestionDuration,
                transition_delay: currentTransitionDelay,
                auto_mode: isAutoMode
            })
        });
        window.soundManager.playClick();
    } catch(e) {}
}

// Dispatch Game Flow Action
async function dispatchAction(actionName) {
    if (!adminPin) {
        checkAdminAuth();
        return;
    }

    try {
        const res = await fetch("/api/admin/action", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                admin_pin: adminPin,
                action: actionName
            })
        });
        const data = await res.json();
        if (res.ok) {
            window.soundManager.playClick();
        } else {
            alert(data.detail || "İşlem başarısız!");
        }
    } catch(e) {
        alert("Aksiyon iletilemedi!");
    }
}

// Confirm Reset
function confirmResetRoom() {
    if (confirm("Odayı sıfırlamak istediğinize emin misiniz? Tüm katılımcı listesi ve skorlar temizlenecektir.")) {
        dispatchAction("RESET_ROOM");
    }
}

// Manual Question Modal Management (Requirement 1 & 8)
function openManualQuestionModal() {
    document.getElementById("modal-manual-question").classList.remove("hidden");
    window.soundManager.playClick();
}

function closeManualQuestionModal() {
    document.getElementById("modal-manual-question").classList.add("hidden");
    window.soundManager.playClick();
}

async function handleManualQuestionSubmit(e) {
    e.preventDefault();
    if (!adminPin) {
        checkAdminAuth();
        return;
    }

    const questionText = document.getElementById("mq-question").value.trim();
    const optA = document.getElementById("mq-opt-A").value.trim();
    const optB = document.getElementById("mq-opt-B").value.trim();
    const optC = document.getElementById("mq-opt-C").value.trim();
    const optD = document.getElementById("mq-opt-D").value.trim();
    const correctOpt = document.getElementById("mq-correct").value;
    const difficulty = document.getElementById("mq-difficulty") ? document.getElementById("mq-difficulty").value : "Orta";
    const duration = parseInt(document.getElementById("mq-duration").value) || 15;
    const explanation = document.getElementById("mq-explanation").value.trim();

    const btn = document.getElementById("btn-save-manual-q");
    btn.disabled = true;
    btn.innerText = "Kaydediliyor...";

    try {
        const res = await fetch("/api/admin/questions/manual", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                admin_pin: adminPin,
                question: questionText,
                options: { A: optA, B: optB, C: optC, D: optD },
                correct: correctOpt,
                explanation: explanation,
                duration: duration,
                difficulty: difficulty,
                folder_id: activeFolderId || "default"
            })
        });

        const data = await res.json();
        if (res.ok && data.success) {
            closeManualQuestionModal();
            document.getElementById("mq-question").value = "";
            document.getElementById("mq-opt-A").value = "";
            document.getElementById("mq-opt-B").value = "";
            document.getElementById("mq-opt-C").value = "";
            document.getElementById("mq-opt-D").value = "";
            document.getElementById("mq-explanation").value = "";
            window.soundManager.playCorrect();
            loadFolders();
            loadQuestions();
            alert("Manuel soru başarıyla eklendi! 🎉");
        } else {
            alert(data.detail || "Soru eklenirken hata oluştu!");
        }
    } catch(err) {
        alert("Bağlantı hatası!");
    } finally {
        btn.disabled = false;
        btn.innerText = "Soruyu Kaydet ve Listeye Ekle ✓";
    }
}

// Delete Question
async function deleteQuestion(qId) {
    if (!adminPin) return;
    if (!confirm("Bu soruyu listeden silmek istediğinize emin misiniz?")) return;

    try {
        const res = await fetch(`/api/admin/questions/${encodeURIComponent(qId)}?admin_pin=${encodeURIComponent(adminPin)}`, {
            method: "DELETE"
        });
        const data = await res.json();
        if (res.ok && data.success) {
            window.soundManager.playClick();
            loadFolders();
            loadQuestions();
        } else {
            alert(data.detail || "Soru silinemedi!");
        }
    } catch(e) {
        alert("Ağ hatası!");
    }
}

// Folder Management (Requirement 8)
async function loadFolders() {
    if (!adminPin) return;
    try {
        const res = await fetch(`/api/admin/folders?admin_pin=${encodeURIComponent(adminPin)}`);
        const data = await res.json();
        if (res.ok && data.folders) {
            cachedFolders = data.folders;
            const container = document.getElementById("quiz-folders-container");
            const badge = document.getElementById("folders-total-badge");
            const selectEl = document.getElementById("ai-folder-select");
            const mqFolderSelect = document.getElementById("mq-folder");

            if (badge) badge.innerText = `${data.folders.length} Klasör`;

            const folderOptions = data.folders.map(f => {
                const fTitle = f.title || f.name || "Genel Soru Seti";
                const fCount = f.questions_count ?? f.question_count ?? (f.questions ? f.questions.length : 0);
                return `<option value="${f.id}" ${f.is_active ? 'selected' : ''}>${escapeHtml(fTitle)} (${fCount} Soru)</option>`;
            }).join("");

            if (selectEl) selectEl.innerHTML = folderOptions;
            if (mqFolderSelect) mqFolderSelect.innerHTML = folderOptions;

            if (!container) return;

            container.innerHTML = data.folders.map(f => {
                const isActive = f.is_active || (f.id === activeFolderId);
                const fTitle = f.title || f.name || "Genel Soru Seti";
                const fCount = f.questions_count ?? f.question_count ?? (f.questions ? f.questions.length : 0);
                return `
                    <div class="p-5 rounded-2xl border transition-all ${isActive ? 'bg-indigo-950/40 border-indigo-500 ring-2 ring-indigo-500/30' : 'bg-slate-950/80 border-slate-800 hover:border-slate-700'}">
                        <div class="flex items-start justify-between mb-3">
                            <div class="flex items-center space-x-3">
                                <div class="w-10 h-10 rounded-xl ${isActive ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400'} flex items-center justify-center font-bold">
                                    <i data-lucide="folder" class="w-5 h-5"></i>
                                </div>
                                <div>
                                    <h4 class="font-extrabold text-sm text-white flex items-center space-x-2">
                                        <span>${escapeHtml(fTitle)}</span>
                                        ${isActive ? '<span class="text-[10px] font-black bg-indigo-500 text-white px-2 py-0.5 rounded-full">AKTİF</span>' : ''}
                                    </h4>
                                    <p class="text-xs text-slate-400 line-clamp-1">${escapeHtml(f.description || 'Açıklama belirtilmedi')}</p>
                                </div>
                            </div>
                            <span class="text-xs font-mono font-black text-indigo-400 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-lg">
                                ${fCount} / 60 Soru
                            </span>
                        </div>

                        <div class="flex items-center justify-between pt-3 border-t border-slate-800/80 text-xs">
                            <button onclick="viewFolderQuestions('${f.id}')" class="text-slate-300 hover:text-white font-bold flex items-center space-x-1">
                                <i data-lucide="eye" class="w-3.5 h-3.5"></i>
                                <span>Soruları Göster</span>
                            </button>
                            <div class="flex items-center space-x-2">
                                ${!isActive ? `
                                    <button onclick="activateFolder('${f.id}')" class="px-2.5 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 font-bold transition-all">
                                        Aktif Yap
                                    </button>
                                ` : ''}
                                ${f.id !== 'default' ? `
                                    <button onclick="deleteFolder('${f.id}')" class="p-1 rounded-lg text-rose-400 hover:bg-rose-500/20 transition-all" title="Klasörü Sil">
                                        <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                                    </button>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }).join("");
            lucide.createIcons();
        }
    } catch(e) {}
}

function viewFolderQuestions(folderId) {
    activeFolderId = folderId;
    loadQuestions();
    window.soundManager.playClick();
}

async function activateFolder(folderId) {
    if (!adminPin) return;
    try {
        const res = await fetch(`/api/admin/folders/${encodeURIComponent(folderId)}/activate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ admin_pin: adminPin })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            activeFolderId = folderId;
            window.soundManager.playCorrect();
            loadFolders();
            loadQuestions();
        } else {
            alert(data.detail || "Klasör aktif edilemedi!");
        }
    } catch(e) {
        alert("Bağlantı hatası!");
    }
}

async function deleteFolder(folderId) {
    if (!adminPin) return;
    if (!confirm("Bu klasörü ve içindeki soruları silmek istediğinize emin misiniz?")) return;
    try {
        const res = await fetch(`/api/admin/folders/${encodeURIComponent(folderId)}?admin_pin=${encodeURIComponent(adminPin)}`, {
            method: "DELETE"
        });
        const data = await res.json();
        if (res.ok && data.success) {
            window.soundManager.playClick();
            if (activeFolderId === folderId) activeFolderId = "default";
            loadFolders();
            loadQuestions();
        } else {
            alert(data.detail || "Klasör silinemedi!");
        }
    } catch(e) {
        alert("Bağlantı hatası!");
    }
}

// Modal 4: Yeni Klasör Oluştur
function openCreateFolderModal() {
    document.getElementById("modal-create-folder").classList.remove("hidden");
    window.soundManager.playClick();
}

function closeCreateFolderModal() {
    document.getElementById("modal-create-folder").classList.add("hidden");
    window.soundManager.playClick();
}

async function handleCreateFolderSubmit(e) {
    e.preventDefault();
    if (!adminPin) {
        checkAdminAuth();
        return;
    }

    const title = document.getElementById("folder-title").value.trim();
    const desc = document.getElementById("folder-desc").value.trim();
    const btn = document.getElementById("btn-submit-create-folder");
    btn.disabled = true;
    btn.innerText = "Oluşturuluyor...";

    try {
        const res = await fetch("/api/admin/folders", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                admin_pin: adminPin,
                name: title,
                description: desc
            })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            closeCreateFolderModal();
            document.getElementById("folder-title").value = "";
            document.getElementById("folder-desc").value = "";
            window.soundManager.playCorrect();
            loadFolders();
            alert("Yeni klasör başarıyla oluşturuldu! 📁");
        } else {
            alert(data.detail || "Klasör oluşturulamadı!");
        }
    } catch(err) {
        alert("Bağlantı hatası!");
    } finally {
        btn.disabled = false;
        btn.innerText = "Klasörü Oluştur 📁";
    }
}

// Modal 5: AI Soru Üretici (Requirement 8 & 9)
function openAiGeneratorModal() {
    document.getElementById("modal-ai-generator").classList.remove("hidden");
    loadFolders(); // Ensure folder list is fresh
    window.soundManager.playClick();
}

function closeAiGeneratorModal() {
    document.getElementById("modal-ai-generator").classList.add("hidden");
    window.soundManager.playClick();
}

function distributeDifficultiesAutomatically(val) {
    const total = parseInt(val) || 0;
    if (total <= 0) return;
    const cokKolay = Math.max(1, Math.round(total * 0.15));
    const kolay = Math.round(total * 0.35);
    const orta = Math.round(total * 0.35);
    const zor = Math.max(1, total - (cokKolay + kolay + orta));

    const elCK = document.getElementById("diff-cok-kolay");
    const elK = document.getElementById("diff-kolay");
    const elO = document.getElementById("diff-orta");
    const elZ = document.getElementById("diff-zor");

    if (elCK) elCK.value = cokKolay;
    if (elK) elK.value = kolay;
    if (elO) elO.value = orta;
    if (elZ) elZ.value = zor;
}

function syncDifficultyInputsToTotal() {
    const ck = parseInt(document.getElementById("diff-cok-kolay").value) || 0;
    const k = parseInt(document.getElementById("diff-kolay").value) || 0;
    const o = parseInt(document.getElementById("diff-orta").value) || 0;
    const z = parseInt(document.getElementById("diff-zor").value) || 0;
    const sum = ck + k + o + z;
    const totalEl = document.getElementById("ai-total-count");
    if (totalEl && sum > 0) {
        totalEl.value = Math.min(50, sum);
    }
}

async function handleAiGenerateSubmit(e) {
    e.preventDefault();
    if (!adminPin) {
        checkAdminAuth();
        return;
    }

    const cokKolay = parseInt(document.getElementById("diff-cok-kolay").value) || 0;
    const kolay = parseInt(document.getElementById("diff-kolay").value) || 0;
    const orta = parseInt(document.getElementById("diff-orta").value) || 0;
    const zor = parseInt(document.getElementById("diff-zor").value) || 0;
    const sumDiffs = cokKolay + kolay + orta + zor;
    const totalCount = sumDiffs > 0 ? Math.min(50, sumDiffs) : (parseInt(document.getElementById("ai-total-count").value) || 30);

    if (totalCount < 1 || totalCount > 50) {
        alert("Tek seferde üretilecek soru sayısı 1 ile 50 arasında olmalıdır!");
        return;
    }

    const btn = document.getElementById("btn-submit-ai-generator");
    const notice = document.getElementById("ai-status-notice");
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">🔄</span> Gemini AI ile Sorular Üretiliyor...`;

    notice.className = "p-3 rounded-xl text-xs font-bold mb-4 bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 block";
    notice.innerText = `Gemini AI ile ${totalCount} özgün soru üretiliyor (Zorluk Dağılımlı: ${cokKolay} Çok Kolay, ${kolay} Kolay, ${orta} Orta, ${zor} Zor)...`;

    try {
        const res = await fetch("/api/admin/generate-questions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                admin_pin: adminPin,
                count: totalCount,
                folder_id: targetFolderId,
                difficulties: {
                    cok_kolay: cokKolay,
                    kolay: kolay,
                    orta: orta,
                    zor: zor
                }
            })
        });

        const data = await res.json();
        if (res.ok && data.success) {
            closeAiGeneratorModal();
            notice.className = "p-3 rounded-xl text-xs font-bold mb-4 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 block";
            notice.innerText = `Harika! Gemini AI ile ${data.count} yeni soru başarıyla üretildi ve "${data.folder_name || 'Klasöre'}" yüklendi. (Toplam soru: ${data.total_questions}/60)`;
            window.soundManager.playCorrect();
            activeFolderId = targetFolderId;
            loadFolders();
            loadQuestions();
            alert(`Gemini AI ile ${data.count} soru üretildi ve başarıyla yüklendi! ✨`);
        } else {
            notice.className = "p-3 rounded-xl text-xs font-bold mb-4 bg-rose-500/10 text-rose-400 border border-rose-500/30 block";
            notice.innerText = "Soru üretilemedi: " + (data.detail || "Bilinmeyen hata");
            alert(data.detail || "Soru üretilemedi!");
        }
    } catch(err) {
        notice.className = "p-3 rounded-xl text-xs font-bold mb-4 bg-rose-500/10 text-rose-400 border border-rose-500/30 block";
        notice.innerText = "Soru üretimi sırasında ağ hatası oluştu.";
        alert("Soru üretimi sırasında bağlantı hatası oluştu.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="sparkles" class="w-4 h-4 mr-1 inline"></i> Soruları Üret ve Klasöre Yükle ✨`;
        lucide.createIcons();
    }
}

// Load Questions Table with Folder & Difficulty Badges
async function loadQuestions() {
    if (!adminPin) return;
    try {
        const res = await fetch(`/api/admin/questions?admin_pin=${encodeURIComponent(adminPin)}`);
        const data = await res.json();
        if (res.ok && data.questions) {
            const tbody = document.getElementById("questions-table-body");
            const titleEl = document.getElementById("active-folder-table-title");
            const countEl = document.getElementById("active-folder-questions-count");

            if (!tbody) return;

            // Filter questions by activeFolderId if set, or show all
            let filtered = data.questions;
            if (activeFolderId) {
                const folderMatch = cachedFolders.find(f => f.id === activeFolderId);
                if (folderMatch && titleEl) {
                    const matchTitle = folderMatch.title || folderMatch.name || "Genel Soru Seti";
                    titleEl.innerText = `${matchTitle} Soruları`;
                }
                const inFolder = data.questions.filter(q => q.folder_id === activeFolderId);
                if (inFolder.length > 0 || cachedFolders.length > 1) {
                    filtered = inFolder;
                }
            }

            if (countEl) {
                countEl.innerText = `${filtered.length} / ${data.total_questions || data.questions.length} Soru (Maks 60)`;
            }

            if (filtered.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="p-6 text-center text-slate-500 font-semibold">Bu klasörde henüz soru bulunmuyor. Manuel ekleyebilir veya AI Soru Üretici ile üretebilirsiniz.</td></tr>`;
                return;
            }

            tbody.innerHTML = filtered.map((q, idx) => `
                <tr class="hover:bg-slate-800/50 transition-colors">
                    <td class="p-3.5 font-mono font-bold text-slate-500">${idx + 1}</td>
                    <td class="p-3.5 font-semibold text-white max-w-sm truncate" title="${escapeHtml(q.question)}">
                        ${escapeHtml(q.question)}
                    </td>
                    <td class="p-3.5">
                        <span class="px-2 py-0.5 rounded-md text-[11px] font-black ${getDifficultyBadgeClass(q.difficulty)}">
                            ${escapeHtml(q.difficulty || 'Orta')}
                        </span>
                    </td>
                    <td class="p-3.5">
                        <span class="px-2.5 py-1 rounded-lg font-mono font-black text-xs ${getCorrectBadgeClass(q.correct)}">
                            ${q.correct}
                        </span>
                    </td>
                    <td class="p-3.5 font-mono text-slate-400 font-bold">${q.duration || 15}s</td>
                    <td class="p-3.5 text-right">
                        <button onclick="deleteQuestion('${q.id}')" class="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 transition-all" title="Soruyu Sil">
                            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                        </button>
                    </td>
                </tr>
            `).join("");
            lucide.createIcons();
        }
    } catch(e) {}
}

function getDifficultyBadgeClass(diff) {
    if (diff === "Çok Kolay") return "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
    if (diff === "Kolay") return "bg-blue-500/20 text-blue-400 border border-blue-500/30";
    if (diff === "Zor") return "bg-rose-500/20 text-rose-400 border border-rose-500/30";
    return "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30";
}

function getCorrectBadgeClass(opt) {
    if (opt === "A") return "bg-red-500/20 text-red-400 border border-red-500/30";
    if (opt === "B") return "bg-blue-500/20 text-blue-400 border border-blue-500/30";
    if (opt === "C") return "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30";
    if (opt === "D") return "bg-green-500/20 text-green-400 border border-green-500/30";
    return "bg-slate-800 text-slate-300";
}

// Export Results Handler (Requirement 3: Excel & PDF)
function exportResults(format) {
    if (!adminPin) {
        checkAdminAuth();
        return;
    }

    const endpoint = format === "excel" ? "/api/admin/export/excel" : "/api/admin/export/pdf";
    const downloadUrl = `${endpoint}?admin_pin=${encodeURIComponent(adminPin)}`;
    window.open(downloadUrl, "_blank");
    window.soundManager.playCorrect();
}

// Banned Users Management (Requirement 9)
async function loadBannedUsers() {
    if (!adminPin) return;
    try {
        const res = await fetch(`/api/admin/banned?admin_pin=${encodeURIComponent(adminPin)}`);
        const data = await res.json();
        const tbody = document.getElementById("banned-table-body");
        if (!tbody) return;

        if (res.ok && data.banned_users && data.banned_users.length > 0) {
            tbody.innerHTML = data.banned_users.map(u => `
                <tr class="hover:bg-slate-800/50 transition-colors">
                    <td class="p-3.5 font-mono font-bold text-white">${escapeHtml(u.identifier)}</td>
                    <td class="p-3.5 font-mono text-amber-400 font-bold">${u.attempts} / 3 İhlal</td>
                    <td class="p-3.5 text-slate-300">${escapeHtml(u.last_attempt_name || '-')}</td>
                    <td class="p-3.5">
                        <span class="px-2.5 py-1 rounded-full text-[11px] font-black bg-rose-500/20 text-rose-400 border border-rose-500/30">
                            Yasaklandı (Ban)
                        </span>
                    </td>
                    <td class="p-3.5 text-right">
                        <button onclick="unbanUser('${escapeHtml(u.identifier)}')" class="px-3 py-1.5 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 font-bold text-xs transition-all active:scale-95">
                            Banı Kaldır ✓
                        </button>
                    </td>
                </tr>
            `).join("");
        } else {
            tbody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-slate-500 font-semibold">Şu anda banlanan kullanıcı bulunmamaktadır.</td></tr>`;
        }
    } catch(e) {}
}

async function unbanUser(identifier) {
    if (!adminPin) return;
    try {
        const res = await fetch("/api/admin/unban", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                admin_pin: adminPin,
                identifier: identifier
            })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            alert(`"${identifier}" kullanıcısının banı başarıyla kaldırıldı!`);
            window.soundManager.playCorrect();
            loadBannedUsers();
        } else {
            alert(data.detail || "Ban kaldırılamadı!");
        }
    } catch(e) {
        alert("Ağ hatası!");
    }
}

// Refresh Live Participants in Admin Dashboard with Manual Score Adjustments (Requirement 7)
async function refreshAdminPlayers() {
    try {
        const res = await fetch("/api/leaderboard?limit=50");
        const players = await res.json();
        const container = document.getElementById("admin-players-container");
        if (!container) return;

        if (!players || players.length === 0) {
            container.innerHTML = `<p class="text-xs text-slate-500 py-4 text-center">Henüz odaya katılan yarışmacı yok.</p>`;
            return;
        }

        container.innerHTML = players.map(p => `
            <div class="flex items-center justify-between p-3 rounded-2xl bg-slate-950 border border-slate-800 text-xs hover:border-slate-700 transition-all">
                <div class="flex items-center space-x-3">
                    <span class="text-2xl">${p.avatar || '🚀'}</span>
                    <div>
                        <span class="font-extrabold text-white text-sm block">${escapeHtml(p.name)}</span>
                        <span class="text-[11px] text-slate-400">${escapeHtml(p.school || 'Diğer')}</span>
                    </div>
                </div>
                <div class="flex items-center space-x-3">
                    <div class="text-right">
                        <span class="font-mono font-black text-sm text-indigo-400 block">${p.score}</span>
                        <span class="text-[10px] text-slate-500 font-bold uppercase">Puan</span>
                    </div>
                    <!-- Score Action Buttons (+100, -100, Custom) -->
                    <div class="flex items-center space-x-1 pl-2 border-l border-slate-800">
                        <button onclick="adjustPlayerScore('${p.id}', 100)" class="w-7 h-7 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 font-black text-xs transition-all active:scale-95 flex items-center justify-center" title="+100 Puan Ekle">
                            +
                        </button>
                        <button onclick="adjustPlayerScore('${p.id}', -100)" class="w-7 h-7 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 border border-rose-500/30 font-black text-xs transition-all active:scale-95 flex items-center justify-center" title="-100 Puan Sil">
                            -
                        </button>
                        <button onclick="promptCustomScore('${p.id}', '${escapeHtml(p.name)}')" class="px-2 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-[11px] transition-all flex items-center justify-center" title="Özel Puan Gir">
                            <i data-lucide="edit-3" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join("");
        lucide.createIcons();
    } catch(e) {}
}

async function adjustPlayerScore(playerId, delta) {
    if (!adminPin) {
        checkAdminAuth();
        return;
    }

    try {
        const res = await fetch("/api/admin/players/score", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                admin_pin: adminPin,
                player_id: playerId,
                score_delta: delta
            })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            window.soundManager.playCorrect();
            refreshAdminPlayers();
        } else {
            alert(data.detail || "Puan güncellenemedi!");
        }
    } catch(e) {
        alert("Bağlantı hatası!");
    }
}

function promptCustomScore(playerId, playerName) {
    const input = prompt(`${playerName} yarışmacısına eklenecek veya çıkarılacak puanı giriniz (Örn: +250 veya -150):`);
    if (input === null) return;
    const delta = parseInt(input.trim());
    if (isNaN(delta) || delta === 0) {
        alert("Lütfen geçerli bir sayı giriniz (0 hariç)!");
        return;
    }
    adjustPlayerScore(playerId, delta);
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Sync State from SSE
function applyState(state) {
    if (!state) return;
    if (state.room_pin) {
        const pinDisplay = document.getElementById("admin-pin-display");
        if (pinDisplay) pinDisplay.innerText = state.room_pin;
    }
    if (state.status) {
        const badge = document.getElementById("admin-status-badge");
        if (badge) {
            badge.innerText = state.status;
            if (state.status === "QUESTION") badge.className = "text-xs font-black px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
            else if (state.status === "REVEAL") badge.className = "text-xs font-black px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30";
            else if (state.status === "PODIUM") badge.className = "text-xs font-black px-2.5 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/30";
            else badge.className = "text-xs font-black px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30";
        }
    }
    if (state.question_duration) {
        currentQuestionDuration = state.question_duration;
    }
    if (state.transition_delay) {
        currentTransitionDelay = state.transition_delay;
    }
    if (typeof state.auto_mode !== "undefined") {
        isAutoMode = state.auto_mode;
        const autoToggle = document.getElementById("toggle-auto-mode");
        if (autoToggle) autoToggle.checked = isAutoMode;
    }
    if (state.theme) {
        updateThemeUI(state.theme);
    }
}

// Theme Dropdown & Switcher (Requirement 2)
function toggleThemeDropdown() {
    const menu = document.getElementById("theme-dropdown-menu");
    if (menu) menu.classList.toggle("hidden");
    window.soundManager.playClick();
}

async function selectTheme(themeId) {
    if (!adminPin) {
        checkAdminAuth();
        return;
    }
    const menu = document.getElementById("theme-dropdown-menu");
    if (menu) menu.classList.add("hidden");

    try {
        const res = await fetch("/api/admin/theme", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                admin_pin: adminPin,
                theme: themeId
            })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            updateThemeUI(data.theme);
            window.soundManager.playCorrect();
        } else {
            alert(data.detail || "Tema değiştirilemedi!");
        }
    } catch(e) {
        alert("Bağlantı hatası!");
    }
}

function updateThemeUI(themeId) {
    if (!themeId) themeId = "default";
    document.body.className = "theme-" + themeId;

    const labels = {
        "default": "Varsayılan",
        "cyberpunk": "Cyberpunk",
        "dark-neon": "Koyu Neon",
        "corporate": "Kurumsal"
    };

    const labelEl = document.getElementById("current-theme-label");
    if (labelEl) labelEl.innerText = `Tema: ${labels[themeId] || "Varsayılan"}`;

    const themes = ["default", "cyberpunk", "dark-neon", "corporate"];
    themes.forEach(t => {
        const checkEl = document.getElementById(`theme-check-${t}`);
        if (checkEl) {
            if (t === themeId) checkEl.classList.remove("hidden");
            else checkEl.classList.add("hidden");
        }

        const btnEl = document.getElementById(`btn-theme-${t}`);
        if (btnEl) {
            if (t === themeId) {
                btnEl.className = "p-2.5 rounded-xl border border-indigo-500 bg-indigo-600/20 text-xs font-bold text-white text-left transition-all";
            } else {
                btnEl.className = "p-2.5 rounded-xl border border-slate-700 text-xs font-bold text-slate-300 hover:border-indigo-500 text-left transition-all";
            }
        }
    });
}

document.addEventListener("click", (e) => {
    const btn = document.getElementById("btn-theme-dropdown");
    const menu = document.getElementById("theme-dropdown-menu");
    if (menu && !menu.classList.contains("hidden") && btn && !btn.contains(e.target) && !menu.contains(e.target)) {
        menu.classList.add("hidden");
    }
});

let firestoreUnsubscribe = null;
function listenToFirestore(roomPin) {
    if (!window.firestoreDb || !roomPin) return;
    if (firestoreUnsubscribe) {
        try { firestoreUnsubscribe(); } catch(e) {}
    }
    try {
        firestoreUnsubscribe = window.firestoreDb.collection("rooms").doc(roomPin).onSnapshot((doc) => {
            if (doc.exists) {
                applyState(doc.data());
            }
        });
    } catch(e) {}
}

// Init
function initAdmin() {
    checkAdminAuth();

    // SSE Stream
    const eventSource = new EventSource("/api/events");
    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            applyState(data);
        } catch(e) {}
    };

    // Initial state fetch
    fetch("/api/state")
        .then(res => res.json())
        .then(state => {
            applyState(state);
            if (state && state.room_pin) listenToFirestore(state.room_pin);
        })
        .catch(() => {});
}

document.addEventListener("DOMContentLoaded", initAdmin);
