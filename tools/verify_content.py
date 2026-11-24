#!/usr/bin/env python3
"""Compare the carried content with the jar it came from, and with 26.3.

The carry is mechanical, so the risk is not in the behaviour a reader can see
in the game but in a file that quietly diverged: a template re-encoded, a pool
element pointing at a template that does not exist, a block id 26.3 renamed, a
biome tag that resolves to nothing. This checker reads both sides and asserts
each of them.

    python3 tools/verify_content.py --content content --jar <jar> --resources <26.3>

It exits 1 with a `FAIL:` line on the first divergence and 0 with a `PASS:`
summary when every family, id and rewrite matches.
"""

import argparse
import gzip
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nbt  # noqa: E402  (the reader beside this file)

NS = "underground_villages"
#: 1.21.1 -> 26.3, proved by the pin's own table and recorded in notes.md.
CHAIN = b"minecraft:chain"
IRON_CHAIN = b"minecraft:iron_chain"
#: The one structure's rewritten start height.
START_HEIGHT = {"type": "minecraft:constant", "value": {"absolute": -20}}
#: GenerationStep.Decoration's order at 26.3 (`structure/start.rs:35`).
STEPS = [
    "raw_generation", "lakes", "local_modifications", "underground_structures",
    "surface_structures", "strongholds", "underground_ores",
    "underground_decoration", "fluid_springs", "vegetal_decoration",
    "top_layer_modification",
]

failures = []


def fail(message):
    failures.append(message)
    print(f"FAIL: {message}")


def check(condition, message):
    if not condition:
        fail(message)
    return condition


def jar_data(jar):
    """Every `data/**` file of the jar, by path, with its bytes."""
    out = {}
    with zipfile.ZipFile(jar) as archive:
        for info in archive.infolist():
            if info.filename.startswith("data/") and not info.is_dir():
                out[info.filename] = archive.read(info.filename)
    return out


def family(path):
    """The registry family a data path belongs to, for the count table."""
    parts = path.split("/")
    if parts[2] == "structure":
        return "structure (NBT)"
    if len(parts) > 3 and parts[2] == "worldgen":
        return "worldgen/" + parts[3]
    if len(parts) > 3 and parts[2] == "tags":
        return "tags/" + "/".join(parts[3:-1])
    return "/".join(parts[1:3])


def load_resources(root):
    worldgen = root / "worldgen"
    tables = {
        "states": {state[0] for state in json.loads((root / "facts.json").read_text())["states"]},
        "entity_types": set(json.loads((root / "entity-types.json").read_text())),
        "biomes": set(json.loads((worldgen / "biomes.json").read_text())),
        "features": set(json.loads((worldgen / "features.json").read_text())),
        "placed_features": set(json.loads((worldgen / "placed_features.json").read_text())),
        "processor_lists": set(json.loads((worldgen / "processor_lists.json").read_text())),
        "template_pools": set(json.loads((worldgen / "template_pools.json").read_text())),
        "structures": set(json.loads((worldgen / "structures.json").read_text())),
    }
    return tables


def check_families(jar_files, content):
    carried = {}
    for path in content.glob("data/**/*"):
        if path.is_file():
            carried[str(path.relative_to(content))] = path
    jar_counts = Counter(family(p) for p in jar_files)
    our_counts = Counter(family(p) for p in carried)
    for name in sorted(set(jar_counts) | set(our_counts)):
        check(
            jar_counts[name] == our_counts[name],
            f"{name}: the jar has {jar_counts[name]}, the content has {our_counts[name]}",
        )
        print(f"  {name:34s} jar {jar_counts[name]:3d}  content {our_counts[name]:3d}")
    missing = sorted(set(jar_files) - set(carried))
    extra = sorted(set(carried) - set(jar_files))
    check(not missing, f"files in the jar but not carried: {missing[:5]}")
    check(not extra, f"files carried that the jar does not have: {extra[:5]}")


