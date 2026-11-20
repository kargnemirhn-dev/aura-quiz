// Player Screen Controller (Strict Kahoot mobile guidelines + Google Animal Avatar System)

const ANIMAL_AVATARS = [
    { emoji: "🐼", name: "Panda" },
    { emoji: "🦊", name: "Tilki" },
    { emoji: "🐱", name: "Kedi" },
    { emoji: "🐺", name: "Kurt" },
    { emoji: "🦁", name: "Aslan" },
    { emoji: "🦉", name: "Baykuş" },
    { emoji: "🐻", name: "Ayı" },
    { emoji: "🐨", name: "Koala" },
    { emoji: "🐰", name: "Tavşan" },
    { emoji: "🐵", name: "Maymun" },
    { emoji: "🐯", name: "Kaplan" },
    { emoji: "🐧", name: "Penguen" },
    { emoji: "🦅", name: "Kartal" },
    { emoji: "🦒", name: "Zürafa" },
    { emoji: "🦔", name: "Kirpi" },
    { emoji: "🐬", name: "Yunus" },
    { emoji: "🐸", name: "Kurbağa" },
    { emoji: "🦩", name: "Flamingo" },
    { emoji: "🦭", name: "Fok" },
    { emoji: "🦦", name: "Su Samuru" }
];

let selectedAvatar = "🐼";
let tempModalAvatar = "🐼";
let currentPlayer = null;
let currentRoomPin = "";
let currentQuestionId = null;
let hasAnsweredCurrentQuestion = false;

// Name input real-time validation (Requirement 3: Ad + Soyad en az 2 kelime ve Sadece Harf)
function validateNameInput(input) {
    const warningEl = document.getElementById("name-validation-warning");
    const val = input.value.trim();
    const rawVal = input.value;
    const turkishLettersRegex = /^[a-zA-ZçÇğĞıİöÖşŞüÜ\s]*$/;

    if (!turkishLettersRegex.test(rawVal)) {
        if (warningEl) {
            warningEl.innerText = "İsimde sadece harf kullanılabilir (Rakam ve özel karakter kabul edilmez).";
            warningEl.classList.remove("hidden");
        }
        input.classList.add("border-amber-500");
        return;
    }

    const words = val.split(/\s+/).filter(w => w.length > 0);
    if (words.length < 2 && val.length > 3) {
        if (warningEl) {
            warningEl.innerText = "Lütfen Ad ve Soyadınızı birlikte giriniz (En az 2 kelime).";
            warningEl.classList.remove("hidden");
        }
        input.classList.add("border-amber-500");
    } else {
        if (warningEl) {
            warningEl.classList.add("hidden");
        }
        input.classList.remove("border-amber-500");
    }
}

// Google-Style Animal Avatar Picker Modal
function openAvatarModal() {
    tempModalAvatar = selectedAvatar;
    renderAnimalAvatarGrid();
    document.getElementById("modal-avatar").classList.remove("hidden");
    window.soundManager.playClick();
}

function closeAvatarModal() {
    document.getElementById("modal-avatar").classList.add("hidden");
    window.soundManager.playClick();
}

function renderAnimalAvatarGrid() {
    const grid = document.getElementById("animal-avatar-grid");
    if (!grid) return;
    grid.innerHTML = ANIMAL_AVATARS.map(item => `
        <button type="button" onclick="selectModalAvatar('${item.emoji}', '${item.name}')" 
            class="flex flex-col items-center justify-center p-3 rounded-2xl bg-slate-950/80 border transition-all hover:bg-slate-800 hover:scale-105 active:scale-95 ${item.emoji === tempModalAvatar ? 'border-indigo-500 bg-indigo-600/20 ring-2 ring-indigo-500/50' : 'border-slate-800'}">
            <span class="text-3xl sm:text-4xl filter drop-shadow mb-1.5">${item.emoji}</span>
            <span class="text-[11px] font-bold text-slate-300 leading-tight">${item.name}</span>
        </button>
    `).join("");

    const currentItem = ANIMAL_AVATARS.find(a => a.emoji === tempModalAvatar) || ANIMAL_AVATARS[0];
    document.getElementById("modal-selected-preview").innerText = currentItem.emoji;
    document.getElementById("modal-selected-name").innerText = currentItem.name;
}

function selectModalAvatar(emoji, name) {
    tempModalAvatar = emoji;
    renderAnimalAvatarGrid();
    window.soundManager.playClick();
}

