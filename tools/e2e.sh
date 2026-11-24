#!/usr/bin/env bash
# In-game check for the Underground Villages content port (content/data tier:
# 1 jigsaw structure, 1 structure set, 17 template pools, 1 processor list,
# 3 placed features, 2 tags, 128 structure templates), Minecraft 26.3 at the
# SDK campaign pin 0a875da (mixins e59da909). A content-only .hmod is loaded with
# --dev-mod on the unmodified 0a875da control game (launcher-game.sh refuses a
# content-only package for native-build); GAME/CTL come from that export.
#
# A data-tier port's behaviour is worldgen, so the harness checks the layers a
# `.hmod` can break without a code error:
#
#   1. static fidelity — tools/verify_content.py compares the carried content
#      with the ATM10 1.21.1 jar (family counts, byte-identical templates, both
#      recorded rewrites) and resolves every id against the packed 26.3 tables.
#   2. the structure starts — `/locate structure` runs the carried structure
#      set, its biome tag and its start height; an unknown id must be refused.
#   3. the structure places — `/place structure underground_villages:underground_village`
#      in a forceloaded chunk 512 blocks from the located site must put the
#      village's own blocks there (cut copper stairs, cyan terracotta, black
#      stained glass panes: none of them occur in natural terrain at Y=-20) and
#      the villagers its templates carry must be entities afterwards.
#
# Modes:
#   default      the whole scenario; PASS + EXIT:0.
#   SELFTEST=1   the same scenario, then a deliberately false assertion (the
#                placed village has 0 cut copper stairs): the run MUST fail,
#                exit 1, with a FAIL: line.
#   NO_SET=1     counterfactual: a copy of the content without
#                `worldgen/structure_set/`. `/locate` must find nothing while
#                `/place` still works — the structure set is what makes the
#                village generate naturally.
#   NO_MOD=1     control: the same game without the content mod. Our structure
#                id must be unknown to `/locate` and `/place`.
#   RAW=1        counterfactual: the jar's own `start_height` type restored, so
#                the worldgen bundle cannot decode the structure. The launch
#                must fail on it, and the same launch with the rewrite must
#                come up and locate the village.
#   SKIP_VERIFY=1 skips the jar comparison (debugging only).
set -euo pipefail

CLONE=/home/adlf/Desktop/all_the_mods_10_rust_rewrite
PORT=$CLONE/ports/underground_villages
# Name the exact 0a875da control binaries, not via $SHARED: e2e-guard rewrites
# $SHARED to the old 1d63e0a5 shared bin when it resolves this line, which would
# wrap a ctl that cannot speak to the 0a875da game.
CTL=${CTL:-$HOME/.cache/horizon-e2e/0a875da/control/horizon-ctl}
GAME=${GAME:-$HOME/.cache/horizon-e2e/0a875da/control/horizon-client}
# The 0a875da game needs the launcher-prepared 26.3 root: the older external
# /home/adlf/Desktop/horizon/.local/horizon-client/26.3 lacks
# block-behaviours.json::fluid_state_definitions and the game crashes on load.
RES=${RES:-${HORIZON_RES:-$HOME/.cache/horizon-e2e/root/data/horizon-launcher/versions/nightly-2026-11-20-0a875da/.local/horizon-client/26.3}}
SOCK=${SOCK:-/tmp/opencode/underground_villages-e2e.sock}
SELFTEST=${SELFTEST:-0}
NO_SET=${NO_SET:-0}
NO_MOD=${NO_MOD:-0}
RAW=${RAW:-0}
SKIP_VERIFY=${SKIP_VERIFY:-0}
SEED=20261105
STRUCTURE=underground_villages:underground_village

[ -x "$CTL" ] || { echo "missing horizon-ctl: $CTL" >&2; exit 1; }
[ -x "$GAME" ] || { echo "missing horizon-client: $GAME" >&2; exit 1; }
[ -d "$RES/assets" ] || { echo "missing prepared resources: $RES" >&2; exit 1; }
[ -f "$PORT/content/horizon-mod.toml" ] || { echo "missing content mod: $PORT/content" >&2; exit 1; }

