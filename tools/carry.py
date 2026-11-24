#!/usr/bin/env python3
"""Data-contract check for the flat SDK carry of Underground Villages 4.0.3.

The mod's product is its worldgen data: one jigsaw structure, its structure set,
17 template pools, a processor list, three placed features, two tags and 128 NBT
templates. Nothing in the jar is made-up gameplay, so the sharpest contract is a
count-and-shape check of the carried tree against the measured jar inventory in
FINDINGS.md.

    python3 tools/carry.py --check            # the carried tree (content/)
    python3 tools/carry.py --check --root DIR # any tree (an empty DIR is RED)

It exits 1 with a FAIL: line for every divergence and 0 with an OK: summary.
No Java, Mojang files or art are read here; the jar is the provenance authority,
but the contract itself is the shipped tree's exact shape.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = "underground_villages"

# Measured from the jar (FINDINGS.md §2); every family count is exact.
EXPECTED = {
    "worldgen/structure": 1,
    "worldgen/structure_set": 1,
    "worldgen/template_pool": 17,
    "worldgen/processor_list": 1,
    "worldgen/placed_feature": 3,
    "tags/worldgen/structure": 1,
    "tags/worldgen/biome": 1,
    "structure (NBT)": 128,
}
TOTAL = sum(EXPECTED.values())  # 153
CHAIN_REWRITES = {
    "structure/village/underground/houses/cartographer_1.nbt",
    "structure/village/underground/houses/small_house_3.nbt",
    "structure/village/underground/houses/small_house_4.nbt",
}
BIOMES = {"desert", "plains", "meadow", "savanna", "snowy_plains", "taiga"}


def family(rel: str) -> str | None:
    """The registry family of a path relative to data/<ns>/, or None if foreign."""
    if rel.startswith("structure/") and rel.endswith(".nbt"):
        return "structure (NBT)"
    prefix = "worldgen/"
    if rel.startswith(prefix):
        rest = rel[len(prefix):]
        head = rest.split("/", 1)[0]
        key = f"worldgen/{head}"
        return key if key in EXPECTED else None
    if rel.startswith("tags/worldgen/"):
        rest = rel[len("tags/worldgen/"):]
        key = "tags/worldgen/" + rest.split("/", 1)[0]
        return key if key in EXPECTED else None
    return None


def load_tree(root: Path) -> tuple[dict[str, Path], list[str]]:
    """(paths relative to data/<ns>/, problems with the tree layout)."""
    problems: list[str] = []
    base = root / "data" / NS
    out: dict[str, Path] = {}
    if not base.is_dir():
        return out, [f"{base}: missing data/{NS}/ tree"]
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(base))
        out[rel] = path
    for path in (root / "data").rglob("*"):
        if path.is_file() and not str(path.relative_to(root / "data")).startswith(NS + "/"):
            problems.append(f"foreign namespace file packed: {path.relative_to(root)}")
    if (root / "assets").exists():
        problems.append("assets/: the jar ships no assets, so none may be invented")
    return out, problems


def walk(node, fn):
    if isinstance(node, dict):
        fn(node)
        for value in node.values():
            walk(value, fn)
    elif isinstance(node, list):
        for value in node:
            walk(value, fn)


def check(root: Path) -> int:
    problems: list[str] = []
    files, layout = load_tree(root)
    problems.extend(layout)

    seen: dict[str, int] = {}
    for rel in files:
        fam = family(rel)
        if fam:
            seen[fam] = seen.get(fam, 0) + 1
    for fam, want in EXPECTED.items():
        got = seen.get(fam, 0)
        if got != want:
            problems.append(f"{fam}: {got} file(s), expected {want}")
    if len(files) != TOTAL:
        problems.append(f"total files: {len(files)}, expected {TOTAL}")

    # The structure must use vanilla's constant provider (the Java-registered
    # underground_villages:constant type has no registrar at this pin).
    st = files.get("worldgen/structure/underground_village.json")
    if st is None:
        problems.append("the structure JSON is missing")
    else:
        try:
            doc = json.loads(st.read_text())
        except Exception as exc:
            doc = {}
            problems.append(f"structure JSON does not parse: {exc}")
        text = st.read_text(errors="replace")
        if '"underground_villages:constant"' in text:
            problems.append("start_height still names the Java-only height provider type")
        start = doc.get("start_height", {})
        if start.get("type") != "minecraft:constant" \
                or start.get("value", {}).get("absolute") != -20:
            problems.append(f"start_height is not minecraft:constant absolute -20: {start}")
        settings = doc.get("structure_settings", doc.get("settings", {}))
        if settings.get("terrain_adaptation", settings.get("terrainAdaptation")) not in \
                (None, "beard_thin"):
            problems.append("terrain_adaptation is not beard_thin")

    # 26.3 block-state shape in the processor list (the carry's own rewrite).
    pl = files.get("worldgen/processor_list/street_cave.json")
    if pl is None:
        problems.append("the processor list is missing")
    else:
        text = pl.read_text(errors="replace")
        if '"Name"' in text or '"Properties"' in text:
            problems.append("processor list still uses the 1.21.1 {Name,Properties} shape")

    # The three renamed palette cells. The 128 templates have to be gzip NBT.
    chains: list[str] = []
    for rel, path in sorted(files.items()):
        if not rel.startswith("structure/"):
            continue
        try:
            raw = gzip.decompress(path.read_bytes())
        except Exception as exc:
            problems.append(f"{rel}: not gzip-decompressible ({exc})")
            continue
        if b"minecraft:chain" in raw:
            problems.append(f"{rel}: still names the renamed minecraft:chain block")
        if b"minecraft:iron_chain" in raw:
            chains.append(rel)
    for rel in sorted(CHAIN_REWRITES - set(chains)):
        problems.append(f"{rel}: missing the minecraft:iron_chain rewrite")

    # Every jigsaw target pool must exist as a carried template pool.
    pools = {rel[len("worldgen/template_pool/"):-5]
             for rel in files if rel.startswith("worldgen/template_pool/") and rel.endswith(".json")}
    targets: set[str] = set()
    for rel, path in files.items():
        if not rel.startswith("structure/"):
            continue
        try:
            raw = gzip.decompress(path.read_bytes()).decode("utf-8", "replace")
        except Exception:
            continue
        import re
        targets.update(re.findall(r"underground_villages:([a-z0-9_/]+)", raw))
    pools_named = {t for t in targets if t.startswith("village/")}
    missing_pools = sorted(pools_named - pools)
    if missing_pools:
        problems.append(f"template pools named by NBT but not carried: {missing_pools[:5]}")

    tag = next((p for name, p in files.items()
                if name.startswith("tags/worldgen/biome/")
                and name.endswith("village_underground.json")), None)
    if tag is None:
        problems.append("the biome tag is missing")
    else:
        members = {v.removeprefix("minecraft:")
                   for v in json.loads(tag.read_text()).get("values", [])}
        if not BIOMES <= members:
            problems.append(f"biome tag lost members: {sorted(BIOMES - members)}")

    if problems:
        for p in problems:
            print(f"FAIL {p}")
        print(f"carry contract FAILED: {len(problems)} problem(s)")
        return 1
    print(f"OK    {TOTAL} carried files; structure=minecraft:constant -20 beard_thin; "
          f"3 iron_chain rewrites; 26.3 state shape; {len(pools)} pools; 6 biomes; "
          f"no assets or foreign namespace")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--root", type=Path, default=ROOT / "content")
    args = ap.parse_args(argv)
    return check(args.root)


if __name__ == "__main__":
    sys.exit(main())
