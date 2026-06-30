$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$env:PYTHONUTF8 = "1"
$env:D5_WORKER_MODEL = "deepseek/deepseek-chat"
$env:D5_TRACE = "1"

$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType Directory -Force -Path "logs\llm_traces" | Out-Null

$out = "logs\pipeline_ablation25_refusal_only_high_deepseek_v3.rerun.json"
$console = "logs\pipeline_ablation25_refusal_only_high_deepseek_v3.rerun.console.log"
$trace = "logs\llm_traces\pipeline_ablation25_$($runStamp)_refusal_only_high_deepseek_v3_rerun.jsonl"
$env:D5_TRACE_FILE = $trace

"RERUN refusal_only/high_deepseek_v3 started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') out=$out trace=$trace" |
  Tee-Object -FilePath "logs\pipeline_ablation25_refusal_only_high_deepseek_v3.rerun.status.txt"

$cmd = @(
  "src\run_pipeline_intervention.py",
  "--backend", "openrouter",
  "--n-payloads", "25",
  "--sample", "stratified",
  "--sample-seed", "42",
  "--max-workers", "4",
  "--rigor", "strict",
  "--decider-model", "deepseek/deepseek-chat",
  "--decider-context", "plan_only",
  "--planner-object-mode", "refusal_only",
  "--out", $out
)

python @cmd *>&1 | Tee-Object -FilePath $console
$code = $LASTEXITCODE

"RERUN refusal_only/high_deepseek_v3 finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') exit=$code out=$out trace=$trace" |
  Tee-Object -FilePath "logs\pipeline_ablation25_refusal_only_high_deepseek_v3.rerun.status.txt" -Append

exit $code
