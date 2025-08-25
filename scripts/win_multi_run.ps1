Param(
    [int]$Start = 1,
    [int]$End = 10
)

# Usage examples:
#   .\scripts\win_multi_run.ps1                     # runs for n = 01..10
#   .\scripts\win_multi_run.ps1 -Start 1 -End 5     # runs for n = 01..05
#   .\scripts\win_multi_run.ps1 -Start 3 -End 12    # runs for n = 03..12

for ($i = $Start; $i -le $End; $i++) {
    $idx = "{0:D2}" -f $i
    python scripts/interact.py --experiment-name "qwen25vl_test_$idx"
    Start-Sleep -Seconds 60
}