say() { echo "== $* =="; }
fail() { echo "FAIL: $*" >&2; exit 1; }
ctl() { "$CTL" --socket "$SOCK" "$@"; }
# Run a game command and return what it said: chat text on success, the error
# text on failure. It never aborts the script, so a reply is always printed and
# the assertions below decide.
run_cmd() { # command line
    local out
    out=$(ctl command "$1" 2>&1) || true
    if printf '%s' "$out" | jq -e . > /dev/null 2>&1; then
        printf '%s' "$out" | jq -r '.chat[0] // .error // "ok"' 2>/dev/null
    else
        printf '%s' "$out"
    fi
}
count_block() { jq -r --arg b "$1" '.count // 0'; }
count_type() { jq -r --arg t "$1" '[.entities[] | select(.type == $t)] | length'; }

if [ "$SKIP_VERIFY" = 1 ]; then
    echo "== jar comparison skipped (SKIP_VERIFY=1) =="
else
    say "data fidelity: carried content vs the ATM10 1.21.1 jar"
    python3 "$PORT/tools/verify_content.py" --content "$PORT/content" \
        --jar "$CLONE/ports/_shared/licence-cache/UndergroundVillages-neoforge-1.21.1-4.0.3.jar" \
        --resources "$RES" || fail "verify_content.py failed"
fi

SCRATCH=$(mktemp -d /tmp/opencode/underground_villages-e2e-home.XXXXXX)
export HORIZON_HOME=$SCRATCH/game
export HORIZON_LAUNCHER_HOME=$SCRATCH/launcher
export XDG_DATA_HOME=$SCRATCH/data
export XDG_CONFIG_HOME=$SCRATCH/config
export HORIZON_NO_AUDIO=1
mkdir -p "$(dirname "$SOCK")"
rm -f "$SOCK"
cd "$SCRATCH"

JAR=$CLONE/ports/_shared/licence-cache/UndergroundVillages-neoforge-1.21.1-4.0.3.jar

# Every leg ends with an EXIT line, RAW included.
cleanup() {
    rc=$?
    ctl quit >/dev/null 2>&1 || true
    sleep 1
    rm -rf "$SCRATCH" || true
    echo "EXIT:$rc"
}
trap cleanup EXIT


