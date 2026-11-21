let stageTimerInterval = null;
let stageLeaderboardInterval = null;

function startStageQuestionCountdown(startTimestamp, duration) {
    if (stageTimerInterval) clearInterval(stageTimerInterval);
    const updateCountdown = () => {
        const timerEl = document.getElementById("q-timer");
        const timerBox = document.getElementById("q-timer-box");
        if (!timerEl) return;
        const now = Date.now() / 1000;
        const elapsed = startTimestamp > 0 ? (now - startTimestamp) : 0;
        const remaining = Math.max(0, Math.ceil(duration - elapsed));
        timerEl.innerText = remaining;
        if (remaining <= 5) {
            if (timerBox) {
                timerBox.classList.add("pulse-urgent", "border-red-500");
                timerBox.classList.remove("border-indigo-500");
            }
            if (remaining > 0) window.soundManager.playTick();
        } else {
            if (timerBox) {
                timerBox.classList.remove("pulse-urgent", "border-red-500");
                timerBox.classList.add("border-indigo-500");
            }
        }
        if (remaining <= 0) {
            clearInterval(stageTimerInterval);
            stageTimerInterval = null;
        }
    };
    updateCountdown();
    stageTimerInterval = setInterval(updateCountdown, 250);
}

function startStageLeaderboardCountdown(startTimestamp, delay) {
    if (stageLeaderboardInterval) clearInterval(stageLeaderboardInterval);
    const updateLbCountdown = () => {
        const countdownEl = document.getElementById("lb-countdown-num");
        if (!countdownEl) return;
        const now = Date.now() / 1000;
        const elapsed = startTimestamp > 0 ? (now - startTimestamp) : 0;
        const remaining = Math.max(0, Math.ceil(delay - elapsed));
        countdownEl.innerText = remaining;
        if (remaining <= 0) {
            clearInterval(stageLeaderboardInterval);
            stageLeaderboardInterval = null;
        }
    };
    updateLbCountdown();
    stageLeaderboardInterval = setInterval(updateLbCountdown, 250);
}

// Stage Screen Controller
let currentRoomPin = document.getElementById("stage-pin-display").innerText.trim();
let lastStatus = "LOBBY";
let qrLobbyInstance = null;
let qrModalInstance = null;
let lastReactionTimestamp = 0;

// Stage Security / PIN Authentication (Requirement 1: Always require PIN verification on every entry/visit)
let stageAuthenticated = false;

function checkStageAuth() {
    const modal = document.getElementById("modal-stage-auth");
    if (!modal) return;
    if (stageAuthenticated) {
        modal.style.display = "none";
        modal.classList.add("hidden");
        modal.classList.remove("flex");
    } else {
        modal.style.display = "flex";
        modal.classList.remove("hidden");
        modal.classList.add("flex");
        const pinInput = document.getElementById("input-stage-pin");
        if (pinInput) setTimeout(() => pinInput.focus(), 100);
    }
}

async function handleStageAuth(e) {
    if (e && e.preventDefault) e.preventDefault();
    const pinInput = document.getElementById("input-stage-pin");
    const pin = pinInput ? pinInput.value.trim() : "";
    const btn = document.getElementById("btn-stage-auth-submit");
    const errorEl = document.getElementById("stage-auth-error");

    if (!pin) {
        if (errorEl) {
            errorEl.innerText = "Lütfen Sahne PIN kodunu giriniz.";
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
        const res = await fetch("/api/stage/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ stage_pin: pin })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            stageAuthenticated = true;
            const modal = document.getElementById("modal-stage-auth");
            if (modal) {
                modal.style.display = "none";
                modal.classList.add("hidden");
                modal.classList.remove("flex");
            }
            try {
                if (window.soundManager && typeof window.soundManager.playCorrect === "function") {
                    window.soundManager.playCorrect();
                }
            } catch(se) {}
        } else {
            const msg = data.detail || "Hatalı Sahne PIN kodu!";
            if (errorEl) {
                errorEl.innerText = msg;
                errorEl.classList.remove("hidden");
            } else {
                alert(msg);
            }
        }
    } catch(err) {
        const msg = "Bağlantı hatası oluştu.";
        if (errorEl) {
            errorEl.innerText = msg;
            errorEl.classList.remove("hidden");
        } else {
            alert(msg);
        }
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "Sahneyi Aç ve Başlat 📺";
        }
    }
}

