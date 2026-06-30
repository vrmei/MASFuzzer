$ErrorActionPreference = "Stop"

$status = "logs\main_api_resume.status.txt"
"MAIN_API_RESUME started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" |
  Tee-Object -FilePath $status

"START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') swarm_faithful_nolabel100_missing" |
  Tee-Object -FilePath $status -Append
& powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\run_swarm_faithful_nolabel100_missing.ps1"
$swarmCode = $LASTEXITCODE
"END   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') swarm_faithful_nolabel100_missing exit=$swarmCode" |
  Tee-Object -FilePath $status -Append
if ($swarmCode -ne 0) {
  throw "swarm_faithful_nolabel100_missing failed with exit code $swarmCode"
}

"START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') trust_signal100" |
  Tee-Object -FilePath $status -Append
& powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\run_trust_signal100.ps1"
$trustCode = $LASTEXITCODE
"END   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') trust_signal100 exit=$trustCode" |
  Tee-Object -FilePath $status -Append
if ($trustCode -ne 0) {
  throw "trust_signal100 failed with exit code $trustCode"
}

"MAIN_API_RESUME finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" |
  Tee-Object -FilePath $status -Append
