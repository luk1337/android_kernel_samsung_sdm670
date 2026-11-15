import sys
sys.path.insert(0, sys.argv[1])
from samupload import samsung_upload
s = samsung_upload()
if not s.connect():
    sys.exit("connect failed")
for c in sys.argv[2:]:
    s.cdc.write(c.encode() + b"\0")
    try:
        r = s.cdc.usbread(0x200)
    except Exception as e:
        r = repr(e)
    print(c, "->", r)
