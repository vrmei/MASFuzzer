$ErrorActionPreference = "Stop"

$runs = @(
  @{ arch = "swarm"; arms = "endorse"; label = "swarm_endorse" },
  @{ arch = "swarm"; arms = "certainty"; label = "swarm_certainty" },
  @{ arch = "swarm"; arms = "recipe"; label = "swarm_recipe" },
  @{ arch = "swarm"; arms = "neutral"; label = "swarm_neutral" },
  @{ arch = "swarm"; arms = "concat"; label = "swarm_concat" },
  @{ arch = "pipeline"; arms = "pipeline_launder"; label = "pipeline_launder" },
  @{ arch = "pipeline"; arms = "certainty"; label = "pipeline_certainty" },
  @{ arch = "pipeline"; arms = "recipe"; label = "pipeline_recipe" },
  @{ arch = "pipeline"; arms = "neutral"; label = "pipeline_neutral" },
  @{ arch = "pipeline"; arms = "concat"; label = "pipeline_concat" }
)

$maxValidationAttempts = if ($env:TRUST_SIGNAL_MAX_VALIDATION_ATTEMPTS) {
  [int]$env:TRUST_SIGNAL_MAX_VALIDATION_ATTEMPTS
} else {
  3
}
$maxWorkers = if ($env:TRUST_SIGNAL_MAX_WORKERS) {
  [int]$env:TRUST_SIGNAL_MAX_WORKERS
} else {
  8
}

$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$status = "logs\trust_signal100_same_judge_retry2_split_arms.status.txt"
$env:D5_JUDGE_MODEL = "openai/gpt-4o-mini"
"TRUST_SIGNAL100_SAME_JUDGE_RETRY2_SPLIT_ARMS started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') judge=$env:D5_JUDGE_MODEL validation_attempts=$maxValidationAttempts max_workers=$maxWorkers" |
  Tee-Object -FilePath $status

foreach ($run in $runs) {
  $env:D5_TRACE = "1"
  $env:D5_TRACE_FILE = "logs\llm_traces\trust_signal100_same_judge_retry2_split_arms_$($runStamp)_$($run.label).jsonl"

  $out = "logs\trust_signal100_same_judge_retry2_split_arms_$($run.label).json"
  $console = "logs\trust_signal100_same_judge_retry2_split_arms_$($run.label).console.log"
  $cmd = @(
    "src\run_arch_matrix.py",
    "--arch", $run.arch,
    "--backend", "openrouter",
    "--rigor", "strict",
    "--seeds", "100",
    "--budget", "100",
    "--arms", $run.arms,
    "--max-validation-attempts", "$maxValidationAttempts",
    "--max-workers", "$maxWorkers",
    "--out", $out
  )

  "START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') label=$($run.label) arch=$($run.arch) arms=$($run.arms) judge=$env:D5_JUDGE_MODEL max_workers=$maxWorkers out=$out trace=$env:D5_TRACE_FILE" |
    Tee-Object -FilePath $status -Append

  try {
    python @cmd *>&1 | Tee-Object -FilePath $console
    $code = $LASTEXITCODE
  } catch {
    $code = 1
    "EXCEPTION $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') label=$($run.label) message=$($_.Exception.Message)" |
      Tee-Object -FilePath $status -Append
  }

  "END   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') label=$($run.label) exit=$code out=$out" |
    Tee-Object -FilePath $status -Append
}

"TRUST_SIGNAL100_SAME_JUDGE_RETRY2_SPLIT_ARMS finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" |
  Tee-Object -FilePath $status -Append