# ------------------------------------------------- RAW start_height (no patch)
if [ "$RAW" = 1 ]; then
    say "counterfactual: the jar's own start_height, without the port's rewrite"
    DEV_MOD=$SCRATCH/content-raw
    cp -a "$PORT/content" "$DEV_MOD"
    unzip -p "$JAR" data/underground_villages/worldgen/structure/underground_village.json \
        > "$DEV_MOD/data/underground_villages/worldgen/structure/underground_village.json"
    grep -q '"type": "underground_villages:constant"' \
        "$DEV_MOD/data/underground_villages/worldgen/structure/underground_village.json" \
        || fail "could not restore the jar's start_height for the counterfactual"
    echo "counterfactual content: $DEV_MOD (start_height = underground_villages:constant)"

    # Each leg gets its own game home, so its log holds one launch and nothing
    # else: the decode failure is deterministic, the client's reaction to it is
    # not, so the assertion reads the log rather than an exit code.
    LOG_RAW=$SCRATCH/raw-home/logs/latest.log
    LOG_PATCHED=$SCRATCH/patched-home/logs/latest.log
    launch_leg() { # home world dev-mod -> the launch command's exit status
        local home=$1
        mkdir -p "$SCRATCH/$home"
        rm -f "$SOCK"
        set +e
        HORIZON_HOME=$SCRATCH/$home "$CTL" --socket "$SOCK" launch \
            --game "$GAME" --world "$2" --seed "$SEED" --creative --offscreen --wait \
            --game-dir "$SCRATCH/$home/game" --resources "$RES" --dev-mod "$3" \
            > "$SCRATCH/launch-$home.json" 2>&1
        echo $?
    }
    wait_for_log() { # file pattern seconds
        local i=0
        while [ "$i" -lt "$3" ]; do
            grep -q "$2" "$1" 2>/dev/null && return 0
            sleep 1
            i=$((i + 1))
        done
        return 1
    }

    RAW_RC=$(launch_leg raw-home UvRaw "$DEV_MOD")
    echo "raw launch exit=$RAW_RC (the client may exit when the integrated server stops)"
    wait_for_log "$LOG_RAW" "invalid world generation field: min_inclusive" 90 \
        || fail "the raw start_height did not stop worldgen (no log at $LOG_RAW?)"
    grep -E "integrated server|world generation field" "$LOG_RAW" | tail -3
    echo "without the rewrite the worldgen bundle refuses the structure: an unknown height"
    echo "provider type falls through to the uniform min_inclusive branch, and the server stops"

    say "the same launch with the port's rewrite must come up, without the error, and locate"
    PATCHED_RC=$(launch_leg patched-home UvPatched "$PORT/content")
    PATCHED_OK=$(jq -r '.launch.ok // "no-reply"' "$SCRATCH/launch-patched-home.json" 2>/dev/null | tail -1)
    echo "patched launch exit=$PATCHED_RC reply ok=$PATCHED_OK"
    [ "$PATCHED_RC" = 0 ] || fail "the patched content did not launch (exit $PATCHED_RC)"
    [ "$PATCHED_OK" = true ] || fail "the patched launch is not up: $PATCHED_OK"
    ctl wait-ready 240 > /dev/null
    if grep -q "world generation field" "$LOG_PATCHED"; then
        grep "world generation field" "$LOG_PATCHED" >&2
        fail "the patched content still reports a worldgen decode failure"
    fi
    echo "the patched launch logs no worldgen decode failure"
    SITE=$(run_cmd "locate structure $STRUCTURE")
    echo "locate $STRUCTURE -> $SITE"
    case "$SITE" in
        "The nearest $STRUCTURE is at ["*) ;;
        *) fail "the patched content launched but the village does not locate: $SITE" ;;
    esac
    echo "PASS: the jar's own start_height type stops world generation (the server refuses the"
    echo "bundle on it); the port's rewrite to minecraft:constant absolute -20 is what makes the"
    echo "same launch load the world and locate the village"
    exit 0
fi

DEV_MOD=""
if [ "$NO_MOD" != 1 ]; then
    DEV_MOD=$PORT/content
    if [ "$NO_SET" = 1 ]; then
        DEV_MOD=$SCRATCH/content-no-set
        cp -a "$PORT/content" "$DEV_MOD"
        rm -rf "$DEV_MOD/data/underground_villages/worldgen/structure_set"
        [ ! -e "$DEV_MOD/data/underground_villages/worldgen/structure_set" ] \
            || fail "could not remove the structure set for the counterfactual"
        echo "counterfactual content: $DEV_MOD (worldgen/structure_set removed)"
    fi
fi

if [ -n "$DEV_MOD" ]; then
    say "launch (offscreen, creative, Overworld, --dev-mod $(basename "$DEV_MOD"))"
    set -- --dev-mod "$DEV_MOD"
else
    say "launch (offscreen, creative, Overworld, NO content mod)"
    set --
fi
"$CTL" --socket "$SOCK" launch \
    --game "$GAME" --world UvE2E --seed "$SEED" --creative --offscreen --wait \
    --game-dir "$SCRATCH/game" --resources "$RES" "$@" \
    > "$SCRATCH/launch.json"
jq -c '{dimension, creative, game: .launch.game, socket: .launch.socket, ok: .launch.ok}' \
    "$SCRATCH/launch.json"
ctl wait-ready 240 > /dev/null
if ctl logs --lines 4000 2>/dev/null | grep -q "content mods not loaded"; then
    ctl logs --lines 4000 | grep "content mods not loaded" >&2
    fail "the content mod did not load"
fi
if [ -n "$DEV_MOD" ]; then
    ctl logs --lines 4000 | grep -q "content from 1 mod(s)" \
        || fail "the log does not report one loaded content mod"
    echo "content mod loaded (no 'content mods not loaded', one mod reported)"
