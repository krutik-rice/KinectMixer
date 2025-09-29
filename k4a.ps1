# Start subordinates (they will wait for master sync)
Start-Process -NoNewWindow k4arecorder -ArgumentList "--device 1 --color-mode 2160p --external-sync subordinate -l 4 Captures\sub1.mkv"
Start-Process -NoNewWindow k4arecorder -ArgumentList "--device 2 --color-mode 2160p --external-sync subordinate -l 4 Captures\sub2.mkv"

# Give them a moment
Start-Sleep -Seconds 2

# Start master (fires sync pulses)
Start-Process -NoNewWindow k4arecorder -ArgumentList "--device 0 --color-mode 2160p --external-sync master -l 4 Captures\mas.mkv"
