# boot the ADSP from apnhlos and keep it up
echo -n /vendor/firmware_mnt/image > /sys/module/firmware_class/parameters/path
H="exec sleep 999998"
pgrep -f "$H" >/dev/null || setsid sh -c "$H < /dev/subsys_adsp" </dev/null >/dev/null 2>&1 &
