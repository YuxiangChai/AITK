EXP_NAME=qwen25vl_test

echo "Running experiment ${EXP_NAME}"

python scripts/start_avd.py

echo "Waiting for AVD fully loaded"
sleep 60

python scripts/interact.py --experiment-name "${EXP_NAME}"