else
    echo "no content mod loaded (control run)"
fi

locate_at() { run_cmd "locate structure $1"; }
# The world-side commands print their reply and are checked separately: with
# `set -e`, a silent redirect would hide which one failed, and a `wait-ready`
# timeout is a scheduling signal, not a verdict on the port.
forceload_area() { # x z radius
    local reply
    reply=$(run_cmd "forceload add $(( $1 - $3 )) $(( $2 - $3 )) $(( $1 + $3 )) $(( $2 + $3 ))")
    echo "forceload $(($1 - $3)) $(($2 - $3)) $(($1 + $3)) $(($2 + $3)) -> $reply"
}
teleport_to() { # x y z
    local reply
    reply=$(run_cmd "tp @s $1 $2 $3")
    echo "tp @s $1 $2 $3 -> $reply"
}
settle() { # seconds
    ctl wait-ready "$1" > /dev/null 2>&1 \
        || echo "wait-ready ${1}s reported $? (chunks may still be streamed)"
    ctl wait 40 > /dev/null 2>&1 || echo "wait 40 reported $?"
}
near() { # x y z tolerance -> is the player there?
    ctl state | jq -e --argjson t "$4" --argjson x "$1" --argjson y "$2" --argjson z "$3" \
        '(.player.position[0] - $x | fabs) <= $t and (.player.position[1] - $y | fabs) <= $t
         and (.player.position[2] - $z | fabs) <= $t' > /dev/null
}

# ------------------------------------------------------------ NO_MOD control
if [ "$NO_MOD" = 1 ]; then
    say "control: without the content mod nothing of ours exists"
    FOUND=$(locate_at "$STRUCTURE")
    echo "locate $STRUCTURE -> $FOUND"
    case "$FOUND" in
        "Could not find"*) ;;
        *) fail "the structure was located without the content mod: $FOUND" ;;
    esac
    BAD=$(run_cmd "place structure $STRUCTURE 0 -20 0")
    echo "place $STRUCTURE -> $BAD"
    case "$BAD" in
        *"no structure with type"*) ;;
        *) fail "the structure was placed without the content mod: $BAD" ;;
    esac
    IGLOO=$(run_cmd "place structure minecraft:igloo 0 100 0")
    echo "place minecraft:igloo -> $IGLOO"
    case "$IGLOO" in
        Generated\ structure\ \"minecraft:igloo\"*) ;;
        *) fail "the vanilla control did not place without the content mod: $IGLOO" ;;
    esac
    echo "PASS: the structure id only exists because our content is loaded (a vanilla structure still places)"
    exit 0
fi

# ------------------------------------------------------------------ worldgen
say "worldgen: the carried structure set locates the village"
SITE=$(locate_at "$STRUCTURE")
echo "locate $STRUCTURE -> $SITE"
UNKNOWN=$(locate_at underground_villages:not_a_structure)
echo "locate underground_villages:not_a_structure -> $UNKNOWN"
case "$UNKNOWN" in
    "Could not find"*) ;;
    *) fail "an unknown structure id was located: $UNKNOWN" ;;
esac

if [ "$NO_SET" = 1 ]; then
    case "$SITE" in
        "Could not find"*) echo "without worldgen/structure_set the village cannot start (it is the set that places it)" ;;
        *) fail "counterfactual: the village was located without its structure set: $SITE" ;;
    esac
    # The structure itself is still there, so `/place` must still work: proof
    # that the missing file is the generation, not the structure's data.
    forceload_area 0 0 96
    teleport_to 8.5 120 8.5
    settle 600
    PLACED=$(run_cmd "place structure $STRUCTURE 0 -20 0")
    echo "place $STRUCTURE -> $PLACED"
    case "$PLACED" in
        Generated\ structure\ \"underground_villages:underground_village\"*) ;;
        *) fail "the structure no longer places without its set: $PLACED" ;;
    esac
    # The village is at Y=-20: read it from there, not from the teleport's
    # vantage point (find-block scans around the player's eye).
    teleport_to 8.5 -20 8.5
    settle 600
    near 8.5 -20 8.5 8 || fail "the player did not reach the village at 8.5 -20 8.5"
    STAIRS=$(ctl find-block minecraft:cut_copper_stairs 64 | count_block minecraft:cut_copper_stairs)
    echo "cut copper stairs within 64 blocks of the origin: $STAIRS"
    [ "$STAIRS" -ge 1 ] || fail "the placed structure wrote no cut copper stairs"
    echo "PASS: the structure set is what makes the village generate naturally (its biome tag, spread and salt), while the structure itself still places on command"
    exit 0
