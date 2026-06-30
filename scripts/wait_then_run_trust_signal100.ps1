$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$status = "logs\trust_signal100_autostart.status.txt"
$contractPidFile = "logs\pipeline_contract25.pid"
$trustPidFile = "logs\trust_signal100.pid"

New-Item -ItemType Directory -Force -Path "logs" | Out-Null
"TRUST_SIGNAL100_AUTOSTART started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" |
  Tee-Object -FilePath $status

if (Test-Path $contractPidFile) {
  $contractPidText = (Get-Content $contractPidFile -Raw).Trim()
  if ($contractPidText -match '^\d+$') {
    "WAIT  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') pipeline_contract25 pid=$contractPidText" |
      Tee-Object -FilePath $status -Append
    while (Get-Process -Id ([int]$contractPidText) -ErrorAction SilentlyContinue) {
      Start-Sleep -Seconds 30
    }
    "DONE  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') pipeline_contract25 pid=$contractPidText exited" |
      Tee-Object -FilePath $status -Append
  }
} else {
  "WARN  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') no pipeline_contract25 pid file found; starting trust_signal100 immediately" |
    Tee-Object -FilePath $status -Append
}

if (Test-Path $trustPidFile) {
  $trustPidText = (Get-Content $trustPidFile -Raw).Trim()
  if ($trustPidText -match '^\d+$') {
    $existing = Get-Process -Id ([int]$trustPidText) -ErrorAction SilentlyContinue
    if ($existing -and $existing.ProcessName -eq "powershell") {
      "SKIP  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') trust_signal100 already running pid=$trustPidText" |
        Tee-Object -FilePath $status -Append
      exit 0
    }
  }
}

"START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') trust_signal100" |
  Tee-Object -FilePath $status -Append

$p = Start-Process -FilePath "powershell" `
  -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts\run_trust_signal100.ps1") `
  -WorkingDirectory $root `
  -WindowStyle Hidden `
  -PassThru

$p.Id | Set-Content -Encoding ASCII $trustPidFile
"PID   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') trust_signal100 pid=$($p.Id)" |
  Tee-Object -FilePath $status -Append

exit 0
