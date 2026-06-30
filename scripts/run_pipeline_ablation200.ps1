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

$maxWorkers = if ($env:PIPELINE_ABLATION200_MAX_WORKERS) { [int]$env:PIPELINE_ABLATION200_MAX_WORKERS } else { 12 }
$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$status = "logs\pipeline_ablation200.status.txt"
New-Item -ItemType Directory -Force -Path "logs\llm_traces" | Out-Null
"PIPELINE_ABLATION200 started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') max_workers=$maxWorkers" |
  Tee-Object -FilePath $status

foreach ($variant in $variants) {
  foreach ($run in $runs) {
    if ($variant.label -eq "visibility" -and $run.label -eq "low_llama31_8b") {
      "SKIP  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') variant=visibility label=low_llama31_8b reason=use_existing_pipeline500_visibility_low_slice" |
        Tee-Object -FilePath $status -Append
      continue
    }

    $env:D5_WORKER_MODEL = $run.model
    $out = "logs\pipeline_ablation200_$($variant.label)_$($run.label).json"
    $console = "logs\pipeline_ablation200_$($variant.label)_$($run.label).console.log"
    $trace = "logs\llm_traces\pipeline_ablation200_$($runStamp)_$($variant.label)_$($run.label).jsonl"
    $env:D5_TRACE = "1"
    $env:D5_TRACE_FILE = $trace

    $cmd = @(
      "src\run_pipeline_intervention.py",
      "--backend", "openrouter",
      "--n-payloads", "200",
      "--sample", "stratified",
      "--sample-seed", "42",
      "--max-workers", "$maxWorkers",
      "--rigor", "strict",
      "--decider-model", "deepseek/deepseek-chat",
      "--decider-context", $variant.decider_context,
      "--planner-object-mode", $variant.planner_object_mode,
      "--out", $out
    )

    "START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') variant=$($variant.label) label=$($run.label) worker=$($run.model) out=$out trace=$trace" |
      Tee-Object -FilePath $status -Append

    python @cmd *>&1 | Tee-Object -FilePath $console
    $code = $LASTEXITCODE

    "END   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') variant=$($variant.label) label=$($run.label) exit=$code out=$out" |
      Tee-Object -FilePath $status -Append

    if ($code -ne 0) {
      throw "pipeline_ablation200 failed for $($variant.label)/$($run.label) with exit code $code"
    }
  }
}

"PIPELINE_ABLATION200 finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Tee-Object -FilePath $status -Append