fi

case "$SITE" in
    "The nearest $STRUCTURE is at ["*) ;;
    *) fail "$STRUCTURE does not start from its carried structure set: $SITE" ;;
esac
read -r SITE_X SITE_Z <<<"$(echo "$SITE" | python3 -c '
import re, sys
text = sys.stdin.read()
match = re.search(r"at \[(-?[0-9]+), ~, (-?[0-9]+)\]", text)
if not match:
    raise SystemExit(f"cannot parse the locate reply: {text!r}")
print(match.group(1), match.group(2))')"
# 512 blocks = 16 chunks east and south: outside the located start's reach, so
# the box holds nothing of ours before `/place`.
PX=$(( (SITE_X + 512) & ~15 ))
PZ=$(( (SITE_Z + 512) & ~15 ))
echo "located site $SITE_X $SITE_Z; placing in the chunk at $PX $PZ (512 blocks away)"

# ---------------------------------------------------------------- placement
say "placement: /place structure $STRUCTURE $PX -20 $PZ"
forceload_area "$PX" "$PZ" 112
teleport_to "$((PX + 8)).5" -20 "$((PZ + 8)).5"
settle 600
DIM=$(ctl state | jq -r '.dimension')
[ "$DIM" = minecraft:overworld ] || fail "the player is in $DIM, not the Overworld"
near "$((PX + 8)).5" -20 "$((PZ + 8)).5" 8 \
    || fail "the player did not reach $((PX + 8)) -20 $((PZ + 8)): $(ctl state | jq -c '.player.position')"
echo "player in $DIM at $(ctl state | jq -c '.player.position'), chunks settled"

BEFORE=$(ctl find-block minecraft:cut_copper_stairs 48)
BEFORE_N=$(echo "$BEFORE" | count_block minecraft:cut_copper_stairs)
echo "before: cut copper stairs within 48 blocks: $BEFORE_N"
[ "$BEFORE_N" = 0 ] || fail "the placement area already holds $BEFORE_N cut copper stairs before /place"

PLACED=$(run_cmd "place structure $STRUCTURE $PX -20 $PZ")
echo "reply: $PLACED"
case "$PLACED" in
    Generated\ structure\ \"underground_villages:underground_village\"*) ;;
    *) fail "$STRUCTURE did not place: $PLACED" ;;
esac
ctl wait 20 > /dev/null

# The village's own blocks, at the village's own positions. None of these three
# occur in natural terrain, and the templates carry thousands of the first.
for block in minecraft:cut_copper_stairs minecraft:cyan_terracotta minecraft:black_stained_glass_pane; do
    reply=$(ctl find-block "$block" 48)
    got=$(echo "$reply" | count_block "$block")
    echo "find-block $block -> $got"
    [ "$got" -ge 1 ] || fail "the placed village has no $block ($got)"
    read -r bx by bz <<<"$(echo "$reply" | jq -r '.nearest[0].pos | @tsv')"
    read_back=$(ctl block "$bx" "$by" "$bz" | jq -r '.block')
    echo "ctl block $bx $by $bz -> $read_back"
    case "$read_back" in
        "$block"*) ;;
        *) fail "$block at $bx $by $bz reads $read_back" ;;
    esac
done
echo "the village's cut copper stairs, cyan terracotta and black stained glass panes are in the world at their own positions"