function lockStage() {
    stageAuthenticated = false;
    sessionStorage.removeItem("aura_stage_auth");
    const modal = document.getElementById("modal-stage-auth");
    if (modal) {
        modal.style.display = "flex";
        modal.classList.remove("hidden");
        modal.classList.add("flex");
        const pinInput = document.getElementById("input-stage-pin");
        if (pinInput) {
            pinInput.value = "";
            setTimeout(() => pinInput.focus(), 100);
        }
    }
    try {
        if (window.soundManager && typeof window.soundManager.playClick === "function") {
            window.soundManager.playClick();
        }
    } catch(e) {}
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

    // Apply Live Theme Sync
    if (state.theme) {
        document.body.className = "theme-" + state.theme;
    } else {
        document.body.className = "theme-default";
    }

    // Check if room PIN was changed by Admin
    if (state.room_pin && state.room_pin !== currentRoomPin) {
        updateQrCodes(state.room_pin);
    }

    // Check for incoming live reactions
    if (state.last_reaction && state.last_reaction.timestamp > lastReactionTimestamp) {
        lastReactionTimestamp = state.last_reaction.timestamp;
        const sender = state.last_reaction.sender || state.last_reaction.player_name || "İzleyici";
        spawnReaction(state.last_reaction.emoji, sender);
    }

    // Update schools leaderboard if data present
    if (state.schools_leaderboard) {
        renderSchoolsLeaderboard(state.schools_leaderboard);
    }

    const stageCount = document.getElementById("stage-players-count");
    if (stageCount) stageCount.innerText = state.participants_count || 0;

    // Handle 5-to-1 Fullscreen Countdown
    const countdownOverlay = document.getElementById("stage-countdown-overlay");
    const cdNumberEl = document.getElementById("countdown-stage-number");
    const cdTitleEl = document.getElementById("countdown-stage-title");
    const cdSubEl = document.getElementById("countdown-stage-subtitle");

    if (state.status === "COUNTDOWN") {
        if (countdownOverlay) countdownOverlay.classList.remove("hidden");
        const startTs = state.countdown_start_timestamp;
        const now = Date.now() / 1000;
        const remaining = Math.max(0, Math.ceil(5 - (startTs > 0 ? (now - startTs) : 0)));
        if (cdNumberEl) {
            if (remaining > 0) {
                cdNumberEl.innerText = remaining;
                if (cdTitleEl) cdTitleEl.innerText = "Yarışma Başlıyor!";
                if (cdSubEl) cdSubEl.innerText = "Hazırlanın, ilk soru ekrana geliyor...";
                if (remaining <= 3) {
                    try { window.soundManager.playTick(); } catch(e) {}
                }
            } else {
                cdNumberEl.innerText = "🚀";
                if (cdTitleEl) cdTitleEl.innerText = "BAŞLADI!";
                if (cdSubEl) cdSubEl.innerText = "İlk soru ekrana yansıtılıyor...";
            }
        }
    } else {
        if (countdownOverlay) countdownOverlay.classList.add("hidden");
    }

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

    if (newStatus !== "QUESTION" && stageTimerInterval) {
        clearInterval(stageTimerInterval);
        stageTimerInterval = null;
    }
    if (newStatus !== "LEADERBOARD" && stageLeaderboardInterval) {
        clearInterval(stageLeaderboardInterval);
        stageLeaderboardInterval = null;
    }

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

            document.getElementById("q-answers-count").innerText = state.answers_count || 0;
            document.getElementById("q-total-players").innerText = state.participants_count || 0;

            // Start smooth timestamp-based countdown
            startStageQuestionCountdown(state.question_start_timestamp, state.duration || 15);
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
            startStageLeaderboardCountdown(state.leaderboard_start_timestamp, state.transition_delay || 5);
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
        const slot1 = document.getElementById("podium-slot-1");
        const slot2 = document.getElementById("podium-slot-2");
        const slot3 = document.getElementById("podium-slot-3");
        const btnFull = document.getElementById("btn-show-full-leaderboard");

        // Fetch top 3 and initialize
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

                // Sequential Kahoot-style reveal if new entry to PODIUM
                if (lastStatus !== "PODIUM") {
                    if (slot1) slot1.classList.remove("podium-revealed");
                    if (slot2) slot2.classList.remove("podium-revealed");
                    if (slot3) slot3.classList.remove("podium-revealed");
                    if (btnFull) btnFull.classList.add("hidden");

                    // Step 1: 3rd Place Rises (0.6s)
                    setTimeout(() => {
                        if (slot3) {
                            slot3.classList.add("podium-revealed");
                            window.soundManager.playTick();
                        }
                    }, 600);

                    // Step 2: 2nd Place Rises (2.2s)
                    setTimeout(() => {
                        if (slot2) {
                            slot2.classList.add("podium-revealed");
                            window.soundManager.playTick();
                        }
                    }, 2200);

                    // Step 3: 1st Place Champion Rises with Fanfare & Confetti (4.2s)
                    setTimeout(() => {
                        if (slot1) {
                            slot1.classList.add("podium-revealed");
                            window.soundManager.playCorrect();
                        }
                        if (typeof confetti === "function") {
                            confetti({
                                particleCount: 180,
                                spread: 100,
                                origin: { y: 0.55 }
                            });
                        }
                    }, 4200);

                    // Step 4: Show "Bütün Sıralamayı Göster" Button (5.5s)
                    setTimeout(() => {
                        if (btnFull) {
                            btnFull.classList.remove("hidden");
                            btnFull.classList.add("fade-in");
                        }
                    }, 5500);
                } else {
                    // Already in PODIUM, ensure elements are visible
                    if (slot1) slot1.classList.add("podium-revealed");
                    if (slot2) slot2.classList.add("podium-revealed");
                    if (slot3) slot3.classList.add("podium-revealed");
                    if (btnFull) btnFull.classList.remove("hidden");
                }
            })
            .catch(() => {});
    }

    lastStatus = newStatus;
}

