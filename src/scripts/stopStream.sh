#!/bin/zsh

echo "[INFO] Finding stream PID..."
pid=$(pgrep gst)

if [ -z "${pid}" ]; then
    echo "[SUCCESS] No streams are running!"
    exit 0
fi

echo "[WARNING] Killing stream with PID $pid..."
kill $pid

# Ensure stream was successfully killed
liveStreams=$(ps | grep "gst-launch-1.0" | grep -v grep &> /dev/null)

if [ -n "${liveStreams}" ]; then
    echo "[ERROR] Failed to terminate stream. Streams still exist:"
    echo $liveStreams
    exit 3
else
    echo "[SUCCESS] Stream $pid was successfully killed!"
fi