say "entities: the templates' villagers and animals are in the village"
ctl wait 20 > /dev/null
VILLAGERS=$(ctl entities 64 minecraft:villager | count_type minecraft:villager)
echo "villagers within 64 blocks: $VILLAGERS"
ctl entities 64 | jq -c '[.entities[] | .type] | group_by(.) | map({(.[0]): length}) | add' >&2 || true
[ "$VILLAGERS" -ge 1 ] || fail "the placed village spawned no villager"
echo "the village's villagers are entities in the world ($VILLAGERS)"

# The villagers must come from *our* structure: count them before placing again
# in a control chunk where no village is placed.
say "controls: an unknown id is refused, a vanilla structure places, no village appears where none is placed"
CX=$((PX + 256))
CZ=$PZ
forceload_area "$CX" "$CZ" 96
teleport_to "$((CX + 8)).5" -20 "$((CZ + 8)).5"
settle 600
near "$((CX + 8)).5" -20 "$((CZ + 8)).5" 8 \
    || fail "the player did not reach the control chunk at $((CX + 8)) -20 $((CZ + 8))"
CONTROL_STAIRS=$(ctl find-block minecraft:cut_copper_stairs 48 | count_block minecraft:cut_copper_stairs)
CONTROL_VILLAGERS=$(ctl entities 48 minecraft:villager | count_type minecraft:villager)
echo "control chunk: $CONTROL_STAIRS cut copper stairs, $CONTROL_VILLAGERS villagers (nothing placed here)"
[ "$CONTROL_STAIRS" = 0 ] || fail "the control chunk holds $CONTROL_STAIRS cut copper stairs without a placement"
[ "$CONTROL_VILLAGERS" = 0 ] || fail "the control chunk holds $CONTROL_VILLAGERS villagers without a placement"

BAD=$(run_cmd "place structure underground_villages:not_a_structure $CX -20 $CZ")
echo "reply: $BAD"
case "$BAD" in
    *"no structure with type"*) ;;
    *) fail "an unknown structure id was accepted: $BAD" ;;
esac
IGLOO=$(run_cmd "place structure minecraft:igloo $CX -20 $CZ")
echo "reply: $IGLOO"
case "$IGLOO" in
    Generated\ structure\ \"minecraft:igloo\"*) ;;
    *) fail "the vanilla igloo control did not place: $IGLOO" ;;
esac
ctl wait 10 > /dev/null
IGLOO_STAIRS=$(ctl find-block minecraft:cut_copper_stairs 48 | count_block minecraft:cut_copper_stairs)
echo "after placing a vanilla igloo: $IGLOO_STAIRS cut copper stairs (still none: that is not our village)"
[ "$IGLOO_STAIRS" = 0 ] || fail "the vanilla igloo produced $IGLOO_STAIRS cut copper stairs"

say "log: no underground_villages worldgen warning (missing template, unknown pool, refused structure)"
ctl logs --lines 8000 > "$SCRATCH/game.log" 2>/dev/null || true
if grep -iE "underground_villages.*(missing|unknown|refus|failed|unsupported)" "$SCRATCH/game.log" | grep -vi "no sounds"; then
    fail "the log reports a worldgen problem for underground_villages"
fi
echo "the log has no underground_villages worldgen problem"

# ----------------------------------------------------------------- SELFTEST
if [ "$SELFTEST" = 1 ]; then
    say "SELFTEST: a deliberately false assertion must fail the run"
    teleport_to "$((PX + 8)).5" -20 "$((PZ + 8)).5"
    settle 600
    got=$(ctl find-block minecraft:cut_copper_stairs 48 | count_block minecraft:cut_copper_stairs)
    echo "the placed village has $got cut copper stairs; this run asserts 0"
    [ "$got" = 0 ] || fail "SELFTEST run: the false assertion (0 cut copper stairs) failed the run, as required"
    echo "SELFTEST run did not fail: the assertion is vacuous" >&2
    exit 2
fi

echo "PASS: $STRUCTURE locates from its carried structure set; /place structure puts the"
echo "village's cut copper stairs, cyan terracotta and black stained glass panes in an"
echo "empty chunk 512 blocks away with its villagers as entities; a chunk with no"
echo "placement holds neither, an unknown id is refused, a vanilla igloo places, and"
echo "the log has no underground_villages worldgen warning"
exit 0
