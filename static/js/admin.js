// Admin Controller
let adminPin = sessionStorage.getItem("aura_admin_pin") || "";
let currentDuration = 15;
let isAutoMode = false;

// Check / Prompt Admin PIN
function checkAdminAuth() {
    const modal = document.getElementById("modal-admin-auth");
    if (adminPin) {
        modal.classList.add("hidden");
        loadQuestions();
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

// Update Room PIN (Syncs to Firestore)
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

// Timer Durations (5s, 10s, 15s)
async function setTimerDuration(seconds) {
    currentDuration = seconds;
    const btns = [5, 10, 15];
    btns.forEach(sec => {
        const b = document.getElementById(`btn-timer-${sec}`);
        if (sec === seconds) {
            b.className = "timer-btn py-2.5 rounded-xl border border-indigo-500 bg-indigo-600/20 text-xs font-black text-indigo-300 transition-all";
        } else {
            b.className = "timer-btn py-2.5 rounded-xl border border-slate-700 text-xs font-black text-slate-300 hover:border-indigo-500 transition-all";
        }
    });

    try {
        await fetch("/api/admin/timer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                admin_pin: adminPin,
                duration: seconds,
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
                duration: currentDuration,
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
        btn.innerHTML = `<i data-lucide="bot" class="w-4 h-4 mr-1 inline"></i> 30 Yeni Soru Üret`;
        lucide.createIcons();
    }
}

// Load Questions Preview
async function loadQuestions() {
    if (!adminPin) return;
    try {
        const res = await fetch(`/api/admin/questions?admin_pin=${encodeURIComponent(adminPin)}`);
        const data = await res.json();
        if (res.ok && data.questions) {
            const tbody = document.getElementById("questions-table-body");
            tbody.innerHTML = data.questions.map((q, idx) => `
                <tr class="hover:bg-slate-800/50 transition-colors">
                    <td class="p-3 font-mono font-bold text-slate-500">${idx + 1}</td>
                    <td class="p-3 font-semibold text-white max-w-xs truncate" title="${escapeHtml(q.question)}">
                        ${escapeHtml(q.question)}
                    </td>
                    <td class="p-3">
                        <span class="px-2 py-0.5 rounded-md font-mono font-black text-xs ${getCorrectBadgeClass(q.correct)}">
                            ${q.correct}
                        </span>
                    </td>
                    <td class="p-3 font-mono text-slate-400">${q.duration || 15}s</td>
                </tr>
            `).join("");
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

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Sync State from SSE
function applyState(state) {
    if (!state) return;
    if (state.room_pin) {
        document.getElementById("admin-pin-display").innerText = state.room_pin;
    }
    if (state.status) {
        const badge = document.getElementById("admin-status-badge");
        badge.innerText = state.status;
        if (state.status === "QUESTION") badge.className = "text-xs font-black px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
        else if (state.status === "REVEAL") badge.className = "text-xs font-black px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30";
        else if (state.status === "PODIUM") badge.className = "text-xs font-black px-2.5 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/30";
        else badge.className = "text-xs font-black px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30";
    }
    if (state.duration) {
        currentDuration = state.duration;
    }
    if (typeof state.auto_mode !== "undefined") {
        isAutoMode = state.auto_mode;
        document.getElementById("toggle-auto-mode").checked = isAutoMode;
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
