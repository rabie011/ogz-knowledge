#!/bin/bash
# pre-commit-hook.sh — Data quality gate for ogz-knowledge
# Runs guard_data_quality.py before every commit.
# Install: ln -sf ../../scripts/pre-commit-hook.sh .git/hooks/pre-commit

cd "$(git rev-parse --show-toplevel)" || exit 0

# Skip if only logs/enricher files changed (daemon auto-commits)
CHANGED=$(git diff --cached --name-only | grep -v "^logs/" | grep -v "enricher_state" | head -1)
if [ -z "$CHANGED" ]; then
    exit 0  # only log files — skip heavy check
fi

python3 scripts/guard_data_quality.py --quick 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Data quality check failed. Fix issues before committing."
    echo "   Run: python3 scripts/guard_data_quality.py"
    echo ""
    exit 1
fi
