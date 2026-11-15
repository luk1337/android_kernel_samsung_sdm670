#!/usr/bin/env python3
"""Pull the 4.19 kernel log out of a Samsung upload-mode RAM dump.

1. find the arm64 Image header of the running kernel in low DRAM
2. read log_buf / log_buf_len / log_next_idx / memstart_addr via System.map
3. dump the log buffer and decode printk records

usage: getlog.py OUTDIR
"""
import os
import re
import struct
import subprocess
import sys

S = os.path.dirname(os.path.abspath(__file__))
SAMUP = os.path.join(S, 'ext/sboot_dump/samupload.py')
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
os.chdir(OUT)

KOUT = os.environ.get('KOUT', os.path.join(S, 'out'))
PAGE_OFFSET = 0xffffffc000000000


def dump(start, end):
    for _ in range(3):
        r = subprocess.run(['timeout', '300', 'python3', '-I', SAMUP, 'range',
                            hex(start), hex(end)], capture_output=True, text=True)
        if os.path.exists('range.bin') and \
                os.path.getsize('range.bin') == end - start + 1:
            d = open('range.bin', 'rb').read()
            os.remove('range.bin')
            return d
    sys.exit(f'dump {start:#x}-{end:#x} failed: {r.stdout[-300:]} {r.stderr[-300:]}')


syms = {}
for line in open(os.path.join(KOUT, 'System.map')):
    a, _, n = line.split()
    syms.setdefault(n, int(a, 16))  # first wins: printk log_buf precedes a driver static
img_hdr = open(os.path.join(KOUT, 'arch/arm64/boot/Image'), 'rb').read(64)
img_size = struct.unpack('<Q', img_hdr[16:24])[0]

low = dump(0x80000000, 0x807fffff)
load = None
for m in re.finditer(rb'ARM\x64', low):
    o = m.start() - 0x38
    size = struct.unpack('<Q', low[o + 16:o + 24])[0]
    print(f'Image header at {0x80000000 + o:#x} size {size:#x}')
    # the running copy has the same size; take the last matching one
    if size == img_size:
        load = 0x80000000 + o
if load is None:
    sys.exit('current kernel image not found in low RAM')
print(f'kernel loaded at {load:#x}')


def phys_of(sym):
    return load + syms[sym] - syms['_text']


def read_u64(sym):
    a = phys_of(sym)
    page = dump(a & ~0xfff, (a & ~0xfff) + 0xfff)
    return struct.unpack('<Q', page[a & 0xfff:(a & 0xfff) + 8])[0]


memstart = read_u64('memstart_addr')
log_buf = read_u64('log_buf')
log_len = read_u64('log_buf_len') & 0xffffffff
next_idx = read_u64('log_next_idx') & 0xffffffff
first_idx = read_u64('log_first_idx') & 0xffffffff
lb_phys = log_buf - PAGE_OFFSET + memstart if log_buf >= PAGE_OFFSET \
    else phys_of('__log_buf')
print(f'memstart {memstart:#x} log_buf {log_buf:#x} -> phys {lb_phys:#x} '
      f'len {log_len:#x} first {first_idx:#x} next {next_idx:#x}')

buf = dump(lb_phys, lb_phys + log_len - 1)
open('logbuf.bin', 'wb').write(buf)

out = []
o = first_idx
seen = 0
while seen < log_len:
    if o + 16 > log_len:
        o = 0
    ts, ln, tl, dl, fac, fl = struct.unpack('<QHHHBB', buf[o:o + 16])
    if ln == 0:              # wrap marker
        if o == next_idx:
            break
        o = 0
        continue
    out.append(f'[{ts / 1e9:12.6f}] ' +
               buf[o + 16:o + 16 + tl].decode('utf8', 'replace'))
    o += ln
    seen += ln
    if o == next_idx:
        break
open('kmsg.txt', 'w').write('\n'.join(out) + '\n')
print(f'{len(out)} records -> {os.path.join(OUT, "kmsg.txt")}')