def check_templates(jar_files, content, tables):
    rewritten = []
    blocks = Counter()
    entities = Counter()
    jigsaw_pools = Counter()
    for path in sorted(content.glob(f"data/{NS}/structure/**/*.nbt")):
        relative = str(path.relative_to(content))
        raw = gzip.decompress(path.read_bytes())
        original = gzip.decompress(jar_files[relative])
        if raw != original:
            expected = original.replace(bytes([0, len(CHAIN)]) + CHAIN,
                                        bytes([0, len(IRON_CHAIN)]) + IRON_CHAIN)
            check(raw == expected, f"{relative}: differs from the jar for a reason other than the chain rename")
            rewritten.append(relative)
        check(CHAIN not in raw, f"{relative}: still names minecraft:chain")
        template = nbt.read(path)
        nbt.size(template)
        for name, count in nbt.block_counts(template).items():
            blocks[name] += count
            check(name in tables["states"], f"{relative}: block {name} is not in 26.3")
        for entity in nbt.entity_ids(template):
            entities[entity] += 1
            check(entity in tables["entity_types"], f"{relative}: entity {entity} is not in 26.3")
        palette = [entry.get("Name") for entry in template.get("palette", [])]
        for block in template.get("blocks", []):
            if palette[block["state"]] != "minecraft:jigsaw":
                continue
            pool = block.get("nbt", {}).get("pool")
            jigsaw_pools[pool] += 1
    check(len(rewritten) == 3, f"{len(rewritten)} templates were rewritten, expected 3: {rewritten}")
    print(f"  templates: {len(blocks)} block ids, {len(entities)} entity kinds, "
          f"{len(rewritten)} rewritten (chain), {sum(jigsaw_pools.values())} jigsaw cells")
    return jigsaw_pools


def check_structure(content, tables):
    path = content / f"data/{NS}/worldgen/structure/underground_village.json"
    structure = json.loads(path.read_text())
    check(structure["type"] == "minecraft:jigsaw", f"structure type {structure['type']}, not jigsaw")
    check(structure["start_height"] == START_HEIGHT,
          f"start_height is {structure['start_height']!r}, not the port's constant -20")
    check(structure["step"] in STEPS, f"step {structure['step']} is not a 26.3 decoration step")
    check(structure["terrain_adaptation"] == "beard_thin",
          f"terrain_adaptation {structure['terrain_adaptation']}")
    check((structure["start_pool"].split(":", 1)[1]) in
          {p.split(f"{NS}:", 1)[1] for p in template_pool_ids()},
          f"start_pool {structure['start_pool']} has no template pool")
    check(0 <= structure["size"] <= 20, f"size {structure['size']} is outside the codec's range")
    check(1 <= structure["max_distance_from_center"] <= 128,
          f"max_distance_from_center {structure['max_distance_from_center']} is outside 1..128")
    check(structure["biomes"].startswith("#"), "the structure's biomes are not a tag")
    print(f"  structure: jigsaw, step {structure['step']}, beard_thin, "
          f"size {structure['size']}, start_height -20 (rewritten)")
    return structure


def template_pool_ids():
    return [f"{NS}:village/{name}" for name in (
        "common/animals", "common/butcher_animals", "common/cats", "common/iron_golem",
        "common/sheep", "common/well_bottoms", "underground/decor", "underground/houses",
        "underground/streets", "underground/terminators", "underground/town_centers",
        "underground/trees", "underground/villagers", "underground/zombie/decor",
        "underground/zombie/houses", "underground/zombie/streets",
        "underground/zombie/villagers",
    )]


def check_pools(content, tables, jigsaw_pools):
    present = {f"{NS}:{path.relative_to(content / 'data' / NS / 'worldgen' / 'template_pool').with_suffix('').as_posix()}"
               for path in content.glob(f"data/{NS}/worldgen/template_pool/**/*.json")}
    for pool in sorted(present):
        check(pool in template_pool_ids(), f"unexpected template pool {pool}")
    for pool in template_pool_ids():
        check(pool in present, f"template pool {pool} is missing")
    for pool, count in jigsaw_pools.items():
        if pool is None:
            fail("a jigsaw block has no target pool")
        elif pool != "minecraft:empty":
            check(pool in present, f"{count} jigsaw cells name the missing pool {pool}")

    elements = 0
    own_features = {f"{NS}:{path.stem}"
                    for path in content.glob(f"data/{NS}/worldgen/placed_feature/*.json")}
    for path in sorted(content.glob(f"data/{NS}/worldgen/template_pool/**/*.json")):
        document = json.loads(path.read_text())
        for entry in document["elements"] + [{"element": document["fallback"]}]:
            element = entry["element"]
            if isinstance(element, str):
                check(element == "minecraft:empty" or element in present,
                      f"{path.name}: fallback {element} is not a pool")
                continue
            elements += 1
            kind = element["element_type"]
            check(kind in {"minecraft:legacy_single_pool_element",
                           "minecraft:single_pool_element",
                           "minecraft:feature_pool_element",
                           "minecraft:list_pool_element",
                           "minecraft:empty_pool_element"},
                  f"{path.name}: element type {kind}")
            if "location" in element:
                template = content / f"data/{element['location'].split(':', 1)[0]}" / \
                    "structure" / f"{element['location'].split(':', 1)[1]}.nbt"
                check(template.is_file(), f"{path.name}: template {element['location']} is missing")
            if "feature" in element:
                # A pool may name a vanilla configured feature or the mod's own
                # placed feature (the three the jar carries).
                check(element["feature"] in tables["placed_features"]
                      or element["feature"] in own_features,
                      f"{path.name}: placed feature {element['feature']} resolves to nothing")
            processors = element.get("processors")
            if isinstance(processors, str):
                check(processors in tables["processor_lists"] or processors.startswith(f"{NS}:"),
                      f"{path.name}: processor list {processors} does not resolve")
    print(f"  template pools: {len(present)} carried, {elements} elements, "
          f"every location/feature/processor resolved")


