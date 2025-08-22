EXP_NAME=qwen25vl_test

echo "Running experiment ${EXP_NAME}"
echo "Starting AVD..."
python scripts/start_avd.py

echo "Waiting for AVD fully loaded"
sleep 60
echo "Starting interaction..."
python scripts/interact.py --experiment-name "${EXP_NAME}"
