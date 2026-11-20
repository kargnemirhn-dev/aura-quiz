// Player Screen Controller (Strict Kahoot mobile guidelines)

const AVATARS = ["🚀", "🤖", "💡", "⚡", "🧠", "🦄", "🏆", "🎯", "🔥", "👑", "💻", "🪐"];
let selectedAvatar = "🚀";
let currentPlayer = null;
let currentRoomPin = "";
let currentQuestionId = null;
let hasAnsweredCurrentQuestion = false;

// Render Avatar Picker Grid
function initAvatarPicker() {
    const grid = document.getElementById("avatar-grid");
    if (!grid) return;
    grid.innerHTML = AVATARS.map((av, idx) => `
        <button type="button" onclick="selectAvatar('${av}')" class="avatar-option p-2 text-2xl rounded-xl transition-all hover:bg-slate-800 ${av === selectedAvatar ? 'bg-indigo-600/40 ring-2 ring-indigo-500 scale-105' : ''}">
            ${av}
        </button>
    `).join("");
}

function selectAvatar(av) {
    selectedAvatar = av;
    initAvatarPicker();
    window.soundManager.playClick();
}

// Show Toast Message
function showToast(msg, duration = 3000) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.innerText = msg;
    toast.classList.remove("opacity-0", "pointer-events-none");
    toast.classList.add("opacity-100");
    setTimeout(() => {
        toast.classList.add("opacity-0", "pointer-events-none");
        toast.classList.remove("opacity-100");
    }, duration);
}

// Join Room Handler
async function handleJoin(e) {
    e.preventDefault();
    const pin = document.getElementById("input-pin").value.trim();
    const name = document.getElementById("input-name").value.trim();
    const school = document.getElementById("input-school").value.trim() || "Bağımsız";

    if (!pin || !name) {
        showToast("Lütfen Oda PIN ve Adınızı giriniz!");
        return;
    }

    const btn = document.getElementById("btn-submit-join");
    btn.disabled = true;
    btn.innerText = "Bağlanıyor...";

    try {
        const res = await fetch("/api/player/join", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                room_pin: pin,
                name: name,
                school: school,
                avatar: selectedAvatar,
                player_id: currentPlayer ? currentPlayer.id : ""
            })
        });

        const data = await res.json();
        if (!res.ok) {
            showToast(data.detail || "Odaya katılırken hata oluştu!");
            btn.disabled = false;
            btn.innerText = "Yarışmaya Katıl 🚀";
            return;
        }

        currentPlayer = data.player;
        currentRoomPin = data.room_pin;
        localStorage.setItem("aura_player", JSON.stringify(currentPlayer));
        localStorage.setItem("aura_room_pin", currentRoomPin);

        updatePlayerHeader();
        showLobbyWaiting();
        window.soundManager.playCorrect();
    } catch (err) {
        showToast("Sunucuya bağlanılamadı!");
        btn.disabled = false;
        btn.innerText = "Yarışmaya Katıl 🚀";
    }
}

// "Odadan Çık" Button Handler (User explicitly requested this feature!)
async function leaveRoom() {
    if (currentPlayer && currentPlayer.id) {
        try {
            await fetch("/api/player/leave", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ player_id: currentPlayer.id })
            });
        } catch(e) {}
    }

    localStorage.removeItem("aura_player");
    currentPlayer = null;
    currentQuestionId = null;
    hasAnsweredCurrentQuestion = false;

    // Reset UI to Join Screen
    document.getElementById("play-view-join").classList.remove("hidden");
    document.getElementById("play-view-lobby").classList.add("hidden");
    document.getElementById("play-view-question").classList.add("hidden");
    document.getElementById("play-view-result").classList.add("hidden");
    document.getElementById("play-view-podium").classList.add("hidden");

    document.getElementById("player-name-badge").innerText = "Misafir";
    document.getElementById("player-score-badge").innerText = "0 Puan";
    document.getElementById("player-avatar-badge").innerText = "🚀";

    const btn = document.getElementById("btn-submit-join");
    btn.disabled = false;
    btn.innerText = "Yarışmaya Katıl 🚀";

    showToast("Odadan çıkış yapıldı.");
    window.soundManager.playClick();
}

function updatePlayerHeader() {
    if (!currentPlayer) return;
    document.getElementById("player-avatar-badge").innerText = currentPlayer.avatar || "🚀";
    document.getElementById("player-name-badge").innerText = currentPlayer.name || "Oyuncu";
    document.getElementById("player-score-badge").innerText = `${currentPlayer.score || 0} Puan`;
}

function showLobbyWaiting() {
    document.getElementById("play-view-join").classList.add("hidden");
    document.getElementById("play-view-question").classList.add("hidden");
    document.getElementById("play-view-result").classList.add("hidden");
    document.getElementById("play-view-podium").classList.add("hidden");
    document.getElementById("play-view-lobby").classList.remove("hidden");

    if (currentPlayer) {
        document.getElementById("lobby-player-avatar").innerText = currentPlayer.avatar;
        document.getElementById("lobby-player-name").innerText = currentPlayer.name;
        document.getElementById("lobby-player-school").innerText = currentPlayer.school;
    }
}

