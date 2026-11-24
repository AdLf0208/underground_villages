#!/usr/bin/env python3
"""Put the licence notices inside a content `.hmod`, so a downloaded copy carries them.

The `.hmod` is the deliverable; this repository's `LICENSE` and
`LICENSE-NOTICE.md` do not travel with it by themselves. A content mod's reader
takes only `horizon-mod.toml`, `assets/` and `data/`, so a notice at the archive
root is shipped and never interpreted.

The rewrite is deterministic: every entry gets one fixed timestamp and mode,
the build's entry order is kept, and the notices are appended in a fixed order,
so two runs over the same build give the same bytes and the same SHA-256.

    python3 tools/notice.py content/underground_villages.hmod
"""

import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
#: The port's notices, in the order they are appended.
NOTICES = ("LICENSE", "LICENSE-NOTICE.md")
#: One timestamp for every entry: `cargo horizon-mod build`'s own zip is
#: deterministic, and re-packing must not reintroduce a clock.
DATE = (2026, 1, 1, 0, 0, 0)


def inject(path: Path) -> dict:
    """Add the notices to `path` in place and describe what it now holds."""
    with zipfile.ZipFile(path) as archive:
        entries = [(info.filename, archive.read(info.filename)) for info in archive.infolist()]
    present = {name for name, _ in entries}
    added = []
    for notice in NOTICES:
        source = ROOT / notice
        if not source.is_file():
            raise SystemExit(f"missing notice for the package: {source}")
        if notice not in present:
            entries.append((notice, source.read_bytes()))
            added.append(notice)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries:
            info = zipfile.ZipInfo(name, DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    return {
        "file": str(path),
        "size": path.stat().st_size,
        "entries": len(entries),
        "added": added,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: tools/notice.py <mod>.hmod")
    result = inject(Path(sys.argv[1]))
    print(f"{result['file']} size={result['size']} sha256={result['sha256']} "
          f"entries={result['entries']} notices={'+'.join(result['added']) or 'already inside'}")
