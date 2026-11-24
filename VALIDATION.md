# Underground Villages — SDK migration validation (v0.1.0, first publication)

Pin **`0a875da91dbb0fdcb7ba8c42c11341aa229af51a`**, mixins
**`e59da9094f0c2fdda6c627fe9eff22dec6a906f0`**, game 26.3, SDK `api = "0.2"`,
package format 6. The retired `1d63e0a5` port's findings and carried data were
reused; this is a fresh **flat content `.hmod`**, not an edit of the old artifact.

## The deliverable

| | |
|---|---|
| package | `ports/underground_villages/underground_villages.hmod` |
| size | **238,235 B** |
| SHA-256 | **`4e2ca3f361e4a151c3bdb07acbce529c480b863785982b3b52288010ede56b8f`** |
| version | **0.1.0** (manifest; first publication) |
| entries | **156** (153 carried worldgen files + manifest + LICENSE + LICENSE-NOTICE.md + built-in index) |
| packed `Cargo.lock` | none (content-only; the manifest carries no `[native]` and no Cargo.toml) |
| notices | `LICENSE` + `LICENSE-NOTICE.md` inside the package, appended by `tools/notice.py` |

## Gates (fresh, against the delivered bytes)

| gate | command | result | log |
|---|---|---|---|
| data contract red | `python3 tools/carry.py --check --root <empty>` | **16 problems**, exit 1 | `../_shared/evidence/underground_villages/data-contract-red.log` |
| data contract green | `python3 tools/carry.py --check` | **OK: 153 carried files**, exit 0 | `../_shared/evidence/underground_villages/data-contract.log` |
| jar fidelity + 26.3 ids | `python3 tools/verify_content.py …` | **PASS**, exit 0 | `../_shared/evidence/underground_villages/verify-content.log` |
| package build | `cargo horizon-mod build` (slot, `BUILD_LOCAL=1`) | `Built ./target/horizon-mod/underground_villages.hmod` | — |
| package check (source tree) | `cargo horizon-mod check` in `content/` | *no code: content only* | `sdk-check.log` |
| package check (artifact) | `cargo horizon-mod check underground_villages.hmod` | *0.1.0 (mod, API 0.2, both), 238235 bytes, SHA-256 4e2ca3f3…*, exit 0 | `sdk-check.log` |
| fits — working pin | `cargo horizon-mod fits underground_villages.hmod --build 0a875da` | *"is a content mod, with no code to check against a build; `fits` doesn't apply."*, **exit 2** | `sdk-fits.log` |
| fits — other build | `cargo horizon-mod fits underground_villages.hmod --build 0b14f8a` | **the same content-mod refusal**, **exit 2** | `sdk-fits.log` |
| whole-archive gate | `python3 ports/tools/verify-sdk-package.py underground_villages` | **1/1 package verified** (content-only row, check, fits, skills all ok) | — |
| skipped gates | clippy / unit tests / recipe-type / manifest-deps | no Rust, no recipe type, no other registry mod named | — |

Both `fits` lines are the tool's **documented not-applicable verdict** for a
content mod (exit 2), not a compile failure; `verify-sdk-package.py` accepts it.
There is no second build to compare a content-only package against — a native
package would be a different, invented product. The equivalent non-vacuous
checks here are the jar byte-comparison (`verify_content.py`) and the game
differential (`e2e-nomod.log`).

## In-game legs (`ports/_shared/evidence/underground_villages-e2e/`)

All four ran on the **unmodified `0a875da` control game** with
`--dev-mod content` (except the no-mod leg), through
`build-slot.sh run --step e2e`. RES is the launcher-prepared 26.3 root; the
older external root lacks `fluid_state_definitions` and crashes the game.

| leg | result | log |
|---|---|---|
| modded game (default) | **PASS + EXIT:0** — `/locate` finds the carried structure; `/place` adds 633 cut copper stairs / 166 cyan terracotta / 35 black stained panes read back at their own positions; 12 villagers; an empty chunk holds 0/0; unknown id refused; vanilla igloo places 0 of ours | `e2e-default.log` |
| control (no content mod) | **PASS + EXIT:0** — our id cannot be located or placed; a vanilla igloo still places | `e2e-nomod.log` |
| inverted assertion | **FAIL: … + EXIT:1** — asserts 0 cut copper stairs where there are 894 | `e2e-selftest.log` |
| log gate | `check-e2e-logs.py underground_villages-e2e --strict` → **logs=3 ok=3 missing-exit=0 bad-exit=0** | — |

The two static counterfactuals from the retired port (`NO_SET=1` — remove the
structure set so `/locate` finds nothing while `/place` still works; `RAW=1` —
restore the jar's Java-only `start_height` so the worldgen bundle is refused)
remain available in `tools/e2e.sh` and are documented in `PLAN.md`/`FINDINGS.md`.

The package was **not changed** after its sha was recorded: only root-level
docs (`notes.md`, `VALIDATION.md`, `README.md`, `compatibility.json`) were
edited afterwards, and none of those is packed inside a content `.hmod`.
`verify-sdk-package.py underground_villages` still reports **1/1**.

## Re-run

```sh
python3 ports/underground_villages/tools/carry.py --check
BUILD_LOCAL=1 ports/tools/build-slot.sh run --job UV-build --port ports/underground_villages --step build -- \
    bash -c 'cd ports/underground_villages/content && rm -f Cargo.lock && cargo horizon-mod build'
cd ports/underground_villages && python3 tools/notice.py content/underground_villages.hmod
cp content/underground_villages.hmod underground_villages.hmod
ports/tools/build-slot.sh run --job UV-e2e --port ports/underground_villages --step e2e -- \
    bash -c 'cd ports/underground_villages && tools/e2e.sh'
# control: NO_MOD=1 ; inverted: SELFTEST=1 ; structure-set counterfactual: NO_SET=1
```