// Full Leaderboard Modal Functions (Requirement 6)
async function openFullLeaderboardModal() {
    const modal = document.getElementById("modal-full-leaderboard");
    const tbody = document.getElementById("full-leaderboard-tbody");
    if (!modal) return;

    modal.classList.remove("hidden");
    window.soundManager.playClick();

    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="4" class="p-6 text-center text-slate-400 font-semibold">Tüm katılımcı sıralaması yükleniyor...</td></tr>`;
        try {
            const res = await fetch("/api/leaderboard?limit=100");
            const players = await res.json();
            if (players && players.length > 0) {
                tbody.innerHTML = players.map(p => `
                    <tr class="hover:bg-slate-800/60 transition-colors ${p.rank === 1 ? 'bg-amber-500/10' : p.rank === 2 ? 'bg-slate-300/5' : p.rank === 3 ? 'bg-amber-600/5' : ''}">
                        <td class="p-3.5 font-mono font-black text-center ${p.rank === 1 ? 'text-amber-400 text-lg' : p.rank === 2 ? 'text-slate-300 text-lg' : p.rank === 3 ? 'text-amber-600 text-lg' : 'text-slate-500'}">
                            ${p.rank === 1 ? '🥇' : p.rank === 2 ? '🥈' : p.rank === 3 ? '🥉' : '#' + p.rank}
                        </td>
                        <td class="p-3.5">
                            <div class="flex items-center space-x-2.5">
                                <span class="text-2xl">${p.avatar || '🚀'}</span>
                                <span class="font-extrabold text-white text-sm">${escapeHtml(p.name)}</span>
                            </div>
                        </td>
                        <td class="p-3.5 text-xs text-indigo-300 font-medium">${escapeHtml(p.school || 'Diğer')}</td>
                        <td class="p-3.5 text-right font-mono font-black text-amber-400 text-sm">${p.score} Puan</td>
                    </tr>
                `).join("");
            } else {
                tbody.innerHTML = `<tr><td colspan="4" class="p-6 text-center text-slate-500">Henüz katılımcı bulunamadı.</td></tr>`;
            }
        } catch(e) {
            tbody.innerHTML = `<tr><td colspan="4" class="p-6 text-center text-rose-400">Veriler yüklenirken hata oluştu.</td></tr>`;
        }
    }
}

function closeFullLeaderboardModal() {
    const modal = document.getElementById("modal-full-leaderboard");
    if (modal) modal.classList.add("hidden");
    window.soundManager.playClick();
}

// Schools Leaderboard Modal & Rendering
function renderSchoolsLeaderboard(schools) {
    const tbody = document.getElementById("schools-leaderboard-tbody");
    if (!tbody || !schools) return;
    tbody.innerHTML = schools.map(s => `
        <tr class="hover:bg-slate-800/60 transition-colors ${s.rank === 1 ? 'bg-amber-500/10' : ''}">
            <td class="p-3.5 font-mono font-black text-center ${s.rank === 1 ? 'text-amber-400 text-base' : s.rank === 2 ? 'text-slate-300' : s.rank === 3 ? 'text-amber-600' : 'text-slate-500'}">
                ${s.rank === 1 ? '🥇 1' : s.rank === 2 ? '🥈 2' : s.rank === 3 ? '🥉 3' : '#' + s.rank}
            </td>
            <td class="p-3.5 font-bold text-white text-sm">${escapeHtml(s.school)}</td>
            <td class="p-3.5 text-center font-mono font-semibold text-indigo-300">${s.player_count} Katılımcı</td>
            <td class="p-3.5 text-right font-mono font-black text-amber-400 text-sm">${s.total_score} Puan</td>
        </tr>
    `).join("");
}

async function openSchoolsLeaderboardModal() {
    const modal = document.getElementById("modal-schools-leaderboard");
    const tbody = document.getElementById("schools-leaderboard-tbody");
    if (!modal) return;
    modal.classList.remove("hidden");
    window.soundManager.playClick();

    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-slate-400">Okul puanları hesaplanıyor...</td></tr>`;
        try {
            const res = await fetch("/api/leaderboard/schools");
            const data = await res.json();
            if (data && data.schools) {
                renderSchoolsLeaderboard(data.schools);
            }
        } catch(e) {
            tbody.innerHTML = `<tr><td colspan="4" class="p-4 text-center text-rose-400">Veriler yüklenemedi.</td></tr>`;
        }
    }
}

function closeSchoolsLeaderboardModal() {
    const modal = document.getElementById("modal-schools-leaderboard");
    if (modal) modal.classList.add("hidden");
    window.soundManager.playClick();
}

// Init Stage
function initStage() {
    stageAuthenticated = false;
    sessionStorage.removeItem("aura_stage_auth");
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
