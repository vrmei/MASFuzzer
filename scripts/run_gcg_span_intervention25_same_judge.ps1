$ErrorActionPreference = "Stop"

$maxWorkers = if ($env:GCG_SPAN_INTERVENTION_MAX_WORKERS) {
  [int]$env:GCG_SPAN_INTERVENTION_MAX_WORKERS
} else {
  8
}

$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$status = "logs\gcg_span_intervention25_same_judge.status.txt"
$env:D5_JUDGE_MODEL = "openai/gpt-4o-mini"
$env:D5_TRACE = "1"
$env:D5_TRACE_FILE = "logs\llm_traces\gcg_span_intervention25_same_judge_$runStamp.jsonl"

$out = "logs\gcg_span_intervention25_same_judge.json"
$console = "logs\gcg_span_intervention25_same_judge.console.log"

"GCG_SPAN_INTERVENTION25_SAME_JUDGE started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') judge=$env:D5_JUDGE_MODEL max_workers=$maxWorkers out=$out trace=$env:D5_TRACE_FILE" |
  Tee-Object -FilePath $status

$cmd = @(
  "src\run_gcg_span_intervention.py",
  "--backend", "openrouter",
  "--rigor", "strict",
  "--payload-limit", "25",
  "--topologies", "supervisor", "swarm", "pipeline", "groupchat",
  "--controls", "matched", "no_token", "human", "random", "cross",
  "--max-workers", "$maxWorkers",
  "--out", $out
)

python @cmd *>&1 | Tee-Object -FilePath $console
$code = $LASTEXITCODE

"GCG_SPAN_INTERVENTION25_SAME_JUDGE finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') exit=$code out=$out" |
  Tee-Object -FilePath $status -Append

if ($code -ne 0) {
  throw "gcg span intervention25 failed with exit code $code"
}
