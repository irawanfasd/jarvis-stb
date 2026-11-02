# CPU Auto-Scaling - STB Amlogic S905X

## Konsep

CPU di STB S905X punya 2 batas:

- scaling_max_freq = 1200000 (dari DTB, default)
- cpuinfo_max_freq = 1512000 (hardware support)

Default scaling_max_freq = 1.2 GHz meskipun hardware bisa 1.5 GHz.

## Solusi

1. Set scaling_max_freq = 1512000 (naikkan batas)
2. Set governor userspace
3. Script cpu-auto.sh (cron tiap 30 detik) pilih freq:
   - Beban >50% -> 1512 MHz
   - Beban 30-50% -> 1200 MHz
   - Beban 10-30% -> 1000 MHz
   - Beban <10% -> 500 MHz

## File Terkait

- /usr/local/bin/cpu-auto.sh - script cron
- /etc/systemd/system/cpu-auto.service - set governor saat boot

## Test

Cek idle:

    cat /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed
    # Harus: 500000

Cek stress:

    stress --cpu 8 --timeout 30 &
    sleep 35
    cat /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed
    # Harus: 1512000

## Kenapa schedutil Tidak Cukup?

schedutil di kernel 6.1 + scpi-cpufreq punya bug: tidak turun ke min freq meskipun idle. Akibatnya CPU selalu 1.0-1.2 GHz meskipun tidak ada beban.

userspace + cron = kontrol penuh, bisa turun ke 500 MHz saat idle.

## Kenapa Tidak Overclock ke 1.9 GHz?

Amlogic membatasi S905 di 1.536 GHz karena stabilitas. Diskusi kernel menunjukkan overclock >1.5 GHz:

- Tidak stabil (bisa hang)
- Peningkatan performa minim (0.1% di 7z)
- Suhu naik drastis (bisa 90 derajat C)

1512 MHz adalah batas aman untuk S905X.
