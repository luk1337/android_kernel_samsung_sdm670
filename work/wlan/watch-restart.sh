R=/mnt/sys; P=$R/mnt/vendor/persist
chmod 755 /tmp/fwatch
pkill -f /tmp/fwatch
setsid /tmp/fwatch /vendor/firmware /vendor/firmware/wlan /vendor/firmware/wlan/qca_cld \
  /vendor/firmware-modem/image /vendor/firmware_mnt/image \
  $P/rfs/msm/mpss $P/hlos_rfs/shared $P/rfs/shared $P/rfs $P/hlos_rfs \
  > /tmp/fwatch.log 2>&1 < /dev/null &
sleep 1
kill $(pidof sleep) 2>/dev/null
sleep 3
setsid sh -c "exec sleep 999999 < /dev/subsys_modem" </dev/null >/dev/null 2>&1 &
