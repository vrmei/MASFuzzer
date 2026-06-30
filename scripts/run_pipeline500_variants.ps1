$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$env:PYTHONUTF8 = "1"

$runs = @(
  @{ label = "low_llama31_8b"; model = "meta-llama/llama-3.1-8b-instruct" },
  @{ label = "mid_llama31_70b"; model = "meta-llama/llama-3.1-70b-instruct" },
  @{ label = "high_deepseek_v3"; model = "deepseek/deepseek-chat" }
)

$variants = @(
  @{
    label = "baseline";
    decider_context = "plan_only";
    planner_object_mode = "action_plan"
  },
  @{
    label = "visibility";
    decider_context = "audit_plan_payload";
    planner_object_mode = "action_plan"
  },
  @{
    label = "refusal_only";
    decider_context = "plan_only";
    planner_object_mode = "refusal_only"
  }
)

$maxWorkers = if ($env:PIPELINE500_MAX_WORKERS) { [int]$env:PIPELINE500_MAX_WORKERS } else { 12 }
$summary = @()
$started = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType Directory -Force -Path "logs\llm_traces" | Out-Null
"PIPELINE500 started $started max_workers=$maxWorkers" | Tee-Object -FilePath "logs\pipeline500.status.txt"

foreach ($variant in $variants) {
  foreach ($run in $runs) {
    $env:D5_WORKER_MODEL = $run.model
    $out = "logs\pipeline500_$($variant.label)_$($run.label).json"
    $console = "logs\pipeline500_$($variant.label)_$($run.label).console.log"
    $trace = "logs\llm_traces\pipeline500_$($runStamp)_$($variant.label)_$($run.label).jsonl"
    $env:D5_TRACE = "1"
    $env:D5_TRACE_FILE = $trace

    $cmd = @(
      "src\run_pipeline_intervention.py",
      "--backend", "openrouter",
      "--n-payloads", "500",
      "--sample", "stratified",
      "--sample-seed", "42",
      "--max-workers", "$maxWorkers",
      "--rigor", "strict",
      "--decider-model", "deepseek/deepseek-chat",
      "--decider-context", $variant.decider_context,
      "--planner-object-mode", $variant.planner_object_mode,
      "--out", $out
    )

    $line = "START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') variant=$($variant.label) label=$($run.label) worker=$($run.model) out=$out trace=$trace"
    $line | Tee-Object -FilePath "logs\pipeline500.status.txt" -Append
    python @cmd *>&1 | Tee-Object -FilePath $console
    $code = $LASTEXITCODE
    $line = "END   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') variant=$($variant.label) label=$($run.label) exit=$code out=$out"
    $line | Tee-Object -FilePath "logs\pipeline500.status.txt" -Append
    $summary += [pscustomobject]@{
      variant = $variant.label
      worker_label = $run.label
      worker = $run.model
      exit_code = $code
      out = $out
      console = $console
      trace = $trace
      decider_context = $variant.decider_context
      planner_object_mode = $variant.planner_object_mode
      n_payloads = 500
      max_workers = $maxWorkers
    }
    if ($code -ne 0) {
      $summary | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 "logs\pipeline500.summary.json"
      exit $code
    }
  }
}

$summary | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 "logs\pipeline500.summary.json"
"PIPELINE500 finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Tee-Object -FilePath "logs\pipeline500.status.txt" -Append
