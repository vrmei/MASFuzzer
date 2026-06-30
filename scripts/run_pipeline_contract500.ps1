$ErrorActionPreference = "Stop"

$models = @(
  @{
    label = "low_llama31_8b";
    worker = "meta-llama/llama-3.1-8b-instruct"
  },
  @{
    label = "mid_llama31_70b";
    worker = "meta-llama/llama-3.1-70b-instruct"
  },
  @{
    label = "high_deepseek_v3";
    worker = "deepseek/deepseek-chat"
  }
)

$maxWorkers = if ($env:PIPELINE_CONTRACT_MAX_WORKERS) { [int]$env:PIPELINE_CONTRACT_MAX_WORKERS } else { 12 }
$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$status = "logs\pipeline_contract500.status.txt"
"PIPELINE_CONTRACT500 started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') max_workers=$maxWorkers" | Tee-Object -FilePath $status

foreach ($model in $models) {
  $env:D5_WORKER_MODEL = $model.worker
  $env:D5_TRACE = "1"
  $env:D5_TRACE_FILE = "logs\llm_traces\pipeline_contract500_$($runStamp)_$($model.label).jsonl"

  $out = "logs\pipeline_contract500_$($model.label).json"
  $console = "logs\pipeline_contract500_$($model.label).console.log"
  $cmd = @(
    "src\run_pipeline_contract_experiment.py",
    "--backend", "openrouter",
    "--rigor", "strict",
    "--n-payloads", "500",
    "--sample", "stratified",
    "--sample-seed", "42",
    "--max-workers", "$maxWorkers",
    "--out", $out
  )

  "START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') label=$($model.label) worker=$($model.worker) out=$out trace=$env:D5_TRACE_FILE" |
    Tee-Object -FilePath $status -Append

  python @cmd *>&1 | Tee-Object -FilePath $console
  $code = $LASTEXITCODE

  "END   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') label=$($model.label) exit=$code out=$out" |
    Tee-Object -FilePath $status -Append

  if ($code -ne 0) {
    throw "pipeline_contract500 failed for $($model.label) with exit code $code"
  }
}

"PIPELINE_CONTRACT500 finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Tee-Object -FilePath $status -Append
