#!/usr/bin/env bash
# The 24h PyBot math run on the RunPod pod. Started once, detached; stops the pod at the end.
#
#   nohup bash /opt/pybot/harness/remote/run.sh > /root/run.out 2>&1 &
#
# Everything runs from the container disk (/opt/pybot), where unix permissions hold: hidden test
# data, the champion repo and the logs are root-only, and each agent runs as its own user. The
# network volume (/workspace) does NOT enforce permissions, so it only ever receives results
# (logs, state, a git bundle of the champion), copied by root; never hidden/ or data/.
#
# Round 4 is redone from the post-round-3 checkpoint with the same clusters and batches, then
# the run keeps whichever round 4 scored higher on test (this redo, or the earlier run on the
# laptop, whose champion and score are passed in) and carries on with fresh rounds.
set -u
H=/opt/pybot/harness
OUT=/workspace/pybot-results
cd $H

export AGENT_SANDBOX=unix-user                     # approved: Codex's sandbox cannot run here
export AGENT_USERS=agent                          # one user: Codex's login can't be shared across users
export AGENT_CODEX_HOME=/home/agent/.codex         # one shared Codex login
export EVAL_SLOTS=3                                # 32 vCPU: three evals of 8 workers at once

sync_results() {
  mkdir -p $OUT
  tar -C $H --exclude='orch/checkpoint-after-r03' -cf - orch runs/chat_baseline.jsonl \
      orchestrate.py eval.py check_candidate.py agent_brief.md remote 2>/dev/null \
    | tar -C $OUT -xf - 2>/dev/null
  git -C /opt/pybot/src/pybot bundle create $OUT/champion.bundle --all >/dev/null 2>&1
  date -u '+%F %T' > $OUT/last_sync.txt
}

( while true; do sleep 600; sync_results; done ) &
SYNC=$!

python3 -u orchestrate.py \
  --effort high --agents 6 --no-overlap --parallel-merge --workers 8 \
  --generalize-first --until "2026-11-18 18:30" \
  >> orch/stdout.txt 2>&1
status=$?
echo "$(date -u '+%F %T') orchestrator exited with status $status" >> orch/log.txt

kill $SYNC 2>/dev/null
cp orch/state.json orch/state.final.json
sync_results
if [ -f orch/NO_SELF_STOP ]; then
  echo "$(date -u '+%F %T') NO_SELF_STOP present; leaving the pod running" >> orch/log.txt
  sync_results
  exit 0
fi
KEY=$(tr '\0' '\n' < /proc/1/environ | sed -n 's/^RUNPOD_API_KEY=//p')
POD=$(tr '\0' '\n' < /proc/1/environ | sed -n 's/^RUNPOD_POD_ID=//p')
echo "$(date -u '+%F %T') stopping pod $POD" >> orch/log.txt
sync_results
curl -s -m 30 -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  https://api.runpod.io/graphql \
  -d "{\"query\":\"mutation { podStop(input: {podId: \\\"$POD\\\"}) { id desiredStatus } }\"}" \
  >> $OUT/stop_response.txt 2>&1
