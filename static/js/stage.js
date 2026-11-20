// Stage Screen Controller
let currentRoomPin = document.getElementById("stage-pin-display").innerText.trim();
let lastStatus = "LOBBY";
let qrLobbyInstance = null;
let qrModalInstance = null;
let knownParticipants = [];

// Initialize QR codes
function updateQrCodes(pin) {
    currentRoomPin = pin;
    document.getElementById("stage-pin-display").innerText = pin;
    document.getElementById("modal-pin-display").innerText = pin;

    const playUrl = `${window.location.origin}/play?pin=${encodeURIComponent(pin)}`;

    const lobbyEl = document.getElementById("lobby-qrcode");
    lobbyEl.innerHTML = "";
    qrLobbyInstance = new QRCode(lobbyEl, {
        text: playUrl,
        width: 220,
        height: 220,
        colorDark: "#020617",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.M
    });

    const modalEl = document.getElementById("modal-qrcode-target");
    modalEl.innerHTML = "";
    qrModalInstance = new QRCode(modalEl, {
        text: playUrl,
        width: 320,
        height: 320,
        colorDark: "#020617",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.H
    });
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

// Render dynamic Marquee Participants
function renderMarquee(players) {
    const marquee = document.getElementById("participants-marquee");
    const statusText = document.getElementById("marquee-status");
    if (!players || players.length === 0) {
        marquee.innerHTML = `
            <div class="inline-flex items-center space-x-3 bg-slate-800/80 border border-slate-700/80 px-4 py-2 rounded-xl text-slate-400 text-sm">
                <span>🚀 Katılımcı kartları burada akacak</span>
            </div>
        `;
        statusText.innerText = "Katılımcılar bekleniyor...";
        return;
    }

    statusText.innerText = `${players.length} yarışmacı hazır`;

    // Duplicate players array to ensure seamless infinite horizontal scroll
    const items = [...players, ...players];
    marquee.innerHTML = items.map(p => `
        <div class="inline-flex items-center space-x-3 bg-slate-800/90 border border-slate-700/90 hover:border-indigo-500 px-5 py-2.5 rounded-2xl text-white shadow-md flex-shrink-0">
            <span class="text-2xl">${p.avatar || '🚀'}</span>
            <div class="flex flex-col text-left">
                <span class="font-bold text-sm leading-tight text-white">${escapeHtml(p.name)}</span>
                <span class="text-xs text-indigo-400 font-medium">${escapeHtml(p.school || 'Bağımsız')}</span>
            </div>
        </div>
    `).join("");
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

    document.getElementById("stage-players-count").innerText = state.participants_count || 0;

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
        if (key === newStatus) {
            views[key].classList.remove("hidden");
        } else {
            views[key].classList.add("hidden");
        }
    });

    if (newStatus === "LOBBY") {
        fetch("/api/leaderboard?limit=50")
            .then(res => res.json())
            .then(data => renderMarquee(data))
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
        fetch("/api/leaderboard?limit=5")
            .then(res => res.json())
            .then(players => {
                const list = document.getElementById("leaderboard-list");
                list.innerHTML = players.map(p => `
                    <div class="flex items-center justify-between bg-slate-900/90 border border-slate-800 hover:border-indigo-500/50 p-4 sm:p-5 rounded-2xl shadow-lg transition-all">
                        <div class="flex items-center space-x-4">
                            <span class="w-10 h-10 rounded-xl bg-slate-800 text-slate-300 font-black flex items-center justify-center text-lg">
                                #${p.rank}
                            </span>
                            <span class="text-3xl">${p.avatar}</span>
                            <div class="flex flex-col text-left">
                                <span class="font-extrabold text-white text-base sm:text-lg">${escapeHtml(p.name)}</span>
                                <span class="text-xs text-slate-400 font-semibold">${escapeHtml(p.school)}</span>
                            </div>
                        </div>
                        <div class="flex items-center space-x-4">
                            ${p.streak > 1 ? `<span class="bg-amber-500/10 text-amber-400 border border-amber-500/30 px-3 py-1 rounded-full text-xs font-bold">🔥 ${p.streak} Seri</span>` : ''}
                            <span class="text-xl sm:text-2xl font-black text-indigo-400">${p.score} P</span>
                        </div>
                    </div>
                `).join("");
            })
            .catch(() => {});

    } else if (newStatus === "PODIUM") {
        if (lastStatus !== "PODIUM") {
            window.soundManager.playPodiumFanfare();
            triggerConfetti();
        }
        fetch("/api/podium")
            .then(res => res.json())
            .then(podium => {
                if (podium.first) {
                    document.getElementById("podium-1-avatar").innerText = podium.first.avatar || "🏆";
                    document.getElementById("podium-1-name").innerText = podium.first.name || "Şampiyon";
                    document.getElementById("podium-1-school").innerText = podium.first.school || "";
                    document.getElementById("podium-1-score").innerText = `${podium.first.score} Puan`;
                }
                if (podium.second) {
                    document.getElementById("podium-2-avatar").innerText = podium.second.avatar || "🥈";
                    document.getElementById("podium-2-name").innerText = podium.second.name || "2. Yarışmacı";
                    document.getElementById("podium-2-school").innerText = podium.second.school || "";
                    document.getElementById("podium-2-score").innerText = `${podium.second.score} Puan`;
                }
                if (podium.third) {
                    document.getElementById("podium-3-avatar").innerText = podium.third.avatar || "🥉";
                    document.getElementById("podium-3-name").innerText = podium.third.name || "3. Yarışmacı";
                    document.getElementById("podium-3-school").innerText = podium.third.school || "";
                    document.getElementById("podium-3-score").innerText = `${podium.third.score} Puan`;
                }
            })
            .catch(() => {});
    }

    lastStatus = newStatus;
}

// Confetti Blast Animation for Grand Finale
function triggerConfetti() {
    if (typeof confetti !== "function") return;
    const count = 250;
    const defaults = { origin: { y: 0.7 } };

    function fire(particleRatio, opts) {
        confetti(Object.assign({}, defaults, opts, {
            particleCount: Math.floor(count * particleRatio)
        }));
    }

    fire(0.25, { spread: 26, startVelocity: 55 });
    fire(0.2, { spread: 60 });
    fire(0.35, { spread: 100, decay: 0.91, scalar: 0.8 });
    fire(0.1, { spread: 120, startVelocity: 25, decay: 0.92, scalar: 1.2 });
    fire(0.1, { spread: 120, startVelocity: 45 });
}

// Real-Time Connection Setup (SSE with Firestore client fallback)
function initRealtime() {
    updateQrCodes(currentRoomPin);

    // Initial state fetch
    fetch("/api/state")
        .then(res => res.json())
        .then(state => applyState(state))
        .catch(() => {});

    // 1. SSE Connection
    const eventSource = new EventSource("/api/events");
    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            applyState(data);
        } catch(e) {}
    };

    eventSource.onerror = () => {
        console.warn("[Stage] SSE reconnecting...");
    };

    // 2. Firebase Firestore Real-Time listener (if configured)
    if (window.firestoreDb) {
        try {
            window.firestoreDb.collection("rooms").doc(currentRoomPin).onSnapshot((doc) => {
                if (doc.exists) {
                    applyState(doc.data());
                }
            });
        } catch(e) {}
    }
}

document.addEventListener("DOMContentLoaded", initRealtime);
