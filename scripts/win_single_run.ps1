$EXP_NAME="qwen25vl_test"

Write-Host "Running experiment $EXP_NAME"
Write-Host "Starting AVD..."
python scripts/start_avd.py

Write-Host "Waiting for AVD fully loaded."
Start-Sleep -Seconds 60
Write-Host "Starting interaction..."
python scripts/interact.py --experiment-name "$EXP_NAME"