function confirmAvatarSelection() {
    selectedAvatar = tempModalAvatar;
    const currentItem = ANIMAL_AVATARS.find(a => a.emoji === selectedAvatar) || ANIMAL_AVATARS[0];
    
    // Update main form preview
    document.getElementById("current-avatar-preview").innerText = currentItem.emoji;
    document.getElementById("current-avatar-name").innerText = currentItem.name;
    
    closeAvatarModal();
    showToast(`${currentItem.name} avatarı seçildi! 🐾`);
    window.soundManager.playCorrect();
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

// Join Room Handler with 3-Strike Ban & Letters-Only checks
async function handleJoin(e) {
    e.preventDefault();
    const pin = document.getElementById("input-pin").value.trim();
    const name = document.getElementById("input-name").value.trim();
    const school = document.getElementById("input-school").value.trim() || "Diğer";
    const warningBox = document.getElementById("join-warning-box");

    // Client-side letters only validation
    const lettersRegex = /^[a-zA-ZçÇğĞıİöÖşŞüÜ\s]+$/;
    if (!lettersRegex.test(name)) {
        showToast("İsim sadece harflerden oluşmalıdır!");
        if (warningBox) {
            warningBox.innerText = "İsim alanında rakam veya özel karakter kullanılamaz.";
            warningBox.classList.remove("hidden");
        }
        return;
    }

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
            const errorMsg = data.detail || "Odaya katılırken hata oluştu!";
            if (warningBox) {
                warningBox.innerText = errorMsg;
                warningBox.classList.remove("hidden");
            }

            if (res.status === 403) {
                // Permanent Ban reached
                warningBox.className = "p-3.5 rounded-xl text-xs font-black bg-rose-500/20 border border-rose-500/40 text-rose-300 block";
                document.getElementById("input-name").disabled = true;
                btn.disabled = true;
                btn.innerText = "Giriş Engellendi 🚫";
                showToast("Sistemden 3 ihlal nedeniyle banlandınız!");
                return;
            }

            showToast(errorMsg);
            btn.disabled = false;
            btn.innerText = "Yarışmaya Katıl 🚀";
            return;
        }

        if (warningBox) warningBox.classList.add("hidden");

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

// "Odadan Çık" Button Handler
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

// Live Reaction Sending Handler (Requirement 2)
async function sendReaction(emoji) {
    window.soundManager.playClick();
    if (navigator.vibrate) navigator.vibrate(20);

    const pin = currentRoomPin || (document.getElementById("input-pin") ? document.getElementById("input-pin").value.trim() : "2026");
    const playerName = currentPlayer ? currentPlayer.name : "İzleyici";

    try {
        await fetch("/api/reaction", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                room_pin: pin,
                emoji: emoji,
                player_name: playerName
            })
        });
    } catch(e) {}
}

// Submit Kahoot Button Tap (A, B, C, D)
async function submitAnswer(choice) {
    if (!currentPlayer || !currentQuestionId || hasAnsweredCurrentQuestion) return;

    hasAnsweredCurrentQuestion = true;

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
        
        // Fetch and display player's individual ranking (Requirement 2)
        if (currentPlayer && currentPlayer.id) {
            fetch(`/api/player/rank/${encodeURIComponent(currentPlayer.id)}`)
                .then(res => res.json())
                .then(data => {
                    const rankEl = document.getElementById("player-final-rank");
                    const iconEl = document.getElementById("player-final-rank-icon");
                    if (rankEl && data.rank) {
                        let rankText = "";
                        let icon = "🏆";
                        if (data.rank === 1) {
                            rankText = "1. Şampiyonsun! 🥇";
                            icon = "👑";
                        } else if (data.rank === 2) {
                            rankText = "2. Sıradasın! 🥈";
                            icon = "🥈";
                        } else if (data.rank === 3) {
                            rankText = "3. Sıradasın! 🥉";
                            icon = "🥉";
                        } else {
                            rankText = `${data.rank}. Sıradasın! 🏆`;
                            icon = "🎖️";
                        }
                        if (data.total_players) {
                            rankText += ` (Toplam ${data.total_players} Katılımcı)`;
                        }
                        rankEl.innerText = rankText;
                        if (iconEl) iconEl.innerText = icon;
                    }
                })
                .catch(() => {});
        }
    }
}

// Initial Setup
function initPlayer() {
    renderAnimalAvatarGrid();
    const currentItem = ANIMAL_AVATARS.find(a => a.emoji === selectedAvatar) || ANIMAL_AVATARS[0];
    const previewEl = document.getElementById("current-avatar-preview");
    const nameEl = document.getElementById("current-avatar-name");
    if (previewEl) previewEl.innerText = currentItem.emoji;
    if (nameEl) nameEl.innerText = currentItem.name;

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
