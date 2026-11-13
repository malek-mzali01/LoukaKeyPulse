# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

TEMPLATE = """# Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({a}, {b}, {c}, 0),
    prodvers=({a}, {b}, {c}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', 'Malek Mzali (Louka)'),
            StringStruct('FileDescription', 'LoukaKeyPulse'),
            StringStruct('FileVersion', '{a}.{b}.{c}.0'),
            StringStruct('InternalName', 'LoukaKeyPulse'),
            StringStruct('LegalCopyright', 'Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.'),
            StringStruct('OriginalFilename', 'LoukaKeyPulse.exe'),
            StringStruct('ProductName', 'LoukaKeyPulse'),
            StringStruct('ProductVersion', '{a}.{b}.{c}.0')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main():
    init = (ROOT / "loukakeypulse" / "__init__.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', init)

    if not m:
        sys.exit("__version__ not found")

    a, b, c = m.groups()
    (ROOT / "version_info.txt").write_text(
        TEMPLATE.format(a=a, b=b, c=c), encoding="utf-8"
    )
    print("version_info.txt written for %s.%s.%s" % (a, b, c))


main()
