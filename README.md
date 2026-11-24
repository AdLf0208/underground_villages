# Underground Villages for Horizon

A Horizon 26.3 port of **Underground Villages Mod 4.0.3** by Mrbysco and ShyNieke
([upstream repository](https://github.com/Mrbysco/UndergroundVillages), MIT).
This is a clean-room data carry, not a translation of the Java mod; the original
MIT licence and a provenance notice travel with the package.

The mod adds one jigsaw village that generates **inside the stone at Y=-20**:
streets, houses, a town centre, shops, farms, animals, villagers and a zombie
variant. The port carries all 153 worldgen files (1 structure, 1 structure set,
17 template pools, 1 processor list, 3 placed features, 2 tags and 128 NBT
templates) to 26.3 and proves in game that the structure locates, places and
spawns its villagers.

## What it implements

- the `underground_villages:underground_village` structure and its random-spread
  set (spacing 32, separation 7, salt 11841195) and six-biome start tag;
- all 17 template pools and 128 structure templates, with the three target-version
  rewrites (vanilla constant start height -20; `minecraft:chain` →
  `minecraft:iron_chain` in three houses; 26.3 block-state shape in the processor
  list);
- the three vanilla placed features referenced by the pools.

## What it does not implement

- the mod's configurable `Generation.yLevel`: content-only packages have no
  config surface at this pin, so the height is baked at the upstream default
  **-20** (`blocked(no-config-surface)`);
- the Java-registered `underground_villages:constant` height-provider type — no
  registrar exists at this pin (`blocked(no-height-provider-registrar)`);
- any asset: the jar ships none, so the port invents none (no blocks, items,
  textures, recipes, loot tables or lang keys).

## Install

Install `underground_villages.hmod` through the Horizon launcher. It is a
content mod and needs no native code. Place it in a world and use
`/locate structure underground_villages:underground_village`, then travel there;
`/place structure underground_villages:underground_village <x> -20 <z>` works too
with the surrounding chunks loaded.

## Layout

- `underground_villages.hmod` — the delivered package (SHA-256 and size in
  `VALIDATION.md`).
- `horizon-mod.toml` + `content/` — the flat SDK manifest and the carried
  `data/` tree.
- `tools/` — the data-contract and jar-fidelity checkers and the in-game
  harness.
- `FINDINGS.md`, `PLAN.md`, `notes.md`, `VALIDATION.md`, `LICENSE`,
  `LICENSE-NOTICE.md` — inventory, plan, scope/gaps and gate record.