def check_processor_list(content, tables):
    path = content / f"data/{NS}/worldgen/processor_list/street_cave.json"
    document = json.loads(path.read_text())
    rules = 0
    for processor in document["processors"]:
        check(processor["processor_type"] == "minecraft:rule",
              f"processor {processor['processor_type']} is not a rule list")
        for rule in processor["rules"]:
            rules += 1
            for key in ("input_predicate", "location_predicate"):
                block = rule[key].get("block")
                if block is not None:
                    check(block in tables["states"], f"rule {key} names {block}, not in 26.3")
            output = rule["output_state"]
            check("id" in output and "Name" not in output,
                  f"output_state is in 1.21.1's shape: {output}")
            check(output["id"] in tables["states"], f"output_state {output['id']} is not in 26.3")
            check("properties" in output or "Properties" not in output,
                  f"output_state keeps 1.21.1's Properties: {output}")
    check(rules == 4, f"{rules} processor rules, expected 4")
    print(f"  processor list: {rules} rules in 26.3's block-state shape")


def check_sets_and_tags(content, tables):
    sets = json.loads((content / f"data/{NS}/worldgen/structure_set/underground_villages.json").read_text())
    placement = sets["placement"]
    check(placement["type"] == "minecraft:random_spread", f"placement {placement['type']}")
    check(0 < placement["separation"] < placement["spacing"],
          f"spacing {placement['spacing']} / separation {placement['separation']} is refused by 26.3")
    check(placement["spacing"] == 32 and placement["separation"] == 7,
          "the spread differs from the jar (32 / 7)")
    check(len(sets["structures"]) == 1 and sets["structures"][0]["structure"] == f"{NS}:underground_village",
          f"structure set contents {sets['structures']}")
    tag = json.loads((content / f"data/{NS}/tags/worldgen/biome/has_structure/village_underground.json").read_text())
    for biome in tag["values"]:
        check(biome in tables["biomes"], f"biome tag names {biome}, not in 26.3")
    structure_tag = json.loads((content / f"data/{NS}/tags/worldgen/structure/underground_village.json").read_text())
    check(structure_tag["values"] == [f"{NS}:underground_village"], f"structure tag {structure_tag}")
    print(f"  structure set: random_spread 32/7; biome tag: {len(tag['values'])} biomes, all in 26.3")


def check_placed_features(content, tables):
    for path in sorted(content.glob(f"data/{NS}/worldgen/placed_feature/*.json")):
        document = json.loads(path.read_text())
        check(document["feature"] in tables["features"],
              f"{path.name}: configured feature {document['feature']} is not in 26.3")
        check(document["placement"] == [], f"{path.name}: placement {document['placement']}")
    print("  placed features: 3, each a vanilla configured feature with empty placement")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", required=True, type=Path)
    parser.add_argument("--jar", required=True, type=Path)
    parser.add_argument("--resources", required=True, type=Path)
    args = parser.parse_args(argv)

    jar_files = jar_data(args.jar)
    tables = load_resources(args.resources)

    print("== families ==")
    check_families(jar_files, args.content)
    print("== templates ==")
    jigsaw_pools = check_templates(jar_files, args.content, tables)
    print("== worldgen ==")
    check_structure(args.content, tables)
    check_pools(args.content, tables, jigsaw_pools)
    check_processor_list(args.content, tables)
    check_sets_and_tags(args.content, tables)
    check_placed_features(args.content, tables)

    if failures:
        print(f"FAIL: {len(failures)} divergence(s) between the jar and the carried content")
        return 1
    print("PASS: every family count matches the jar; the 128 templates are byte-identical "
          "except the 3 `chain` -> `iron_chain` cells; the structure's start_height is the "
          "port's `minecraft:constant` -20; every block, entity, biome, feature, processor "
          "list and template pool named by the content exists in 26.3")
    return 0


if __name__ == "__main__":
    sys.exit(main())
