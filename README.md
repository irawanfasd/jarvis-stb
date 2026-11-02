# JARVIS STB — Asisten Server Otonom untuk Armbian STB

Kumpulan AI assistant & optimasi server untuk STB Amlogic S905X (Armbian).

## 🎯 Fitur

- **JARVIS v6.0** — Planner agent (cloud Groq) + fallback lokal (Ollama)
- **JARVIS Otonom** — Cek server tiap 24 jam (03:00), kirim laporan ke chat
- **CPU Auto-Scaling** — Idle 500 MHz, beban max 1512 MHz
- **ZRAM Optimized** — Swap compressed di RAM, tanpa swapfile SD
- **Chat Integration** — Kirim laporan via Socket.IO ke LMS Moodle

## 📦 Isi Repo

bin/
├── jarvis # CLI JARVIS (interactive)
├── jarvis-otonom.py # Otonom monitoring 24 jam
├── jarvis-chat-send.js # Helper kirim ke chat (Socket.IO)
├── jarvis-cloud-helper.py # Helper Groq API (UA Chrome)
└── cpu-auto.sh # CPU auto-scaling (500-1512 MHz)

systemd/
├── jarvis-otonom.service # Service monitoring (EnvironmentFile)
├── jarvis-otonom.timer # Timer 03:00 harian
├── cpu-auto.service # Set governor saat boot
└── env.example # Template environment (TANPA key asli)

docs/
├── CPU_SCALING.md # Penjelasan CPU scaling
└── TROUBLESHOOTING.md # Error umum

## 🚀 Quick Start

Lihat [INSTALL.md](INSTALL.md) untuk panduan lengkap.

## 🖥️ Hardware Target

- STB Amlogic S905X (P212), 4 core A53
- RAM 2 GB, eMMC 7.3 GB
- Armbian 25.05, kernel 6.1.137-ophub
- 2 kipas (suhu idle 40°C, beban 52°C)

## ⚙️ Stack

- **AI Cloud**: Groq (`openai/gpt-oss-120b`) — reasoning
- **AI Lokal**: Ollama (`qwen3:0.6b`) — fallback
- **Chat**: Node.js + Socket.IO (port 3001)
- **Web**: nginx (port 80) + cloudflared tunnel
- **CPU**: `userspace` governor + cron auto-scale

## ⚠️ Keamanan

File `systemd/env.example` adalah **template**. API key sebenarnya:

- Disimpan di `/etc/jarvis-otonom.env` (chmod 600, root only)
- **TIDAK** di-push ke repo ini
- **TIDAK** hardcoded di service file

## 📄 Lisensi

MIT
