// Procedural Web Audio API sound synthesizer
// Zero external files, zero 404s, 100% reliable across browsers
class SoundManager {
    constructor() {
        this.ctx = null;
        this.enabled = true;
    }

    _init() {
        if (!this.ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.ctx = new AudioContext();
        }
        if (this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    playClick() {
        if (!this.enabled) return;
        try {
            this._init();
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(600, this.ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(300, this.ctx.currentTime + 0.05);
            gain.gain.setValueAtTime(0.15, this.ctx.currentTime);
            gain.gain.linearRampToValueAtTime(0.01, this.ctx.currentTime + 0.05);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start();
            osc.stop(this.ctx.currentTime + 0.05);
        } catch(e) {}
    }

    playTick() {
        if (!this.enabled) return;
        try {
            this._init();
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(800, this.ctx.currentTime);
            gain.gain.setValueAtTime(0.1, this.ctx.currentTime);
            gain.gain.linearRampToValueAtTime(0.01, this.ctx.currentTime + 0.04);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start();
            osc.stop(this.ctx.currentTime + 0.04);
        } catch(e) {}
    }

    playCorrect() {
        if (!this.enabled) return;
        try {
            this._init();
            const now = this.ctx.currentTime;
            [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
                const osc = this.ctx.createOscillator();
                const gain = this.ctx.createGain();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(freq, now + i * 0.08);
                gain.gain.setValueAtTime(0.2, now + i * 0.08);
                gain.gain.exponentialRampToValueAtTime(0.01, now + i * 0.08 + 0.3);
                osc.connect(gain);
                gain.connect(this.ctx.destination);
                osc.start(now + i * 0.08);
                osc.stop(now + i * 0.08 + 0.3);
            });
        } catch(e) {}
    }

    playWrong() {
        if (!this.enabled) return;
        try {
            this._init();
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(220, now);
            osc.frequency.linearRampToValueAtTime(140, now + 0.3);
            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + 0.35);
        } catch(e) {}
    }

    playPodiumFanfare() {
        if (!this.enabled) return;
        try {
            this._init();
            const now = this.ctx.currentTime;
            const notes = [
                { f: 523.25, d: 0.15, t: 0.0 },
                { f: 659.25, d: 0.15, t: 0.15 },
                { f: 783.99, d: 0.2, t: 0.3 },
                { f: 1046.50, d: 0.6, t: 0.5 }
            ];
            notes.forEach(n => {
                const osc = this.ctx.createOscillator();
                const gain = this.ctx.createGain();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(n.f, now + n.t);
                gain.gain.setValueAtTime(0.3, now + n.t);
                gain.gain.exponentialRampToValueAtTime(0.01, now + n.t + n.d);
                osc.connect(gain);
                gain.connect(this.ctx.destination);
                osc.start(now + n.t);
                osc.stop(now + n.t + n.d);
            });
        } catch(e) {}
    }
}

window.soundManager = new SoundManager();
