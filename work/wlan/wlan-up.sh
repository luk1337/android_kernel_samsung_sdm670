# recovery-only Wi-Fi bring-up test (4.19): firmware mounts + vendor daemons in a chroot
O=ro,shortname=lower,context=u:object_r:firmware_file:s0
R=/mnt/sys
mkdir -p /firmware /vendor $R
mountpoint -q /vendor || mount -o ro /dev/block/by-name/vendor /vendor
mountpoint -q /firmware || mount -t vfat -o $O /dev/block/by-name/modem /firmware
mountpoint -q /vendor/firmware_mnt || mount -t vfat -o $O /dev/block/by-name/apnhlos /vendor/firmware_mnt
mountpoint -q /vendor/firmware-modem || mount -t vfat -o $O /dev/block/by-name/modem /vendor/firmware-modem
mountpoint -q $R || mount -o ro /dev/block/by-name/system $R
mountpoint -q $R/apex || mount -t tmpfs tmpfs $R/apex
if ! mountpoint -q $R/apex/com.android.runtime; then
  mkdir -p $R/apex/com.android.runtime /tmp/apex
  unzip -o -q $R/system/apex/com.android.runtime.apex apex_payload.img -d /tmp/apex
  mount -o ro,loop /tmp/apex/apex_payload.img $R/apex/com.android.runtime
fi
for d in dev proc sys; do mountpoint -q $R/$d || mount --bind /$d $R/$d; done
for d in /vendor /vendor/firmware_mnt /vendor/firmware-modem; do mountpoint -q $R$d || mount --bind $d $R$d; done
mountpoint -q $R/data || mount -t tmpfs tmpfs $R/data
mountpoint -q $R/linkerconfig || mount -t tmpfs tmpfs $R/linkerconfig
mkdir -p $R/data/vendor/rfs/mpss $R/data/vendor/tombstones/rfs $R/data/vendor/pddump
mountpoint -q /sys/kernel/debug || mount -t debugfs none /sys/kernel/debug
for s in /sys/bus/msm_subsys/devices/*; do [ "$(cat $s/name)" = modem ] && echo related > $s/restart_level; done
chmod 755 /tmp/qrtr-ns
pgrep -f /tmp/qrtr-ns >/dev/null || setsid /tmp/qrtr-ns -f > /tmp/qrtr-ns.log 2>&1 < /dev/null &
sleep 1
for b in rmt_storage pd-mapper tftp_server; do
  pgrep -f /vendor/bin/$b >/dev/null || setsid chroot $R /vendor/bin/$b > /tmp/$b.log 2>&1 < /dev/null &
done
sleep 1
pgrep -f "sleep 999999" >/dev/null || setsid sh -c "sleep 999999 < /dev/subsys_modem" </dev/null >/dev/null 2>&1 &
sleep 1
ps -A | grep -E "qrtr-ns|rmt_storage|pd-mapper|tftp_server|sleep 999"
