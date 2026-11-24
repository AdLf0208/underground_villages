#!/usr/bin/env python3
"""The two hand rewrites the raw carry cannot make, applied idempotently.

`horizon-port-pack carry` maps a library's worldgen types to vanilla's, but it
cannot know a mod's *own* registered codecs. Underground Villages 4.0.3 uses
exactly one of those, and it also predates 26.3's `chain` -> `iron_chain`
rename. Both are target-version rewrites, which the campaign allows; every one
is listed in `notes.md` and re-checked by `tools/verify_content.py`.

1. `worldgen/structure/underground_village.json`
   `start_height` is `{"type": "underground_villages:constant"}` — a
   `HeightProviderType` registered in Java (`height/ConfigHeight.java`) whose
   `sample()` returns the `Generation.yLevel` config value, default **-20**
   (`UndergroundConfigForge.java:16`). 26.3 has no such type and the structure
   registry refuses the whole bundle on an unknown height provider, so it
   becomes vanilla's `minecraft:constant` with `{"absolute": -20}` — the same
   number the mod samples by default.

2. `data/underground_villages/structure/**/*.nbt`
   Three templates carry a `minecraft:chain` palette cell. 26.3 renamed the
   block to `minecraft:iron_chain`, and the template reader turns an unknown id
   into air, so the chain would silently disappear. The patch replaces the
   length-prefixed NBT string where it stands (`0x000f` + `minecraft:chain` ->
   `0x0014` + `minecraft:iron_chain`) and re-gzips: a byte substitution, not a
   re-encode, so every other byte of the template is untouched.

    python3 tools/apply_patches.py --content content --jar <jar>
"""

import argparse
import gzip
import json
import sys
import zipfile
from pathlib import Path

STRUCTURE = "data/underground_villages/worldgen/structure/underground_village.json"
CHAIN = b"minecraft:chain"
IRON_CHAIN = b"minecraft:iron_chain"
#: 1.21.1's config default, and the value the port adopts.
START_HEIGHT = {"type": "minecraft:constant", "value": {"absolute": -20}}


def patch_structure(content: Path) -> str:
    """Rewrite `start_height`; returns 'rewritten' or 'already patched'."""
    path = content / STRUCTURE
    document = json.loads(path.read_text(encoding="utf-8"))
    current = document.get("start_height")
    if current == START_HEIGHT:
        return "already patched"
    if current != {"type": "underground_villages:constant"}:
        raise SystemExit(f"{path}: unexpected start_height {current!r}")
    # Rebuild in the file's own key order so the diff is one line.
    document["start_height"] = START_HEIGHT
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return "rewritten"


def patch_templates(content: Path) -> list:
    """Rewrite the chain palette cells; returns the templates touched."""
    touched = []
    for path in sorted(content.glob("data/underground_villages/structure/**/*.nbt")):
        raw = gzip.decompress(path.read_bytes())
        if CHAIN not in raw and IRON_CHAIN not in raw:
            continue
        if IRON_CHAIN in raw:
            continue
        # The NBT string is `u16 length` + bytes; a longer name needs a new
        # length, so substitute both halves together.
        old = bytes([0x00, len(CHAIN)]) + CHAIN
        new = bytes([0x00, len(IRON_CHAIN)]) + IRON_CHAIN
        if raw.count(old) != 1:
            raise SystemExit(f"{path}: {raw.count(old)} chain strings, expected 1")
        rewritten = raw.replace(old, new)
        path.write_bytes(gzip.compress(rewritten, mtime=0))
        touched.append(str(path.relative_to(content)))
    return touched


def jar_licence(jar: Path) -> dict:
    """The licence the jar itself declares, so the record cites the file."""
    with zipfile.ZipFile(jar) as archive:
        manifest = archive.read("META-INF/neoforge.mods.toml").decode("utf-8")
    fields = {}
    section = None
    for line in manifest.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[[") or line.startswith("["):
            section = line
            continue
        if section not in (None, "[[mods]]") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() in ("license", "authors", "modId", "version", "displayName"):
            fields[key.strip()] = value.strip().strip('"')
    return fields


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", required=True, type=Path)
    parser.add_argument("--jar", type=Path, help="the source jar, for the licence line")
    args = parser.parse_args(argv)

    structure = patch_structure(args.content)
    templates = patch_templates(args.content)
    report = {
        "start_height": structure,
        "templates_rewritten": templates,
    }
    if args.jar:
        report["jar_licence"] = jar_licence(args.jar)
    print(json.dumps(report, indent=1))
    if structure == "rewritten":
        print("start_height: underground_villages:constant -> minecraft:constant absolute -20")
    for name in templates:
        print(f"chain -> iron_chain: {name}")
    if structure == "already patched" and not templates:
        print("nothing to do: the content already carries both rewrites")
    return 0


if __name__ == "__main__":
    sys.exit(main())
