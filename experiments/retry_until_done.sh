#!/bin/bash
# Retry loop: keep re-running mega_batch_runner until every instance in the
# queue has a non-empty patch.diff, or the retry cap is hit.
#
# Usage: ./retry_until_done.sh <queue.tsv> [workers=16] [max_rounds=6]

set -u
QUEUE="${1:?queue.tsv required}"
WORKERS="${2:-16}"
MAX_ROUNDS="${3:-6}"
TIMEOUT="${4:-3600}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT=$PROJ/output
LOGS=$PROJ/logs
mkdir -p "$LOGS"

declare -A DSDIR=( [lite]=swebenchlite [verified]=swebenchverified )

cd "$PROJ/experiments"

round=1
while [ $round -le $MAX_ROUNDS ]; do
    # Count how many queue items still lack a valid patch
    missing=0
    while IFS=$'\t' read -r inst mode ds; do
        [ -z "$inst" ] && continue
        dsd=${DSDIR[$ds]:-}
        [ -z "$dsd" ] && continue
        p="$OUTPUT/$dsd/opencode/$mode/$inst/patch.diff"
        if [ ! -s "$p" ]; then
            missing=$((missing+1))
            # also delete the stale dir so the re-run is fresh
            d="$OUTPUT/$dsd/opencode/$mode/$inst"
            [ -d "$d" ] && rm -rf "$d"
        fi
    done < "$QUEUE"

    if [ $missing -eq 0 ]; then
        echo "[retry] ROUND $round — all instances have valid patches. DONE."
        break
    fi

    echo "[retry] ROUND $round — $missing instances still missing a patch; running..."
    log="$LOGS/mega_retry_round${round}.log"
    python -u mega_batch_runner.py "$QUEUE" "$WORKERS" opencode "$TIMEOUT" > "$log" 2>&1
    echo "[retry] ROUND $round finished. log=$log"
    round=$((round+1))
done

# Final summary
final_missing=0
while IFS=$'\t' read -r inst mode ds; do
    [ -z "$inst" ] && continue
    dsd=${DSDIR[$ds]:-}
    p="$OUTPUT/$dsd/opencode/$mode/$inst/patch.diff"
    [ -s "$p" ] || final_missing=$((final_missing+1))
done < "$QUEUE"

total=$(grep -cv '^$\|^#' "$QUEUE")
echo "[retry] FINAL: $((total-final_missing))/$total with valid patch, $final_missing still missing"
