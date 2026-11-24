# Licence and provenance notice — Underground Villages (Horizon port)

This port is **MIT**, the licence of the original mod. `LICENSE` is the MIT text
shipped inside the source jar (`LICENSE_UndergroundVillages`), unmodified, with
the original copyright line. The author of the original mod is **Mrbysco**, with
**ShyNieke** credited as a second author in the mod's own metadata; everything
under `content/` is their work, carried to Minecraft 26.3. This repository and
the delivered `.hmod` carry that notice with them.

## Licence, as read from the mod's own files

| Source | Read |
|---|---|
| `UndergroundVillages-neoforge-1.21.1-4.0.3.jar` (`ports/_shared/licence-cache/`, 282,060 B, SHA-256 `8f965da645cb7e3e75bb1ad8c6c4862d893eb9aff785f5a03ccaba2a92733820`, SHA-1 `a7635a74bf563e4e05296ed9df85d1e90802dfd8`) | `META-INF/neoforge.mods.toml`: `license="MIT"`, `authors="Mrbysco, ShyNieke"`, `modId="underground_villages"`, `displayName="Underground Villages Mod"` |
| The same jar | `LICENSE_UndergroundVillages`, 21 lines: *MIT License, Copyright (c) 2022 Mrbysco* — copied verbatim to `LICENSE` here |
| Modrinth | project `iQ2U9xwG`, version `6MdVRjCY` (`4.0.3`), whose `sha1` is the cached file's — the jar is the published 1.21.1 NeoForge build |
| ATM10 | `ports/_shared/licence-cache/atm10-modlist.json` lists `UndergroundVillages-neoforge-1.21.1-4.0.3.jar` — the pack's own version |
| `ports/ledger.csv` | `underground_villages … MIT`, rank 0 |

Publishing a port still needs the campaign maintainer's approval
(`ARCHITECTURE.md` §8); this notice records the licence, not a permission.

## What comes from where

| What | Where it comes from |
|---|---|
| `content/data/underground_villages/worldgen/**` (25 JSON: 1 structure, 1 structure set, 17 template pools, 1 processor list, 3 placed features, 2 tags) | The jar above, carried by `horizon-port-pack carry` at the campaign pin. One file rewritten for 26.3 (`start_height`), one file's block states rewritten by the carry (`#816`); both are listed in `notes.md` §"Version rewrites". |
| `content/data/underground_villages/structure/**` (128 NBT templates) | The jar, byte-identical except the three `minecraft:chain` palette cells 26.3 renamed to `minecraft:iron_chain` (`tools/apply_patches.py`). |
| `content/horizon-mod.toml` | Written for this port: the carrier's id/name, the port's version `0.1.0`, the authors from the jar. |
| `content/underground_villages.hmod` | Built from `content/` at the pin by `cargo horizon-mod build`, with this notice injected by `tools/notice.py`. |
| `tools/` (the checkers, the patch and the e2e) | This port's own code, MIT. |

No Java was translated and nothing was decompiled: the jar ships 0 templates
that needed re-encoding, and the single code-registered worldgen type it uses
(a height provider) is expressed with the vanilla provider that means the same
number, not with a rewrite of the class.
