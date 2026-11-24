# Underground Villages — jar inventory and carry verdict

Written **before** any file was copied into `content/`, from the jar alone
(`ports/_shared/licence-cache/UndergroundVillages-neoforge-1.21.1-4.0.3.jar`,
282,060 B, SHA-256 `8f965da645cb7e3e75bb1ad8c6c4862d893eb9aff785f5a03ccaba2a92733820`,
SHA-1 `a7635a74bf563e4e05296ed9df85d1e90802dfd8`) and the machine's own census
(`horizon-port-pack check`).

## 1. Provenance

| Field | Value |
|---|---|
| Mod id / name | `underground_villages` / Underground Villages Mod |
| Version | **4.0.3** (NeoForge, Minecraft 1.21.1) |
| File | `UndergroundVillages-neoforge-1.21.1-4.0.3.jar`, 282,060 B |
| SHA-256 | `8f965da645cb7e3e75bb1ad8c6c4862d893eb9aff785f5a03ccaba2a92733820` |
| SHA-1 | `a7635a74bf563e4e05296ed9df85d1e90802dfd8` |
| Modrinth | project `iQ2U9xwG`, version `6MdVRjCY` — its `sha1` is the file's, so the cached jar **is** the Modrinth 1.21.1 NeoForge build |
| ATM10 | `ports/_shared/licence-cache/atm10-modlist.json` lists `UndergroundVillages-neoforge-1.21.1-4.0.3.jar` — the pack's version, not a fallback |
| Licence (jar) | `META-INF/neoforge.mods.toml`: `license="MIT"`; `authors="Mrbysco, ShyNieke"`; `LICENSE_UndergroundVillages` at the jar root is the MIT text, `Copyright (c) 2022 Mrbysco` |
| Ledger rank | **0** (MIT) |

## 2. Contents (236 entries, 154 of them content)

| Family | Files | Notes |
|---|---:|---|
| `data/underground_villages/worldgen/structure` | **1** | `underground_village.json` — `minecraft:jigsaw` |
| `data/underground_villages/worldgen/structure_set` | **1** | `underground_villages.json` — `minecraft:random_spread`, spacing 32, separation 7, salt 11841195 |
| `data/underground_villages/worldgen/template_pool` | **17** | `village/underground/{town_centers,streets,houses,decor,villagers,trees,terminators}`, `village/underground/zombie/{streets,houses,decor,villagers}`, `village/common/{animals,butcher_animals,cats,iron_golem,sheep,well_bottoms}` |
| `data/underground_villages/worldgen/processor_list` | **1** | `street_cave.json` — one `minecraft:rule` list, 4 rules (calcite→oak planks in water, calcite→10 % grass block, grass/dirt→water in water) |
| `data/underground_villages/worldgen/placed_feature` | **3** | `oak`, `pile_hay`, `flower_plain`, each the vanilla configured feature with empty placement |
| `data/underground_villages/tags/worldgen/structure` | **1** | `underground_village` → the one structure |
| `data/underground_villages/tags/worldgen/biome/has_structure` | **1** | `village_underground` → `desert, plains, meadow, savanna, snowy_plains, taiga` |
| `data/underground_villages/structure/**` (NBT templates) | **128** | gzipped structure templates, `village/{common,underground,underground/zombie,decays}/…` |
| `assets/` | **0** | the jar ships **no** assets, no lang, no icon: the mod adds no blocks, items or textures |
| recipes / loot tables / advancements | **0** | chests in the templates use vanilla village loot tables |
| `LICENSE_UndergroundVillages` | 1 | MIT text, `Copyright (c) 2022 Mrbysco` |
| Java classes | 31 (`check.json`: 27 counted as mod classes) | registration/datagen/config boilerplate + **one** runtime type |
| `.cache/*` | 5 | the jar's own build hashes; not content |

Templates: 128 files, 83 distinct block ids, 9 entity kinds
(`minecraft:villager` ×3, `zombie_villager` ×2, `cat` ×10, `horse` ×7, `cow`,
`pig`, `sheep`, `iron_golem`, `bat`). 467 `minecraft:jigsaw` cells carry the
16 target pools (`underground_villages:village/…` — all 17 files exist) and the
vanilla target names `minecraft:street`, `minecraft:building_entrance`,
`minecraft:bottom`.

## 3. What is data and what is code (the census, then the source)

`horizon-port-pack check <jar> content` → **`Partly. 151 worldgen files port;
not 1 worldgen feature or structure type in code.`**

The one code-shaped item is `registration/ModHeightProvider` +
`height/ConfigHeight`: a `HeightProviderType` registered as
`underground_villages:constant`, whose `sample()` returns the config value
`Generation.yLevel` (`forge/…/UndergroundConfigForge.java:16`, default **-20**).
The structure JSON uses it as its `start_height`.

Everything else in the class list is datagen or platform boilerplate:
`ModStructures`/`ModStructureSets`/`ModTemplatePools`/`ModProcessorLists`/
`ModPlacedFeatures` are `BootstrapContext` registrations that *generate* the
JSON the jar also ships (the JSON wins at runtime; a datapack registry entry is
not built from code), and `StructureUpdater`, `UndergroundDatagen` and the two
tag providers are `runData` only. `CommonClass.init()` calls exactly one thing:
`ModHeightProvider.loadClass()`.

**So the carry is: all 153 content files, plus one rewrite of
`start_height`** (see `notes.md` §"Version rewrites"), plus a block rename inside
NBT (below). That is a `content`/`data` port with no native half, which is what
`horizon/docs/modpacks.md` §"Worldgen carry-over" prescribes.

## 4. Target-version mismatches found before copying

| Item | Jar (1.21.1) | 26.3 | Action |
|---|---|---|---|
| `start_height.type` | `underground_villages:constant` (a Java-registered provider) | no such type; an unknown provider fails `StructureRegistry::new` for the whole bundle (`structure/start.rs:357`) | rewrite to `minecraft:constant` with `value: absolute -20` (the mod's own config default) |
| processor `output_state` | `{"Name": …, "Properties": …}` | `{"id": …, "properties": …}` (`#816`) | `horizon-port-pack carry` already rewrote it (1 file, 4 states) |
| block `minecraft:chain` | exists in 1.21.1 | renamed `minecraft:iron_chain` | 3 templates (`cartographer_1`, `small_house_3`, `small_house_4`), one cell each: rewrite the palette string in place |
| `minecraft:legacy_single_pool_element` | not vanilla 1.21.1 | **supported** at the pin (`jigsaw.rs:142`) | none |
| vanilla references | `mossify_20_percent`, `mossify_70_percent`, `zombie_plains`, `oak`, `pile_hay`, `flower_plain`, the 6 biomes | all present in the 26.3 tables | none |
| other 82 block ids + 5 entity kinds | | all present | none |

## 5. What the port must prove

1. A village **places** from `/place structure underground_villages:underground_village`
   and its own blocks read back (`cut_copper_stairs`, `cyan_terracotta`,
   `black_stained_glass_pane` are not natural terrain at y≈-20).
2. The villagers the templates carry **spawn** (`ctl entities … villager`).
3. `/locate structure` finds it from the carried structure set and biome tag.
4. A control run without our content finds nothing of ours, and an unknown id is
   refused.
5. A `SELFTEST=1` leg exits non-zero with a `FAIL:` verdict.
