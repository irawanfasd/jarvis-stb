#!/bin/bash
# v6: pastikan governor + max_freq, baru set speed

POLICY=/sys/devices/system/cpu/cpufreq/policy0

# 1. Pastikan governor userspace
CUR_GOV=$(cat "$POLICY/scaling_governor" 2>/dev/null)
if [ "$CUR_GOV" != "userspace" ]; then
    echo userspace > "$POLICY/scaling_governor" 2>/dev/null
    sleep 0.3
fi

# 2. Pastikan max_freq 1512000
CUR_MAX=$(cat "$POLICY/scaling_max_freq" 2>/dev/null)
if [ "$CUR_MAX" != "1512000" ]; then
    echo 1512000 > "$POLICY/scaling_max_freq" 2>/dev/null
    sleep 0.2
fi

# 3. Baca CPU usage instan
read_cpu() {
    awk '/^cpu / {print $2+$3+$4+$5+$6+$7+$8, $5}' /proc/stat
}

read -r TOTAL1 IDLE1 <<< "$(read_cpu)"
sleep 1
read -r TOTAL2 IDLE2 <<< "$(read_cpu)"

TOTAL_DIFF=$((TOTAL2 - TOTAL1))
IDLE_DIFF=$((IDLE2 - IDLE1))
if [ "$TOTAL_DIFF" -gt 0 ]; then
    USAGE=$(( (100 * (TOTAL_DIFF - IDLE_DIFF)) / TOTAL_DIFF ))
else
    USAGE=0
fi

# 4. Tentukan target
if [ "$USAGE" -ge 50 ]; then
    TARGET=1512000
elif [ "$USAGE" -ge 30 ]; then
    TARGET=1200000
elif [ "$USAGE" -ge 10 ]; then
    TARGET=1000000
else
    TARGET=500000
fi

# 5. Set speed
CURRENT=$(cat "$POLICY/scaling_setspeed" 2>/dev/null)
if [ "$CURRENT" != "$TARGET" ]; then
    echo "$TARGET" > "$POLICY/scaling_setspeed" 2>/dev/null
fi
