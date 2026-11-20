// Admin Controller
let adminPin = sessionStorage.getItem("aura_admin_pin") || "";
let currentQuestionDuration = 15;
let currentTransitionDelay = 5;
let isAutoMode = false;

// Check / Prompt Admin PIN
function checkAdminAuth() {
    const modal = document.getElementById("modal-admin-auth");
    if (adminPin) {
        modal.classList.add("hidden");
        loadQuestions();
        refreshAdminPlayers();
    } else {
        modal.classList.remove("hidden");
    }
}

async function handleAdminAuth(e) {
    e.preventDefault();
    const pin = document.getElementById("input-admin-pin").value.trim();
    const btn = document.getElementById("btn-admin-login");
    btn.disabled = true;
    btn.innerText = "Doğrulanıyor...";

    try {
        const res = await fetch("/api/admin/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ admin_pin: pin })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            adminPin = pin;
            sessionStorage.setItem("aura_admin_pin", adminPin);
            document.getElementById("modal-admin-auth").classList.add("hidden");
            window.soundManager.playCorrect();
            loadQuestions();
            refreshAdminPlayers();
        } else {
            alert(data.detail || "Hatalı Admin PIN!");
        }
    } catch(err) {
        alert("Bağlantı hatası!");
    } finally {
        btn.disabled = false;
        btn.innerText = "Giriş Yap";
    }
}

function adminLogout() {
    sessionStorage.removeItem("aura_admin_pin");
    adminPin = "";
    document.getElementById("modal-admin-auth").classList.remove("hidden");
    window.soundManager.playClick();
}

// Tab Switching
function switchAdminTab(tabName) {
    const tabs = ["control", "quizzes", "reports", "security"];
    tabs.forEach(t => {
        const btn = document.getElementById(`tab-btn-${t}`);
        const sec = document.getElementById(`tab-section-${t}`);
        if (t === tabName) {
            btn.className = "admin-tab-btn flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-extrabold bg-indigo-600 text-white shadow-md shadow-indigo-600/30 transition-all";
            sec.classList.remove("hidden");
        } else {
            btn.className = "admin-tab-btn flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold text-slate-400 hover:text-white hover:bg-slate-800/60 transition-all";
            sec.classList.add("hidden");
        }
    });

    if (tabName === "quizzes") loadQuestions();
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

// Manual Question Modal Management (Requirement 1)
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
                duration: duration
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
            loadQuestions();
        } else {
            alert(data.detail || "Soru silinemedi!");
        }
    } catch(e) {
        alert("Ağ hatası!");
    }
}

// Generate Questions with Gemini AI API
async function generateAiQuestions() {
    if (!adminPin) {
        checkAdminAuth();
        return;
    }

    const btn = document.getElementById("btn-generate-ai");
    const notice = document.getElementById("ai-status-notice");
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">🔄</span> 30 Soru Üretiliyor...`;

    notice.className = "p-3 rounded-xl text-xs font-bold mb-4 bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 block";
    notice.innerText = "Gemini AI modeli ile 30 özgün yapay zeka ve girişimcilik sorusu üretiliyor, lütfen bekleyiniz...";

    try {
        const res = await fetch("/api/admin/generate-questions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                admin_pin: adminPin,
                count: 30
            })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            notice.className = "p-3 rounded-xl text-xs font-bold mb-4 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 block";
            notice.innerText = `Harika! Gemini API ile ${data.count} yeni soru başarıyla üretildi ve yarışmaya yüklendi.`;
            window.soundManager.playCorrect();
            loadQuestions();
        } else {
            notice.className = "p-3 rounded-xl text-xs font-bold mb-4 bg-rose-500/10 text-rose-400 border border-rose-500/30 block";
            notice.innerText = "Soru üretilemedi: " + (data.detail || "Bilinmeyen hata");
        }
    } catch(err) {
        notice.className = "p-3 rounded-xl text-xs font-bold mb-4 bg-rose-500/10 text-rose-400 border border-rose-500/30 block";
        notice.innerText = "Soru üretimi sırasında ağ hatası oluştu.";
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i data-lucide="bot" class="w-4 h-4 mr-1 inline"></i> 30 Yeni Soru Üret (Gemini API)`;
        lucide.createIcons();
    }
}

// Load Questions Table with Delete Button
async function loadQuestions() {
    if (!adminPin) return;
    try {
        const res = await fetch(`/api/admin/questions?admin_pin=${encodeURIComponent(adminPin)}`);
        const data = await res.json();
        if (res.ok && data.questions) {
            const tbody = document.getElementById("questions-table-body");
            if (!tbody) return;
            if (data.questions.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-slate-500 font-semibold">Henüz soru eklenmedi. Manuel ekleyebilir veya Gemini ile üretebilirsiniz.</td></tr>`;
                return;
            }
            tbody.innerHTML = data.questions.map((q, idx) => `
                <tr class="hover:bg-slate-800/50 transition-colors">
                    <td class="p-3 font-mono font-bold text-slate-500">${idx + 1}</td>
                    <td class="p-3 font-semibold text-white max-w-sm truncate" title="${escapeHtml(q.question)}">
                        ${escapeHtml(q.question)}
                    </td>
                    <td class="p-3">
                        <span class="px-2 py-0.5 rounded-md font-mono font-black text-xs ${getCorrectBadgeClass(q.correct)}">
                            ${q.correct}
                        </span>
                    </td>
                    <td class="p-3 font-mono text-slate-400">${q.duration || 15}s</td>
                    <td class="p-3 text-right">
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

// Refresh Live Participants in Admin Dashboard
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
            <div class="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                <div class="flex items-center space-x-2.5">
                    <span class="text-xl">${p.avatar || '🚀'}</span>
                    <div>
                        <span class="font-bold text-white block">${escapeHtml(p.name)}</span>
                        <span class="text-[10px] text-slate-400">${escapeHtml(p.school || 'Diğer')}</span>
                    </div>
                </div>
                <div class="text-right">
                    <span class="font-mono font-bold text-indigo-400">${p.score} Puan</span>
                </div>
            </div>
        `).join("");
    } catch(e) {}
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
        .then(state => applyState(state))
        .catch(() => {});
}

document.addEventListener("DOMContentLoaded", initAdmin);
