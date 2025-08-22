$EXP_NAME="qwen25vl_test"

Write-Host "Running experiment $EXP_NAME"

python scripts/start_avd.py

Write-Host "Waiting for AVD fully loaded."
Start-Sleep -Seconds 60

python scripts/interact.py --experiment-name "$EXP_NAME"