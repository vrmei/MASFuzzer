$ErrorActionPreference = "Stop"

$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$status = "logs\swarm_faithful_nolabel25.status.txt"
$out = "logs\swarm_faithful_nolabel25.json"
$console = "logs\swarm_faithful_nolabel25.console.log"

$budget = if ($env:SWARM_FAITHFUL_NOLABEL_BUDGET) {
  [int]$env:SWARM_FAITHFUL_NOLABEL_BUDGET
} else {
  40
}

$env:D5_TRACE = "1"
$env:D5_TRACE_FILE = "logs\llm_traces\swarm_faithful_nolabel25_$runStamp.jsonl"

"SWARM_FAITHFUL_NOLABEL25 started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') budget=$budget out=$out trace=$env:D5_TRACE_FILE" |
  Tee-Object -FilePath $status

$cmd = @(
  "src\run_swarm_faithful_fuzz.py",
  "--backend", "openrouter",
  "--n-payloads", "25",
  "--sample", "stratified",
  "--sample-seed", "42",
  "--budget", "$budget",
  "--arms", "swarm_handoff_proceed,swarm_handoff_proceed_nolabel,neutral,recipe",
  "--rigor", "strict",
  "--attacker", "deepseek/deepseek-chat",
  "--decider-model", "deepseek/deepseek-chat",
  "--max-validation-attempts", "5",
  "--out", $out
)

python @cmd *>&1 | Tee-Object -FilePath $console
$code = $LASTEXITCODE

"SWARM_FAITHFUL_NOLABEL25 finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') exit=$code out=$out" |
  Tee-Object -FilePath $status -Append

if ($code -ne 0) {
  throw "swarm_faithful_nolabel25 failed with exit code $code"
}
