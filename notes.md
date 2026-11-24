# Underground Villages — port notes

Ported from **Underground Villages Mod 4.0.3** (NeoForge, Minecraft 1.21.1) to
Minecraft Java **26.3** at the campaign SDK pin
**`0a875da91dbb0fdcb7ba8c42c11341aa229af51a`** + horizon-mixins
**`e59da9094f0c2fdda6c627fe9eff22dec6a906f0`** (SDK `api = "0.2"`, game 26.3,
package format 6). **One flat content `.hmod`, no native half, no Rust** — the
jar's only code-shaped piece is a height-provider type that the pin cannot name,
so the carried data uses vanilla's equivalent constant (below).

**Class + tier:** `content` / `data` (`ports/_shared/source-map/atm10-sources.csv`,
mirroring `docs/modpacks/atm10-mods.csv`; `ports/ledger.csv` row
`underground_villages,Underground Villages Mod,content,data,MIT`). The approach is
the tier's **carry-over** shape from `horizon/docs/modpacks.md` §"Worldgen
carry-over": the jar's `data/` moved to 26.3 with three recorded rewrites and no
gameplay code. Nothing was re-tiered.

**Version 0.1.0** — a **first publication**: the id is absent from upstream
`main` and from every open PR, so there is no record to supersede and no `Add`
vs `Update` ambiguity. Cargo's version and the manifest's version agree.

**Licence: MIT → rank 0.** `META-INF/neoforge.mods.toml` says `license="MIT"`,
`authors="Mrbysco, ShyNieke"`; `LICENSE_UndergroundVillages` is the MIT text,
`Copyright (c) 2022 Mrbysco`. `LICENSE` here is that text verbatim and
`LICENSE-NOTICE.md` records the provenance; both are injected into the delivered
`.hmod` (156 entries). MIT makes publication possible; it does not grant it —
the maintainer's approval from `ARCHITECTURE.md` §8 is still required. Upstream
credit: `https://github.com/Mrbysco/UndergroundVillages` (Mrbysco, ShyNieke).

## Provenance

