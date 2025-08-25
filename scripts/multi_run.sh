set -euo pipefail

# Usage:
#   ./scripts/multi_run.sh                # runs for n = 01..10
#   ./scripts/multi_run.sh 1 5           # runs for n = 01..05
#   ./scripts/multi_run.sh 3 12          # runs for n = 03..12

START=${1:-1}
END=${2:-10}

for (( i=START; i<=END; i++ )); do
	idx=$(printf "%02d" "$i")
	python scripts/interact.py --experiment-name "qwen25vl_test_${idx}"
	sleep 60
done


