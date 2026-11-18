#!/usr/bin/env bash
# Set up a RunPod CPU pod to run the PyBot math hill-climb. Run once, as root.
#
# Layout (on the container disk, where unix permissions hold; RunPod network volumes do not
# enforce them, so a volume only ever receives results, see run.sh):
#   /opt/pybot/harness     orchestrator, evals, splits, hidden test data, logs (root only)
#   /opt/pybot/src/pybot   the champion git repo (root only)
#   /opt/pybot/harness/wt  agents' worktrees (owned by the 'agent' user)
#
# Codex agents run as the unprivileged 'agent' user. They can write only their own worktree
# and cannot read hidden/ (test + GSM-Symbolic), data/, orch/ or the champion repo.
# Codex's own sandbox (bubblewrap) cannot start in a RunPod container, so run.sh runs the
# agents without it, relying on these permissions plus the audit in orchestrate.py.
set -euo pipefail

apt-get update -qq
apt-get install -y -qq curl ca-certificates sudo >/dev/null
if ! command -v node >/dev/null || [ "$(node -p 'process.versions.node.split(".")[0]')" -lt 20 ]; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash - >/dev/null
  apt-get install -y -qq nodejs >/dev/null
fi
npm install -g --silent @openai/codex@0.169.0
codex --version

id agent >/dev/null 2>&1 || useradd -m -s /bin/bash agent
git config --global safe.directory '*'      # root commits inside agent-owned worktrees
git config --global user.name pybot-math-orchestrator
git config --global user.email orchestrator@localhost

R=/opt/pybot
mkdir -p $R/src $R/harness/wt
chmod 711 $R $R/src $R/harness           # traverse only
chmod 700 $R/harness/hidden $R/harness/data $R/harness/orch 2>/dev/null || true
chmod 711 $R/harness/runs $R/harness/wt
chmod 644 $R/harness/runs/.eval.lock* 2>/dev/null || true
echo "bootstrap done: node $(node --version), $(codex --version)"
