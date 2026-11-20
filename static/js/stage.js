// Stage Screen Controller
let currentRoomPin = document.getElementById("stage-pin-display").innerText.trim();
let lastStatus = "LOBBY";
let qrLobbyInstance = null;
let qrModalInstance = null;
let lastReactionTimestamp = 0;

// Stage Security / PIN Authentication
function checkStageAuth() {
    const modal = document.getElementById("modal-stage-auth");
    if (!modal) return;
    const isAuthed = sessionStorage.getItem("aura_stage_auth") === "true";
    if (isAuthed) {
        modal.classList.add("hidden");
    } else {
        modal.classList.remove("hidden");
    }
}

async function handleStageAuth(e) {
    e.preventDefault();
    const pin = document.getElementById("input-stage-pin").value.trim();
    const btn = document.getElementById("btn-stage-auth-submit");
    btn.disabled = true;
    btn.innerText = "Doğrulanıyor...";

    try {
        const res = await fetch("/api/stage/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ stage_pin: pin })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            sessionStorage.setItem("aura_stage_auth", "true");
            document.getElementById("modal-stage-auth").classList.add("hidden");
            window.soundManager.playCorrect();
        } else {
            alert(data.detail || "Hatalı Sahne PIN!");
        }
    } catch(err) {
        alert("Bağlantı hatası!");
    } finally {
        btn.disabled = false;
        btn.innerText = "Sahneyi Aç ve Başlat 📺";
    }
}

function lockStage() {
    sessionStorage.removeItem("aura_stage_auth");
    document.getElementById("modal-stage-auth").classList.remove("hidden");
    window.soundManager.playClick();
}

// Initialize QR codes
function updateQrCodes(pin) {
    currentRoomPin = pin;
    const pinDisplay = document.getElementById("stage-pin-display");
    const lobbyPinDisplay = document.getElementById("lobby-pin-display");
    const modalPinDisplay = document.getElementById("modal-pin-display");

    if (pinDisplay) pinDisplay.innerText = pin;
    if (lobbyPinDisplay) lobbyPinDisplay.innerText = pin;
    if (modalPinDisplay) modalPinDisplay.innerText = pin;

    const playUrl = `${window.location.origin}/play?pin=${encodeURIComponent(pin)}`;

    const lobbyEl = document.getElementById("lobby-qrcode");
    if (lobbyEl) {
        lobbyEl.innerHTML = "";
        qrLobbyInstance = new QRCode(lobbyEl, {
            text: playUrl,
            width: 200,
            height: 200,
            colorDark: "#020617",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.M
        });
    }

    const modalEl = document.getElementById("modal-qrcode-target");
    if (modalEl) {
        modalEl.innerHTML = "";
        qrModalInstance = new QRCode(modalEl, {
            text: playUrl,
            width: 300,
            height: 300,
            colorDark: "#020617",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });
    }
}

function openQrModal() {
    const modal = document.getElementById("modal-qr");
    modal.classList.remove("hidden");
    window.soundManager.playClick();
}

