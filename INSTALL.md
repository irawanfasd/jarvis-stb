# Panduan Instalasi JARVIS STB

## Peringatan

Repo ini berisi template, bukan siap jalan. Beberapa hal perlu disesuaikan:

1. API Key Groq - isi di /etc/jarvis-otonom.env (jangan di repo)
2. Path - pastikan script ada di /usr/local/bin/ sebelum service jalan
3. Chat server - helper jarvis-chat-send.js butuh socket.io-client di /var/www/chat/node_modules/

## Prasyarat

Install dependency:

    sudo apt install -y python3 python3-pip nodejs npm git

Untuk chat integration (opsional):

    cd /var/www/chat && npm install socket.io-client --save

## Instalasi

### 1. Copy binary ke /usr/local/bin/

    sudo cp bin/jarvis              /usr/local/bin/
    sudo cp bin/jarvis-otonom.py    /usr/local/bin/
    sudo cp bin/jarvis-chat-send.js /usr/local/bin/
    sudo cp bin/jarvis-cloud-helper.py /root/
    sudo cp bin/cpu-auto.sh         /usr/local/bin/

    sudo chmod +x /usr/local/bin/jarvis* /usr/local/bin/cpu-auto.sh /root/jarvis-cloud-helper.py

### 2. Setup environment

    sudo cp systemd/env.example /etc/jarvis-otonom.env
    sudo nano /etc/jarvis-otonom.env
    sudo chmod 600 /etc/jarvis-otonom.env
    sudo chown root:root /etc/jarvis-otonom.env

### 3. Setup systemd services

    sudo cp systemd/jarvis-otonom.service /etc/systemd/system/
    sudo cp systemd/jarvis-otonom.timer   /etc/systemd/system/
    sudo cp systemd/cpu-auto.service      /etc/systemd/system/

    sudo systemctl daemon-reload
    sudo systemctl enable --now jarvis-otonom.timer
    sudo systemctl enable --now cpu-auto.service

### 4. Setup cron CPU auto-scaling

Jalankan:

    sudo crontab -e

Tambahkan 2 baris:

    * * * * * /usr/local/bin/cpu-auto.sh
    * * * * * sleep 30; /usr/local/bin/cpu-auto.sh

### 5. Test

Test JARVIS interactive:

    jarvis
    # Bos > halo
    # Bos > cek suhu
    # Bos > exit

Test otonom:

    sudo systemctl start jarvis-otonom.service
    sleep 20
    tail -20 /var/log/jarvis-otonom.log

Test CPU scaling:

    stress --cpu 8 --timeout 10 &
    sleep 5
    /usr/local/bin/cpu-auto.sh
    cat /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed
    # Harus: 1512000

## Troubleshooting

Lihat docs/TROUBLESHOOTING.md

## Update

    cd ~/jarvis-stb
    git pull
    # Copy ulang binary ke /usr/local/bin/
