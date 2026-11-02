# Troubleshooting JARVIS STB

## Cloud Groq 403 / Cloudflare 1010

Penyebab: Python urllib default UA diblokir Cloudflare.

Fix: Pakai jarvis-cloud-helper.py (UA Chrome). Pastikan jarvis memanggil helper, bukan urllib langsung.

Test:

    echo '{"messages":[{"role":"user","content":"test"}],"num_predict":20}' | \
      GROQ_API_KEY="$GROQ_API_KEY" python3 /root/jarvis-cloud-helper.py

## JARVIS Lambat (30-40s per query)

Penyebab: Fallback ke Ollama lokal (qwen3:0.6b) karena cloud gagal.

Fix: Cek GROQ_API_KEY ada dan valid. Cek cloud_ready() di log.

## Ollama Pakai CPU 64% meskipun Idle

Penyebab: OLLAMA_KEEP_ALIVE=5m - model tetap di RAM 5 menit setelah request.

Fix: Set OLLAMA_KEEP_ALIVE=30s di /etc/systemd/system/ollama.service.d/hemat.conf

## CPU Selalu 1.2 GHz, Tidak Turun 500

Penyebab: scaling_max_freq = 1200000 (default), atau governor schedutil (bug kernel 6.1).

Fix: Apply cpu-auto.service (set max_freq 1512000) + cron cpu-auto.sh.

## Swapfile Failed Setiap Boot

Penyebab: Swapfile di SD card hilang / corrupt.

Fix: Disable + mask (ZRAM 1.8 GB sudah cukup):

    sudo systemctl mask mnt-sdcard-swapfile.swap mnt-sdcard-swapfile2.swap
    sudo systemctl reset-failed

## Chat Tidak Menerima Laporan JARVIS

Penyebab: jarvis-chat-send.js butuh socket.io-client di /var/www/chat/node_modules/

Fix:

    cd /var/www/chat && npm install socket.io-client --save
    sudo -u www-data node /usr/local/bin/jarvis-chat-send.js "test"
    # Harus: sent

## JARVIS Otonom Kirim "Node.js 7.7 GB"

Penyebab: Groq salah baca ps aux VSZ (virtual) sebagai RSS (physical).

Fix: Update collect_data() - kirim ps -eo comm,rss (RSS fisik), bukan ps aux (VSZ).

## Service jarvis-otonom Failed Setelah Reboot

Penyebab: /etc/jarvis-otonom.env tidak ada / permission salah.

Fix:

    sudo ls -la /etc/jarvis-otonom.env
    # Harus: -rw------- 1 root root

    # Kalau tidak ada, buat ulang
    sudo cp ~/jarvis-stb/systemd/env.example /etc/jarvis-otonom.env
    sudo nano /etc/jarvis-otonom.env
    sudo chmod 600 /etc/jarvis-otonom.env
    sudo systemctl restart jarvis-otonom.service