function closeQrModal() {
    const modal = document.getElementById("modal-qr");
    modal.classList.add("hidden");
    window.soundManager.playClick();
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

// Render Unique Participants List (Requirement 6: Strictly 1 card per player)
function renderParticipantsList(players) {
    const container = document.getElementById("lobby-participants-container");
    const countBadge = document.getElementById("lobby-players-count-badge");
    const stageCount = document.getElementById("stage-players-count");

    if (!container) return;

    const count = (players && players.length) || 0;
    if (countBadge) countBadge.innerText = `${count} Katılımcı`;
    if (stageCount) stageCount.innerText = count;

    if (!players || players.length === 0) {
        container.innerHTML = `
            <div id="empty-participants-notice" class="flex flex-col items-center justify-center h-48 text-center text-slate-500">
                <i data-lucide="user-plus" class="w-10 h-10 mb-2 opacity-40"></i>
                <span class="text-sm font-semibold">İlk yarışmacının odaya bağlanması bekleniyor...</span>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    // Strictly unique items (No duplicate arrays)
    container.innerHTML = players.map(p => `
        <div class="flex items-center justify-between p-3.5 rounded-2xl bg-slate-950/80 border border-slate-800 hover:border-indigo-500/50 transition-all shadow-md group">
            <div class="flex items-center space-x-3.5">
                <div class="w-11 h-11 sm:w-12 sm:h-12 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-2xl sm:text-3xl group-hover:scale-110 transition-transform">
                    ${p.avatar || '🚀'}
                </div>
                <div class="flex flex-col text-left">
                    <span class="font-extrabold text-sm sm:text-base text-white leading-tight">${escapeHtml(p.name)}</span>
                    <span class="text-xs text-indigo-400 font-medium">${escapeHtml(p.school || 'Diğer')}</span>
                </div>
            </div>
            <div class="flex items-center space-x-2">
                <span class="inline-flex items-center px-2.5 py-1 rounded-xl text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
                    Hazır
                </span>
            </div>
        </div>
    `).join("");
}

// Live Reaction Floating Emoji Animation (Requirement 2)
function spawnReaction(emoji, senderName) {
    const container = document.getElementById("stage-reactions");
    if (!container) return;

    const bubble = document.createElement("div");
    bubble.className = "reaction-bubble";
    const randomLeft = Math.floor(Math.random() * 80) + 10; // 10% to 90%
    bubble.style.left = `${randomLeft}%`;
    bubble.innerHTML = `<span class="text-4xl filter drop-shadow-xl select-none">${emoji}</span>`;
    container.appendChild(bubble);

    setTimeout(() => {
        bubble.remove();
    }, 3200);
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// State Switcher
function applyState(state) {
    if (!state) return;

    // Check if room PIN was changed by Admin
    if (state.room_pin && state.room_pin !== currentRoomPin) {
        updateQrCodes(state.room_pin);
    }

    // Check for incoming live reactions
    if (state.last_reaction && state.last_reaction.timestamp > lastReactionTimestamp) {
        lastReactionTimestamp = state.last_reaction.timestamp;
        spawnReaction(state.last_reaction.emoji, state.last_reaction.player_name);
    }

    const stageCount = document.getElementById("stage-players-count");
    if (stageCount) stageCount.innerText = state.participants_count || 0;

    const views = {
        LOBBY: document.getElementById("view-lobby"),
        QUESTION: document.getElementById("view-question"),
        REVEAL: document.getElementById("view-reveal"),
        LEADERBOARD: document.getElementById("view-leaderboard"),
        PODIUM: document.getElementById("view-podium")
    };

    const newStatus = state.status || "LOBBY";

    // Hide all, show target
    Object.keys(views).forEach(key => {
        if (views[key]) {
            if (key === newStatus) {
                views[key].classList.remove("hidden");
            } else {
                views[key].classList.add("hidden");
            }
        }
    });

    if (newStatus === "LOBBY") {
        fetch("/api/leaderboard?limit=50")
            .then(res => res.json())
            .then(data => renderParticipantsList(data))
            .catch(() => {});
    } else if (newStatus === "QUESTION") {
        const q = state.current_question;
        if (q) {
            document.getElementById("q-number").innerText = (state.current_question_index + 1);
            document.getElementById("q-total").innerText = state.total_questions;
            document.getElementById("q-text").innerText = q.question;
            document.getElementById("stage-text-A").innerText = q.options.A;
            document.getElementById("stage-text-B").innerText = q.options.B;
            document.getElementById("stage-text-C").innerText = q.options.C;
            document.getElementById("stage-text-D").innerText = q.options.D;

            // Ensure option C has exact bg-yellow-500 styling
            const optC = document.getElementById("stage-opt-C");
            optC.className = "bg-yellow-500 rounded-3xl p-6 sm:p-8 flex items-center space-x-6 text-slate-950 shadow-xl transition-all";

            document.getElementById("q-timer").innerText = state.timer_remaining;
            document.getElementById("q-answers-count").innerText = state.answers_count || 0;
            document.getElementById("q-total-players").innerText = state.participants_count || 0;

            const timerBox = document.getElementById("q-timer-box");
            if (state.timer_remaining <= 5) {
                timerBox.classList.add("pulse-urgent", "border-red-500");
                timerBox.classList.remove("border-indigo-500");
                window.soundManager.playTick();
            } else {
                timerBox.classList.remove("pulse-urgent", "border-red-500");
                timerBox.classList.add("border-indigo-500");
            }
        }
    } else if (newStatus === "REVEAL") {
        if (lastStatus !== "REVEAL") {
            window.soundManager.playCorrect();
        }
        const q = state.current_question;
        if (q) {
            document.getElementById("reveal-q-text").innerText = q.question;
            const correctOpt = q.correct || "A";
            const correctText = q.options ? q.options[correctOpt] : "";

            const banner = document.getElementById("reveal-correct-banner");
            let bgClass = "bg-red-600";
            let symbol = "🔺";
            if (correctOpt === "B") { bgClass = "bg-blue-600"; symbol = "🔷"; }
            if (correctOpt === "C") { bgClass = "bg-yellow-500 text-slate-950"; symbol = "🟡"; }
            if (correctOpt === "D") { bgClass = "bg-green-600"; symbol = "🟢"; }

            banner.className = `p-6 rounded-2xl flex items-center justify-center space-x-4 text-2xl font-black shadow-xl mb-6 ${bgClass}`;
            banner.innerHTML = `<span>${symbol}</span> <span>Doğru Cevap: ${correctOpt} - ${escapeHtml(correctText)}</span>`;
            document.getElementById("reveal-explanation").innerText = q.explanation || "";
        }

        // Stats bars
        const totalAnswers = Math.max(1, state.answers_count || 1);
        ["A", "B", "C", "D"].forEach(opt => {
            const count = (state.answer_stats && state.answer_stats[opt]) || 0;
            const pct = Math.min(100, Math.max(10, Math.round((count / totalAnswers) * 100)));
            document.getElementById(`stat-count-${opt}`).innerText = count;
            document.getElementById(`stat-bar-${opt}`).style.height = `${pct}%`;
        });

    } else if (newStatus === "LEADERBOARD") {
        const autoCountdownEl = document.getElementById("leaderboard-auto-countdown");
        if (state.auto_mode) {
            autoCountdownEl.classList.remove("hidden");
            document.getElementById("lb-countdown-num").innerText = state.leaderboard_countdown || 5;
        } else {
            autoCountdownEl.classList.add("hidden");
        }

        fetch("/api/leaderboard?limit=5")
            .then(res => res.json())
            .then(players => {
                const list = document.getElementById("leaderboard-list");
                list.innerHTML = players.map(p => `
                    <div class="flex items-center justify-between p-4 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg">
                        <div class="flex items-center space-x-4">
                            <span class="font-mono text-xl font-black w-8 text-center ${p.rank === 1 ? 'text-amber-400' : p.rank === 2 ? 'text-slate-300' : p.rank === 3 ? 'text-amber-600' : 'text-slate-500'}">
                                ${p.rank === 1 ? '🥇' : p.rank === 2 ? '🥈' : p.rank === 3 ? '🥉' : '#' + p.rank}
                            </span>
                            <span class="text-3xl">${p.avatar || '🚀'}</span>
                            <div class="flex flex-col text-left">
                                <span class="font-extrabold text-white text-base">${escapeHtml(p.name)}</span>
                                <span class="text-xs text-indigo-400 font-semibold">${escapeHtml(p.school || 'Diğer')}</span>
                            </div>
                        </div>
                        <div class="text-right">
                            <span class="font-mono text-xl font-black text-amber-400">${p.score}</span>
                            <span class="text-xs text-slate-400 font-bold block">Puan</span>
                        </div>
                    </div>
                `).join("");
            })
            .catch(() => {});

    } else if (newStatus === "PODIUM") {
        if (lastStatus !== "PODIUM") {
            window.soundManager.playCorrect();
            // Confetti celebration
            if (typeof confetti === "function") {
                confetti({
                    particleCount: 150,
                    spread: 80,
                    origin: { y: 0.6 }
                });
            }
        }

        fetch("/api/leaderboard?limit=3")
            .then(res => res.json())
            .then(top3 => {
                const p1 = top3[0] || { name: "Şampiyon", school: "Kurum", score: 0, avatar: "🏆" };
                const p2 = top3[1] || { name: "2. Yarışmacı", school: "Kurum", score: 0, avatar: "🥈" };
                const p3 = top3[2] || { name: "3. Yarışmacı", school: "Kurum", score: 0, avatar: "🥉" };

                // 1st
                document.getElementById("podium-1-avatar").innerText = p1.avatar || "🏆";
                document.getElementById("podium-1-name").innerText = p1.name;
                document.getElementById("podium-1-school").innerText = p1.school;
                document.getElementById("podium-1-score").innerText = `${p1.score} Puan`;

                // 2nd
                document.getElementById("podium-2-avatar").innerText = p2.avatar || "🥈";
                document.getElementById("podium-2-name").innerText = p2.name;
                document.getElementById("podium-2-school").innerText = p2.school;
                document.getElementById("podium-2-score").innerText = `${p2.score} Puan`;

                // 3rd
                document.getElementById("podium-3-avatar").innerText = p3.avatar || "🥉";
                document.getElementById("podium-3-name").innerText = p3.name;
                document.getElementById("podium-3-school").innerText = p3.school;
                document.getElementById("podium-3-score").innerText = `${p3.score} Puan`;
            })
            .catch(() => {});
    }

    lastStatus = newStatus;
}

// Init Stage
function initStage() {
    checkStageAuth();
    updateQrCodes(currentRoomPin);

    // Initial state fetch
    fetch("/api/state")
        .then(res => res.json())
        .then(state => applyState(state))
        .catch(() => {});

    // SSE Stream
    const eventSource = new EventSource("/api/events");
    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            applyState(data);
        } catch(e) {}
    };

    // Firestore listener
    if (window.firestoreDb && currentRoomPin) {
        try {
            window.firestoreDb.collection("rooms").doc(currentRoomPin).onSnapshot((doc) => {
                if (doc.exists) {
                    applyState(doc.data());
                }
            });
        } catch(e) {}
    }
}

document.addEventListener("DOMContentLoaded", initStage);
