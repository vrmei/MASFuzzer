$ErrorActionPreference = "Stop"

$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$status = "logs\swarm_sop_audit100.status.txt"
$out = "logs\swarm_sop_audit100.json"
$console = "logs\swarm_sop_audit100.console.log"

$env:D5_TRACE = "1"
$env:D5_TRACE_FILE = "logs\llm_traces\swarm_sop_audit100_$runStamp.jsonl"

$maxWorkers = if ($env:SWARM_SOP_AUDIT_MAX_WORKERS) {
  [int]$env:SWARM_SOP_AUDIT_MAX_WORKERS
} else {
  4
}

"SWARM_SOP_AUDIT100 started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') max_workers=$maxWorkers out=$out trace=$env:D5_TRACE_FILE" |
  Tee-Object -FilePath $status

$cmd = @(
  "src\run_swarm_sop_audit.py",
  "--backend", "openrouter",
  "--n-payloads", "100",
  "--sample", "stratified",
  "--sample-seed", "42",
  "--rigor", "strict",
  "--decider-model", "deepseek/deepseek-chat",
  "--max-workers", "$maxWorkers",
  "--out", $out
)

python @cmd *>&1 | Tee-Object -FilePath $console
$code = $LASTEXITCODE

"SWARM_SOP_AUDIT100 finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') exit=$code out=$out" |
  Tee-Object -FilePath $status -Append

if ($code -ne 0) {
  throw "swarm_sop_audit100 failed with exit code $code"
}