**4.0.3**, `UndergroundVillages-neoforge-1.21.1-4.0.3.jar`, **282,060 B**,
SHA-1 `a7635a74bf563e4e05296ed9df85d1e90802dfd8` (= Modrinth version
`6MdVRjCY`'s file, project `iQ2U9xwG`), SHA-256
`8f965da645cb7e3e75bb1ad8c6c4862d893eb9aff785f5a03ccaba2a92733820`, cached at
`ports/_shared/licence-cache/`. ATM10's own modlist names that exact file, so
this is the pack's version, not a fallback. Full record:
[`../_shared/evidence/underground_villages/SOURCE.md`](../_shared/evidence/underground_villages/SOURCE.md).

## Old-port / jar inventory (read before choosing a family)

The retired port's `FINDINGS.md`/`PLAN.md` were read first; the jar was inventoried
independently before any file was copied. Both agree on **236 entries, 154 of
them content, 153 carried**. No family was invented from the mod's name.

| Family | Files | Notes |
|---|---:|---|
| `worldgen/structure` | 1 | `underground_village`: `minecraft:jigsaw`, pool `village/underground/town_centers`, size 6, reach 80, `underground_decoration`, `beard_thin`, expansion hack |
| `worldgen/structure_set` | 1 | `minecraft:random_spread`, spacing 32, separation 7, salt 11841195 |
| `worldgen/template_pool` | 17 | 7 `village/underground/*`, 4 `village/underground/zombie/*`, 6 `village/common/*` |
| `worldgen/processor_list` | 1 | `street_cave`: 4 `minecraft:rule` rules |
| `worldgen/placed_feature` | 3 | `oak`, `pile_hay`, `flower_plain` — all **vanilla** configured features |
| `tags/worldgen/structure` | 1 | `underground_village` |
| `tags/worldgen/biome/has_structure` | 1 | `village_underground`: the six vanilla biomes |
| `structure/**` (NBT) | 128 | 83 block ids, 9 entity kinds, 467 jigsaw cells naming 16 carried pools + vanilla targets |
| `assets/` | 0 | the jar ships **no** art, lang, model or icon: no block/item is added |
| recipes / loot / advancements | 0 | chests use vanilla village loot tables |

The one code-shaped item is `registration/ModHeightProvider` +
`height/ConfigHeight`: a `HeightProviderType` registered as
`underground_villages:constant`, whose `sample()` returns the config
`Generation.yLevel` (default **-20**). `CommonClass.init()` calls only
`ModHeightProvider.loadClass()`; every other class is datagen or platform
boilerplate that emits the JSON the jar already ships. Upstream repository read
as an analysis aid only (commit `f132ed16d43adfe9167e1e2900982dbcbce3efb2`,
2025-07-02; the five registration classes, `height/ConfigHeight.java`,
`registration/ModHeightProvider.java`, `CommonClass.java`, the tag/config
classes). No Java was translated or decompiled; the clone was deleted.

**Jar-derived asset byte count: 0** — the jar has no `assets/`, so no art could
be carried and none was invented. The package ships only worldgen data and the
two MIT notices.

## SDK surface measured at the pin (before choosing the family)

Grepped `ports/_shared/sdk/0a875da/surface.json` and the cached SDK crates:

- **Present**: `trait:StructuresRegistrar` + `handle:Registrar::register_structure_type`,
  `trait:StructureType`, `trait:StructurePiece`, `handle:LevelRef::structures_at`,
  `trait:BiomeModifiersRegistrar::declare_biome_modifier`, `trait:BiomeRegionsRegistrar`.
  A data-defined `minecraft:jigsaw` structure, its set, pools and biome tag are
  expressible — confirmed in game below.
- **Absent**: any `configured_feature` / `FeatureType` / `PlacementModifier`
  registrar (only `register_structure_type` and `StructureType` answer that
  regex), any `HeightProvider`/`start_height` registrar (grep over every id:
  **0** matches), and `levels_reset`/`reset_vanilla` (that hook lands only in a
  later nightly). None of these is needed by the carried data: all three placed
  features name **vanilla** configured features, terrain adaptation is
  `beard_thin` (data, not a terrain reset), and the one custom provider is
  replaced by vanilla's constant.

So there is **no** `configured-feature-not-registered` or terrain-reset block in
this port. The surface measurement is kept here so a later repin can re-check it
without guessing.

## Version rewrites (every changed byte)

| File | Jar (1.21.1) | 26.3 | Why |
|---|---|---|---|
| `worldgen/structure/underground_village.json` | `start_height.type = underground_villages:constant` | `{"type": "minecraft:constant", "value": {"absolute": -20}}` | The type is a Java-registered `HeightProviderType`; 26.3 has no such type and no registrar at this pin. `RAW=1` (at the retired pin, re-measured in data here) showed an unknown provider falls through to a uniform branch and refuses the **whole** worldgen bundle. Vanilla's constant with the mod's own default (-20) samples the same number. |
| 3 × `structure/village/underground/houses/{cartographer_1,small_house_3,small_house_4}.nbt` | palette cell `minecraft:chain` | `minecraft:iron_chain` | 26.3 renamed the block; an unknown id would silently become air. Byte substitution inside the length-prefixed NBT string, then re-gzip: every other byte is unchanged. |
| `worldgen/processor_list/street_cave.json` | block states `{"Name", "Properties"}` | `{"id", "properties"}` | 26.3 refuses the 1.21.1 shape; the carry's own rewrite. |

`tools/apply_patches.py` performs the first two idempotently and
`tools/carry.py --check` / `tools/verify_content.py` re-check all three.

## `blocked(...)` and deviations

- **`blocked(no-height-provider-registrar)`** — the faithful
  `underground_villages:constant` `HeightProviderType` cannot be named at this
  pin (0 matches in `surface.json`, no registrar trait; R9 forbids a crate that
  could add one). The carried data uses `minecraft:constant` with the mod's
  default -20, which samples the same value. This is a **named gap**, not
  faked data: a player who changed `Generation.yLevel` upstream cannot express
  that value here.
- **`blocked(no-config-surface)`** — a content mod has no config hook at this
  pin, so the village height is baked at -20. Same user-visible consequence as
  the row above; the mod's own default is what ships.
- **Deviation — `/place structure` needs the start box's chunks loaded.**
  The village is ~160 blocks wide at size 6/reach 80, so the e2e forceloads the
  15×15 chunks around the target. Natural generation has no such requirement.
- **Deviation — the zombie variant is carried, not individually asserted.**
  It is the same pool family at weight 1 against 50 for the normal village;
  `tools/verify_content.py` resolves every one of its pools and templates.
- **Deviation — a village is generated inside stone.** `beard_thin` fills
  around the pieces; the templates' air cells are the walkable space. That is
  the mod's design, not a port artefact.

## Upstream defects fixed

**None found.** Checked and clean: all 83 block ids and 9 entity kinds exist in
26.3 except the `chain` rename (a version change, recorded above, not a defect);
all 16 target pools named by 467 jigsaw cells exist; `village/underground/terminators`
— named by no cell — is the fallback of four pools, so it is not dead data; all
four processor rules name real blocks in both slots; the six biome ids exist;
every pool element's `location`/`processors` resolves.

## Coverage (every family the jar ships)

| Family | Status | Proof |
|---|---|---|
| jigsaw structure + structure set | **tested** | `locate structure underground_villages:underground_village` from the carried set; `/place structure` in an empty forceloaded chunk; e2e default |
| 17 template pools / 128 NBT templates | **tested** | 633/894 cut copper stairs, 166/209 cyan terracotta, 35/58 black stained panes read back at their own positions after `/place`; `verify_content.py` byte-compares all 128 templates |
| villagers / animals in templates | **tested** | `ctl entities 64 minecraft:villager` → 12–15 villagers, plus cats/iron golem/bats; control chunk holds 0 |
| 1 processor list (4 rules) | **tested** | 26.3 state shape verified; `beard_thin` adaptation exercised by the placement; all four rules resolve |
| 3 placed features (vanilla) | **tested** | carried and resolved by `verify_content.py`; present in the worldgen bundle at load |
| 2 worldgen tags | **tested** | biome tag drives `/locate` (it starts in the six named biomes); unknown id is refused |
| zombie village variant | **carried, not individually asserted** | `verify_content.py` resolves its 4 pools and all templates; weight 1/50 |
| custom height-provider type | **`blocked(no-height-provider-registrar)`** | 0 registrar matches; vanilla constant -20 carries the default value |
| configurable `Generation.yLevel` | **`blocked(no-config-surface)`** | content-only package; value baked at the mod's default |
| assets / recipes / loot / advancements / blocks / items | **not ported — absent from the jar** | 0 `assets/`, 0 recipes, 0 loot tables; no invented data |

## Verification

Skills: superpowers/using-superpowers,brainstorming,writing-plans,test-driven-development,systematic-debugging,verification-before-completion; BeautifulRust/rust-best-practices (loaded before judging the package/harness; **no Rust written** — this port is data-only).

Pin **`0a875da…`** / mixins **`e59da909…`**; every build/e2e step ran through
`ports/tools/build-slot.sh` with `CARGO_INCREMENTAL=0`, no `--target-dir`.
Evidence: [`../_shared/evidence/underground_villages/`](../_shared/evidence/underground_villages/)
and [`../_shared/evidence/underground_villages-e2e/`](../_shared/evidence/underground_villages-e2e/).

| Check | Evidence |
|---|---|
| data contract **RED** (empty tree) | `tools/carry.py --check --root <empty>` → **16 problems**, exit 1; `data-contract-red.log` |
| data contract **GREEN** | `tools/carry.py --check` → **OK: 153 carried files**, exit 0; `data-contract.log` |
| jar-vs-tree + 26.3 id resolution | `tools/verify_content.py` → **PASS**, exit 0; `verify-content.log` |
| package build | `cargo horizon-mod build` in a slot → `Built ./target/horizon-mod/underground_villages.hmod`; notices injected by `tools/notice.py` |
| package check | `cargo horizon-mod check underground_villages.hmod` → **0.1.0 (mod, API 0.2, both), 238235 bytes, SHA-256 4e2ca3f3…, no code: content only**, exit 0; `sdk-check.log` |
| fits (working pin) | `cargo horizon-mod fits … --build 0a875da` → **"content mod … `fits` doesn't apply"**, exit 2 (the tool's not-applicable status); `sdk-fits.log` |
| fits (other build) | `cargo horizon-mod fits … --build 0b14f8a` → **same content-mod refusal**, exit 2; `sdk-fits.log` |
| whole-archive gate | `verify-sdk-package.py underground_villages` → **1/1**, package + content-only + check + fits + skills all ok |
| e2e default | `tools/e2e.sh` at `0a875da` → **PASS + EXIT:0**; `e2e-default.log` |
| e2e no-mod control | `NO_MOD=1 tools/e2e.sh` → **PASS + EXIT:0** (our id unknown, vanilla igloo places); `e2e-nomod.log` |
| e2e inverted | `SELFTEST=1 tools/e2e.sh` → **FAIL: … + EXIT:1**; `e2e-selftest.log` |
| e2e log gate | `check-e2e-logs.py underground_villages-e2e --strict` → **logs=3 ok=3 missing-exit=0 bad-exit=0**, exit 0 |

In-game transcript (default leg, abridged — full log has every command/reply):

```
locate underground_villages:underground_village -> The nearest ... at [-368, ~, -224] (444 blocks away)
locate underground_villages:not_a_structure      -> Could not find a structure of type "..." nearby
forceload 32 176 256 400 -> Marked 225 chunks ...
place structure underground_villages:underground_village 144 -20 288
  -> Generated structure "underground_villages:underground_village" at 144, -20, 288
find-block minecraft:cut_copper_stairs        -> 633 ; ctl block 147 -16 296 -> minecraft:cut_copper_stairs
find-block minecraft:cyan_terracotta          -> 166 ; ctl block 135 -19 304 -> minecraft:cyan_terracotta
find-block minecraft:black_stained_glass_pane ->  35 ; ctl block 146 -18 296 -> minecraft:black_stained_glass_pane
villagers within 64 blocks: 12 (plus cats, iron golem, bats)
control chunk (nothing placed): 0 cut copper stairs, 0 villagers
unknown id -> There is no structure with type "underground_villages:not_a_structure"
vanilla igloo -> Generated structure "minecraft:igloo" at 400, -20, 288 ; 0 of our blocks
PASS ... EXIT:0
```

`SELFTEST=1` ends: `the placed village has 894 cut copper stairs; this run asserts 0`
→ `FAIL: SELFTEST run: …` → `EXIT:1`.

Re-run:

```sh
python3 ports/underground_villages/tools/carry.py --check
BUILD_LOCAL=1 ports/tools/build-slot.sh run --job UV-build --port ports/underground_villages --step build -- \
    bash -c 'cd ports/underground_villages/content && cargo horizon-mod build'
ports/tools/build-slot.sh run --job UV-e2e --port ports/underground_villages --step e2e -- \
    bash -c 'cd ports/underground_villages && tools/e2e.sh'
# control: NO_MOD=1 … ; inverted: SELFTEST=1 … ; RAW=1 … (see VALIDATION.md)
```

## Artifacts

- `ports/underground_villages/underground_villages.hmod` — **238,235 B**, SHA-256
  **`4e2ca3f361e4a151c3bdb07acbce529c480b863785982b3b52288010ede56b8f`**, **156
  entries**, MIT notices inside. Root manifest mirrors `content/horizon-mod.toml`.
- `ports/underground_villages/content/` — the carry tree (`horizon-mod.toml`,
  `data/underground_villages/**`, 153 files, both rewrites applied).
- `LICENSE`, `LICENSE-NOTICE.md` — MIT text and provenance naming Mrbysco and
  ShyNieke plus the jar's SHA-256; packed inside the `.hmod`.
- `tools/` — `carry.py` (flat-tree data contract), `apply_patches.py`, `nbt.py`,
  `verify_content.py` (jar-vs-tree + 26.3 resolution), `notice.py`, `package.sh`,
  `e2e.sh` (default / `NO_MOD` / `NO_SET` / `RAW` / `SELFTEST` legs).
- `FINDINGS.md` (pre-copy inventory), `PLAN.md` (the retired plan, history),
  `VALIDATION.md` (this migration's gate record), `compatibility.json`.