// Submit Kahoot Button Tap (A, B, C, D)
async function submitAnswer(choice) {
    if (!currentPlayer || !currentQuestionId || hasAnsweredCurrentQuestion) return;

    hasAnsweredCurrentQuestion = true;

    // Haptic feedback for tactile feel on mobile
    if (navigator.vibrate) {
        navigator.vibrate(40);
    }
    window.soundManager.playClick();

    // Disable all 4 Kahoot buttons and indicate selected
    const buttons = ["A", "B", "C", "D"];
    buttons.forEach(opt => {
        const btn = document.getElementById(`play-btn-${opt}`);
        btn.disabled = true;
        if (opt !== choice) {
            btn.classList.add("opacity-40");
        } else {
            btn.classList.add("ring-4", "ring-white", "scale-105");
        }
    });

    document.getElementById("play-answered-notice").classList.remove("hidden");
    document.getElementById("play-status-banner").innerText = "Cevabınız Alındı • Sahneyi İzleyin";

    try {
        const res = await fetch("/api/player/answer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                player_id: currentPlayer.id,
                question_id: currentQuestionId,
                choice: choice
            })
        });

        const data = await res.json();
        if (res.ok && data.success) {
            currentPlayer.score = data.current_score;
            currentPlayer.streak = data.streak;
            currentPlayer.last_is_correct = data.is_correct;
            currentPlayer.last_points = data.points_earned;
            updatePlayerHeader();
            localStorage.setItem("aura_player", JSON.stringify(currentPlayer));
        }
    } catch(e) {
        showToast("Cevap iletilirken ağ hatası oluştu!");
    }
}

// Reset Question Buttons
function resetQuestionButtons() {
    hasAnsweredCurrentQuestion = false;
    document.getElementById("play-answered-notice").classList.add("hidden");
    document.getElementById("play-status-banner").innerText = "Soru Devam Ediyor • Sahneye Bakın!";

    const buttons = ["A", "B", "C", "D"];
    buttons.forEach(opt => {
        const btn = document.getElementById(`play-btn-${opt}`);
        btn.disabled = false;
        btn.classList.remove("opacity-40", "ring-4", "ring-white", "scale-105");
    });
}

// Apply Real-Time State
function applyState(state) {
    if (!state || !currentPlayer) return;

    // Check if room PIN changed
    if (state.room_pin && currentRoomPin && state.room_pin !== currentRoomPin) {
        showToast("Oda PIN kodu güncellendi: " + state.room_pin);
        currentRoomPin = state.room_pin;
    }

    const views = {
        LOBBY: document.getElementById("play-view-lobby"),
        QUESTION: document.getElementById("play-view-question"),
        REVEAL: document.getElementById("play-view-result"),
        LEADERBOARD: document.getElementById("play-view-lobby"),
        PODIUM: document.getElementById("play-view-podium")
    };

    const newStatus = state.status || "LOBBY";

    // Switch view
    Object.keys(views).forEach(key => {
        if (key === newStatus) {
            views[key].classList.remove("hidden");
        } else {
            views[key].classList.add("hidden");
        }
    });

    if (newStatus === "QUESTION") {
        const q = state.current_question;
        if (q && q.id !== currentQuestionId) {
            currentQuestionId = q.id;
            resetQuestionButtons();
        }
    } else if (newStatus === "REVEAL") {
        const isCorrect = currentPlayer.last_is_correct;
        const pts = currentPlayer.last_points || 0;

        const titleEl = document.getElementById("result-title");
        const ptsEl = document.getElementById("result-points");
        const iconEl = document.getElementById("result-icon");

        if (isCorrect) {
            titleEl.innerText = "Tebrikler! Doğru Cevap 🎯";
            ptsEl.innerText = `+${pts} Puan`;
            ptsEl.className = "text-lg font-black text-emerald-400 mb-4";
            iconEl.innerText = "🌟";
        } else {
            titleEl.innerText = "Sağlık Olsun! Yanlış Cevap";
            ptsEl.innerText = "+0 Puan";
            ptsEl.className = "text-lg font-black text-rose-400 mb-4";
            iconEl.innerText = "💔";
        }

        document.getElementById("result-total-score").innerText = currentPlayer.score || 0;
        document.getElementById("result-streak").innerText = `🔥 ${currentPlayer.streak || 0}`;

    } else if (newStatus === "PODIUM") {
        document.getElementById("final-score").innerText = `${currentPlayer.score || 0} Puan`;
    }
}

// Initial Setup
function initPlayer() {
    initAvatarPicker();

    // Check saved session
    const saved = localStorage.getItem("aura_player");
    const savedPin = localStorage.getItem("aura_room_pin");
    if (saved) {
        try {
            currentPlayer = JSON.parse(saved);
            currentRoomPin = savedPin || "";
            updatePlayerHeader();
            showLobbyWaiting();
        } catch(e) {
            localStorage.removeItem("aura_player");
        }
    }

    // Connect to SSE
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

document.addEventListener("DOMContentLoaded", initPlayer);
