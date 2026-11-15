# host-side: daemons+modem, then ADSP, then retrigger the analog codec probe
cd ~/tmp.do4dLU5XtT/work/wlan
adb push wlan-up.sh qrtr-ns qrtr-lookup adsp-up.sh /tmp/ >/dev/null
timeout 60 adb shell 'sh /tmp/wlan-up.sh >/dev/null'
timeout 90 sh -c 'until adb shell "grep State /sys/kernel/debug/icnss/stats" 2>/dev/null | grep -q "FW CONN"; do sleep 3; done'
timeout 20 adb shell 'sh /tmp/adsp-up.sh'
timeout 60 sh -c 'until adb shell dmesg | grep -q "audio_pd.*is up"; do sleep 3; done'
adb shell 'D=$(basename $(ls -d /sys/bus/platform/devices/*anlg-cdc*)); echo $D > /sys/bus/platform/drivers_probe; sleep 3; cat /proc/asound/cards'
