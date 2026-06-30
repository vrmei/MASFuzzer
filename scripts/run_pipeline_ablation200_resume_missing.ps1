$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$env:PYTHONUTF8 = "1"

$jobs = @(
  @{
    variant = "visibility";
    label = "high_deepseek_v3";
    model = "deepseek/deepseek-chat";
    decider_context = "audit_plan_payload";
    planner_object_mode = "action_plan"
  },
  @{
    variant = "refusal_only";
    label = "low_llama31_8b";
    model = "meta-llama/llama-3.1-8b-instruct";
    decider_context = "plan_only";
    planner_object_mode = "refusal_only"
  },
  @{
    variant = "refusal_only";
    label = "mid_llama31_70b";
    model = "meta-llama/llama-3.1-70b-instruct";
    decider_context = "plan_only";
    planner_object_mode = "refusal_only"
  },
  @{
    variant = "refusal_only";
    label = "high_deepseek_v3";
    model = "deepseek/deepseek-chat";
    decider_context = "plan_only";
    planner_object_mode = "refusal_only"
  }
)

$maxWorkers = if ($env:PIPELINE_ABLATION200_MAX_WORKERS) { [int]$env:PIPELINE_ABLATION200_MAX_WORKERS } else { 12 }
$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$status = "logs\pipeline_ablation200_resume.status.txt"
New-Item -ItemType Directory -Force -Path "logs\llm_traces" | Out-Null
"PIPELINE_ABLATION200_RESUME started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') max_workers=$maxWorkers" |
  Tee-Object -FilePath $status

foreach ($job in $jobs) {
  $env:D5_WORKER_MODEL = $job.model
  $out = "logs\pipeline_ablation200_$($job.variant)_$($job.label).json"
  $console = "logs\pipeline_ablation200_$($job.variant)_$($job.label).resume.console.log"
  $trace = "logs\llm_traces\pipeline_ablation200_resume_$($runStamp)_$($job.variant)_$($job.label).jsonl"
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
    "--decider-context", $job.decider_context,
    "--planner-object-mode", $job.planner_object_mode,
    "--out", $out
  )

  "START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') variant=$($job.variant) label=$($job.label) worker=$($job.model) out=$out trace=$trace" |
    Tee-Object -FilePath $status -Append

  python @cmd *>&1 | Tee-Object -FilePath $console
  $code = $LASTEXITCODE

  "END   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') variant=$($job.variant) label=$($job.label) exit=$code out=$out" |
    Tee-Object -FilePath $status -Append

  if ($code -ne 0) {
    throw "pipeline_ablation200 resume failed for $($job.variant)/$($job.label) with exit code $code"
  }
}

"PIPELINE_ABLATION200_RESUME finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Tee-Object -FilePath $status -Append
