#!/usr/bin/env python3
"""
JARVIS Otonom — monitoring server harian.
Dijalankan oleh systemd timer (default: setiap hari jam 03:00).
Aman: hanya tindakan ringan, semua tercatat di log.
"""
import os, sys, json, subprocess, datetime, urllib.request

LOG_FILE = "/var/log/jarvis-otonom.log"
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("JARVIS_GROQ_MODEL", "openai/gpt-oss-120b")
CHROME_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
             "AppleWebKit/537.36 (KHTML, like Gecko) "
             "Chrome/124.0.0.0 Safari/537.36")

# Threshold tindakan otomatis
RAM_CRITICAL_MB = 200
DISK_CRITICAL_PCT = 90
TEMP_CRITICAL_C = 75
AUTO_HEAL_SERVICES = True
HEAL_BLACKLIST = {
    "systemd-sysctl.service",
    "motd-news.service",
    "mnt-sdcard-swapfile.swap",
    "mnt-sdcard-swapfile2.swap",
    "mnt-sdcard-swapfile2.service",
    "mnt-sdcard-swapfile.service",
}

def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def sh(cmd, timeout=30):
    try:
        p = subprocess.run(["bash", "-c", cmd], capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:
        return 1, str(e)


def collect_data():
    data = {}
    rc, out = sh("free -m | awk '/^Mem:/ {print $7}'")
    data["ram_available_mb"] = int(out) if out.isdigit() else -1
    rc, out = sh("df / | awk 'NR==2 {print $5}' | tr -d '%'")
    data["disk_used_pct"] = int(out) if out.isdigit() else -1
    rc, out = sh("cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | "
                 "awk '{printf \"%.1f\", $1/1000}'")
    try:
        data["temp_c"] = float(out)
    except Exception:
        data["temp_c"] = -1
    rc, out = sh("systemctl --failed --no-legend --plain | awk '{print $1}'")
    data["failed_services"] = [s for s in out.splitlines() if s]
    rc, out = sh("ps -eo comm,%mem --sort=-%mem | head -4 | tail -3")
    data["top_processes"] = out
    rc, out = sh("uptime")
    data["uptime"] = out
    return data


def decide_actions(data):
    actions = []
    if data["ram_available_mb"] >= 0 and data["ram_available_mb"] < RAM_CRITICAL_MB:
        actions.append({
            "action": "clean-ram",
            "reason": f"RAM tinggal {data['ram_available_mb']}MB (<{RAM_CRITICAL_MB}MB)",
            "cmd": "/usr/local/bin/clean-ram"
        })
    if AUTO_HEAL_SERVICES:
        for svc in data["failed_services"]:
            if svc in HEAL_BLACKLIST:
                continue
            actions.append({
                "action": "restart_service",
                "reason": f"Service failed: {svc}",
                "cmd": f"systemctl restart {svc}"
            })
    return actions


def execute_actions(actions, dry_run=False):
    results = []
    for act in actions:
        log(f"  {'[DRY-RUN]' if dry_run else '[EXEC]'} {act['action']}: {act['reason']}")
        if dry_run:
            results.append({"action": act["action"], "status": "skipped (dry-run)",
                            "reason": act["reason"]})
            continue
        rc, out = sh(act["cmd"], timeout=60)
        status = "✅ success" if rc == 0 else f"❌ failed (rc={rc})"
        log(f"    → {status}: {out[:200]}")
        results.append({"action": act["action"], "status": status,
                        "reason": act["reason"], "output": out[:200]})
    return results


def cloud_analyze(data, actions_taken):
    if not GROQ_KEY:
        return "(Cloud OFF — analisis dilewati)"
    try:
        prompt = f"""Data server Armbian STB S905X:
- RAM available: {data['ram_available_mb']} MB
- Disk used: {data['disk_used_pct']}%
- Suhu CPU: {data['temp_c']}°C
- Service gagal: {', '.join(data['failed_services']) or 'tidak ada'}
- Proses terberat: {data['top_processes']}
- Uptime: {data['uptime']}

Tindakan otomatis yang sudah dilakukan:
{json.dumps(actions_taken, indent=2) if actions_taken else 'tidak ada'}

Berikan analisis singkat (3-5 kalimat) dalam bahasa Indonesia:
ATURAN PENTING:
1. Server ini RAM fisiknya HANYA 2GB. JANGAN sebut angka > 2000 MB untuk proses apapun.
2. Gunakan "RAM fisik dipakai proses" di atas — itu angka akurat.
3. JANGAN mengarang hubungan sebab-akibat. Contoh SALAH: "CPU 7% menyebabkan disk penuh."
   CPU tinggi ≠ disk penuh. Disk penuh = file menumpuk.
4. JANGAN sarankan restart service otomatis — bisa putuskan user yang sedang chat.
5. JANGAN mengarang. Kalau tidak yakin, bilang "perlu cek detail".
6. Fokus ke MASALAH NYATA: disk 78% adalah yang paling perlu tindakan.
1. Kondisi server secara keseluruhan
2. Masalah yang perlu perhatian (jika ada)
3. Saran konkret untuk 24 jam ke depan

Gaya JARVIS: ringkas, langsung ke inti, panggil user "Bos"."""
        body = {"model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3, "max_tokens": 600}
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {GROQ_KEY}",
                     "Content-Type": "application/json",
                     "User-Agent": CHROME_UA},
            method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"(Cloud error: {e})"


def kirim_ke_chat(analysis, data, actions):
    """Kirim laporan ke chat server via helper Socket.IO."""
    pesan = f"""🤖 JARVIS Otonom — {datetime.datetime.now():%Y-%m-%d %H:%M}

📊 RAM: {data['ram_available_mb']} MB | Disk: {data['disk_used_pct']}% | Suhu: {data['temp_c']}°C
🔧 Tindakan otomatis: {len(actions)} ({', '.join(a['action'] for a in actions) or 'tidak ada'})

💡 {analysis}"""
    try:
        proc = subprocess.run(
            ["node", "/usr/local/bin/jarvis-chat-send.js", pesan, "JARVIS"],
            capture_output=True, text=True, timeout=15)
        if proc.returncode == 0:
            log("✅ Laporan terkirim ke chat LMS Moodle")
            return True
        log(f"❌ Gagal kirim: {proc.stderr[:200]}")
        return False
    except Exception as e:
        log(f"❌ Exception kirim: {e}")
        return False


def main():
    dry_run = "--dry-run" in sys.argv
    log("=" * 50)
    log(f"JARVIS Otonom dimulai {'(DRY-RUN)' if dry_run else ''}")

    log("Mengumpulkan data server...")
    data = collect_data()
    log(f"  RAM: {data['ram_available_mb']}MB | Disk: {data['disk_used_pct']}% | "
        f"Suhu: {data['temp_c']}°C | Failed: {len(data['failed_services'])}")

    actions = decide_actions(data)
    log(f"Tindakan yang perlu dilakukan: {len(actions)}")
    results = execute_actions(actions, dry_run=dry_run)

    log("Menganalisis dengan cloud...")
    analysis = cloud_analyze(data, results)
    log(f"\n📊 ANALISIS:\n{analysis}\n")

    kirim_ke_chat(analysis, data, results)

    log("JARVIS Otonom selesai")
    log("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
