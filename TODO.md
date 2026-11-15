# SM-T720 (gts4lvwifi) msm-4.19 port

Tree: `~/lineage-24/kernel/samsung/sdm670`, branch `sdm670-gts4lv`.
Samsung 4.9 reference: `android_kernel_samsung_sdm670`.
Rules: `~/lineage-24/AGENTS.md` (`Assisted-by: LLM - ...` trailer, subject ≤72
chars, no Co-Authored-By). Don't use mainline drivers; pmaports patches are
reference only.

## History layout

Commits are grouped under empty marker commits, oldest first:

1. `=== SDM670 platform support ===` – SoC/DT/driver fixes, not Samsung specific
2. `=== Samsung gts4lv device support ===` – Samsung drivers, gts4lv config
   fragment (`arch/arm64/configs/vendor/samsung/gts4lv.config`), DT
   (all DT changes squash into "arm64: dts: Add Samsung Galaxy Tab S5e Wi-Fi
   (gts4lvwifi) r05")
3. `=== Temporary bring-up hacks ===` – `vendor/bringup.config` and other hacks

To add a commit to an earlier group, commit on top, then rebase with a
`GIT_SEQUENCE_EDITOR` script that moves the line in front of the next marker
(examples: `work/commit/reorder-*.py`). Use `--autosquash` for fixups. Check
that the HEAD tree is the same before and after.

## Tooling (`work/`)

- `kmake [targets]` – build into `work/out` with clang-r596125.
  `kmake defconfig` merges sdm670-perf_defconfig + samsung/gts4lv.config +
  bringup.config.
- `mkboot 'nokaslr printk.devkmsg=on'` – packs Image.gz +
  r05 DTB with the patched Lineage recovery ramdisk (`unpack/ramdisk.new`)
  into `boot-4.19.img` (header v1, AVB footer).
- `flashtest` – from recovery: adb push + dd to `boot`, sets the param
  debuglevel/force-upload so panics land in upload mode, then reboots.
  Then `timeout 150 adb wait-for-recovery` (`wait-for-device` never returns).
- `boot-good.img` – last known-good image. From download mode:
  `heimdall flash --BOOT work/boot-good.img`.
- `getlog.py OUTDIR` – pulls the kernel log from upload mode. Needs
  `out/System.map` + `out/arch/arm64/boot/Image` of the crashed build. The
  whole log stays in the static 1 MB `__log_buf` (bringup.config).
- `uploadreset` – leaves upload mode and reboots (ReSeT/RePoWeR/PoWeRdOwN).
- `ext/sboot_dump` – https://github.com/bkerler/sboot_dump

Upload and download mode are both USB `04e8:685d`. Tell them apart by the
product string: `MSM_UPLOAD` = upload, `SDM710` = download.

The device shell can't do heredocs (no tmp file), so write scripts on the host
and `adb push` them.

## Working

- Display, touch, USB 2/3 both orientations (S2MM005 CCIC, SM5705 MUIC,
  PTN36502)
- Sensors: adsp_factory/ssc_core ported, ssc_hw_rev from androidboot.revision
  selects the r05 IMU/mag axis mapping (wipe persist registry after
  changes); auto-rotate verified in all four orientations
- Charging (SM5705 MFD/charger/FG + sec_battery on IIO ADC), 9 V USB-PD;
  AFC built, untested
- sec_thermistor (ap/pa/bk), xo_therm ADC-TM
- DP alt mode, kernel side (HBR2 x2 link training OK, picture needs Android)
- Pogo keyboard dock drivers probe (FPGA firmware loads); untested, no dock
- Sound card (sdm670-snd-card) registers in recovery with qrtr-ns +
  pd-mapper running and the ADSP started after them
  (work/wlan/audio-test.sh): analog + digital codec, DP audio codec,
  headset/button jack inputs. Speakers work through the CS35L41 amps.
- Deep suspend/resume (AOSD+CXSD, RTC/power key wake) with USB unplugged
- Venus video (SKU 1; the vidc0 -22 is the expected SKU 0 node rejection)
- fastrpc (ADSP/CDSP context banks)
- Fingerprint (ET523, TZ mode), enroll + unlock work: /dev/esfp0 + sysfs; the
  stock HAL/TA detects the sensor. SE15 master needs pinctrl states but
  GPIO81-84 are TZ-owned (reserved), so its states are a config-only
  dummy on GPIO30.
- GPU (Adreno615v2): a615_zap via PIL, SQE/GMU fw, 430 MHz max (SDM670
  bin). Test in recovery: mount apnhlos (vfat,
  context=u:object_r:firmware_file:s0) on /firmware and vendor on
  /vendor, then `cat /dev/kgsl-3d0` prints "OH HAI GPU". Rendering needs
  Android userspace.

## TODO

- [x] DBMD8 voice trigger: dbmdx driver ported from 4.9, /dev/dbmdx-1 up,
      VA fw loads, dspg-dbmdx card registers; hotword e2e untested.
- [x] Speakers: CS35L41 stack imported from the Samsung SM8250 4.19 kernel,
      SEC TDM0 -> 4 amps (RR/RL/FR/FL) hooked up in sdm660 machine driver.
      Leftovers: Cirrus mixer controls (DAI Clocks/Mode, Codec CLK Source)
      not ported, ADM set-params ADSP_EUNSUPPORTED, speaker calibration
      (cs35l41-dsp1-spk-prot-calib) untested.
- [x] ADSP / audio_pd: works in the full LineageOS boot (the glink intent
      timeout was only seen in recovery)
- [ ] Full LineageOS boot on 4.19: boots; audio, Wi-Fi, sensors, video
      verified. Still to check: DP picture, dock
- [x] Wi-Fi: WCN3990 works in the full LineageOS boot (FW_READY never
      came in the recovery setup). Recovery test scripts
      remain in work/wlan/.
- [x] Camera: rear and front work in Aperture
      with proper AE/AWB. Fixes: legacy link_control layout, vfe170 CAMIF
      IRQ masks, IPE write constituent paths, qcom,no-fw-mem-map for
      CICP.FW.1.2, UBWC config from cam_plane_cfg, non-fatal +
      stall-disable camera SMMU banks, no deep prefetch on HF/SF TBUs
      (qsmmuv500 errata 2), EEPROM QUP read rc, Samsung addressed EEPROM
      map (without the cal data AWB ratios were 0 -> NaN WB -> AEC saw
      luma 255 and drove exposure to the minimum).
      Snapshots: CSID RDI decode only where the HW can repack (170 v110
      wrote plain8 RDI -> sheared JPEGs). Video recording: legacy
      msm_media_info header on SDM670 (128x32 NV12 like gralloc/camx,
      on top of the libqcodec2_utils blob patch). Display HAL also got
      the TARGET_USES_ALIGNED_YCBCR/YCRCB_HEIGHT gralloc option.
- [x] Camera leftovers (2026-11-12): front camera verified (preview +
      3264x2448 snapshot, proper AE/AWB). Fixed: "Invalid buf_handle"
      spam (FD put all 3 planes), CSID halt -110 on stop (camx stops the
      sensor first; fall back to immediate halt), actuator "Can't add
      Request ID" (camx never links it, AUTO_MOVE_LENS applies directly),
      gpio12 VANA/VAF sharing (res-mgr compared raw shared-gpios with the
      global TLMM numbers; now `gpios = <&tlmm 12 0>`), ICP
      HFI_ERR_SYS_FATAL recovers instead of BUG(), A5 clock levels
      (src-clock-name + svs/svs_l1/turbo ICP rates).
- [ ] Camera remaining (cosmetic/optional): ICP "DMI_STATUS polling timed
      out" FW message (IPE/BPS PC is off like 4.9, which hardcodes it),
      "CSID:2 IPP resource not available" on acquire (hw mgr also tries
      the CSID lite, upstream behaviour), Samsung sysfs
      (/sys/class/camera/*) missing: parked 2026-11-12, blobs only log
      moduleinfo (isAvailableModule always succeeds), uniplugin
      GetSensorID falls back to 0 without *_camtype, rest is EXIF/factory;
      minimal port would be camtype + moduleinfo, opcode 264 (FLUSH) rejection
      not reproduced. Debug: camx logs via
      `setprop persist.vendor.camera.logInfoMask 0xFFFFFFFF` /
      `logVerboseMask 0x200` (STATS) and restart the provider; kernel
      module debug via /sys/module/cam_debug_util/parameters/debug_mdl;
      kernel dump hooks in work/debug/*.patch.
- [x] Earjack (USB-C analog adapter): MBHC uses the "earjack" IIO
      channel + det-zones-list, drives the sbu-oe/ear-sel/gnd-sel switch,
      extn cable detection off, CCIC_S2MM005_ANALOG_AUDIO=y. Hotplug is
      only seen when the whole adapter is unplugged (passive adapter, no
      detect pin for its 3.5 mm socket).
- [x] "could not get #gpio-cells for /soc/msm_cdc_pinctrl_usbc_audio_en"
      won't fix: harmless CAF noise (of_get_named_gpio before pinctrl
      fallback in sdm660-common.c), stock 4.9 logs it too.
- [x] Built-in mics (fixed 2026-11-15): mixer_paths sets the Samsung-only
      "Enable Micbias" control at HAL init to keep MICB1 on (AMIC routes
      have no bias widget); ported to msm-analog-cdc.c. Other Samsung
      analog/digital codec tweaks from 4.9 (EAR INPUT Mode, RX delay,
      compander peak, SAMSUNG_JACK micbias2) are still not ported.
- [ ] GND/MIC swap path (msm_swap_gnd_mic via us-euro pinctrl) untested:
      needs a CTIA vs OMTP headset on the USB-C adapter.
- [ ] Modem fatals ~40 s after some boots ("subsys-restart: Resetting the
      SoC - modem crashed"); with upload mode armed that panics.
- [x] Random early-boot loops (fixed 2026-11-13, CONFIG_VMAP_STACK off in
      gts4lv.config). The Samsung bootloader loads the kernel at a random
      16 KiB-granular offset; with VMAP_STACK, THREAD_ALIGN is 32 KiB, so
      on odd-16K offsets init_stack trips the entry overflow check ("kernel
      stack overflow" panic at 3 ms in rest_init). CONFIG_PANIC_TIMEOUT=-1
      made that an instant cold PSCI reset with no log. Caught with panic=0
      in boot.img + param DMID/force_upload + plain `adb reboot` (reboot
      recovery resets the param) + key combo into upload. 20/20 clean
      boots incl. 6 odd-16K offsets. getlog.py needed "first symbol wins"
      (a driver also has a static log_buf).
- [ ] QUSB "PLL LOCK" warning on re-init after dwc3 power collapse
      (cosmetic, USB works). Root-caused 2026-11-14 with DIAG builds:
      the init from dwc3_msm_resume -> dwc3_core_init reads
      COMMON_STATUS 0x64 / STAT5 lock=0 and stays unlocked even after
      polling 5 ms. 1.3 ms later, at notify_connect, it reads 0x17 /
      lock=1. The PLL only starts once dwc3 brings the PHY out of
      suspend, so the check in qusb_phy_init is too early on this path.
      The probe-time init locks immediately. The code is unchanged from
      Samsung stock 4.9 / CAF. Fix if wanted: make the WARN_ON a
      dev_dbg (non-fatal, not a hack).
- [ ] eMMC drops to ~6 MB/s (~1 IRQ per 512 B, PIO-like) after a failed
      write: fastbootd writing vbmeta gets `I/O error, dev mmcblk0, sector
      67072` (vbmeta start, write-protected) and the controller stays slow
      until reboot. Fresh boot is fine (64-bit ADMA, HS400ES, 139 MB/s).
      Workaround: don't flash vbmeta. Fix sdhci-msm error recovery.
- [x] Bluetooth: works with the FP4 QTI BT HAL blobs (the Samsung 4.9-era
      HAL only read garbage after the 3.2 Mbaud switch).
- [x] LiveDisplay: mDNIe display modes work (Settings > Display > Colors,
      HAL lists all 6, writes reach the panel). Cosmetic leftover: kernel
      mode_show prints "Current Mode: X_MODE", the HAL parses an int, so
      the current mode always reads back as Dynamic.
- [x] Video: venus HW decode + encode work (screenrecord and scrcpy at
      1600x2560, Glimpse H.264 playback). Fixes: memcore-only vcodec1
      clocks, sdm670 codec/caps table (frame height up to 4096), sessions
      pinned to core 0 via VIDEOCORES_USAGE. Audio capture + c2.android
      Opus encode work (scrcpy audio).
- [ ] Video leftovers: venus init failure path NULL-derefs a regulator in
      __venus_power_on (panics if init ever fails); harmless VP9_LEVEL
      ctrl / fourcc 0 probe errors; caps are sdm845's, not tuned for sdm670
      MBPS limits.
- [x] VP9 hang on YouTube streams (fixed 2026-11-12, platform commit
      "msm: vidc: Keep VP9 hidden frames away from the client"). Venus 4xx
      returns VP9 superframe hidden frames as DROP_FRAME|READONLY FBDs with
      the superframe's input tag; the FP4 (split-mode) C2 HAL completed the
      input on them and leaked the shown frame's output buffer each time.
      Driver now keeps hidden buffers and requeues them on RBR (returns them
      empty during flush/reconfig). Repro clip: yt-dlp -f 303+251 of
      aqz-KE-bpKQ. Verified YouTube app, Glimpse 60fps, seeks, 4K regressions.
- [x] DP hotplug stalled the internal panel (fixed 2026-11-12, platform
      commit "drm/msm/sde: Skip CTL start for video intfs without active
      CTL"). sde_encoder_helper_phys_disable() fired CTL_START on DP's
      video CTL after its timing engine was off; on legacy-CTL SDE 4.x
      that wedges the MDP until power collapse, so the cmd panel's next
      kickoff hung until ESD power-cycled it. Samsung 4.9 never does it.
      Found by bisecting DP teardown steps with a runtime skip mask.
      Plug-in corruption gone too; plug-in only blanks the panel <1 s.
- [x] secdp aux pull-up (pm660l_l7): the SM8250 code asked for a fixed
      3.072 V outside L7's 3.088-3.1 V, so it never enabled, and unplug
      disabled it anyway. Restored 4.9's 3.075-3.2 V and guarded the off
      path (folded into "disp: msm: dp: Add Samsung DisplayPort support").
- [ ] Before upstreaming anywhere: drop the hacks group

## Gotchas

- Vendor QMI blobs use QRTR on 4.19 but nothing ships a name service
  (no in-kernel ns.c, no qrtr-ns): without qrtr-ns the modem never gets
  EFS and fatals after 40 s. Set the modem restart_level to related when
  testing, or a modem crash panics the SoC.

- Recovery SELinux blocks the kernel from reading firmware in /tmp; use
  the ueventd paths (/firmware/image, /vendor/firmware) instead.

- Don't read `/sys/kernel/debug/gpio`: LPI pins without the LPASS clock hang
  the bus.
- qtee_shmbridge must stay off on SDM670, or PAS rejects every firmware image.
- ADSP SMP2P/GLINK on SDM670: SPI 172/bit 26 and SPI 170/bit 24 (not the
  SDM845 values).
- The SPMI arbiter IRQ must go through the PDC, or PMIC wakeups can't leave
  deep sleep.
- 4.19 msmgpio irq_disable also disables the PDC line: drivers must not
  disable_irq() a wake IRQ in suspend (CCIC/MUIC/SM5705 fixed; USB plug
  wake verified).
- 4.19 power_supply: `power_supply_register` returns ERR_PTR. An empty
  properties list fails, and so do uevents on props that return -EINVAL.
- 4.19 DP clock names need the `link_`/`strm0_`/`core_` prefixes.
- 4.19 fastrpc `shared-cb` is a count, not a flag.
