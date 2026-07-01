$ErrorActionPreference = "Stop"

$runs = @(
  @{
    arch = "supervisor";
    arms = "neutral,concat";
    label = "supervisor_certainty_retry_neutral_concat"
  },
  @{
    arch = "groupchat";
    arms = "groupvote,certainty,recipe,neutral,concat";
    label = "groupchat_vote"
  },
  @{
    arch = "swarm";
    arms = "specialist,endorse,certainty,recipe,neutral,concat";
    label = "swarm_specialist"
  },
  @{
    arch = "pipeline";
    arms = "pipeline_launder,certainty,recipe,neutral,concat";
    label = "pipeline_guarded_launder"
  }
)

$maxValidationAttempts = if ($env:TRUST_SIGNAL_MAX_VALIDATION_ATTEMPTS) {
  [int]$env:TRUST_SIGNAL_MAX_VALIDATION_ATTEMPTS
} else {
  3
}

$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$status = "logs\trust_signal100_retry_same_judge.status.txt"
$env:D5_JUDGE_MODEL = "openai/gpt-4o-mini"
"TRUST_SIGNAL100_RETRY_SAME_JUDGE started $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') judge=$env:D5_JUDGE_MODEL validation_attempts=$maxValidationAttempts" |
  Tee-Object -FilePath $status

foreach ($run in $runs) {
  $env:D5_TRACE = "1"
  $env:D5_TRACE_FILE = "logs\llm_traces\trust_signal100_retry_same_judge_$($runStamp)_$($run.label).jsonl"

  $out = "logs\trust_signal100_retry_same_judge_$($run.label).json"
  $console = "logs\trust_signal100_retry_same_judge_$($run.label).console.log"
  $cmd = @(
    "src\run_arch_matrix.py",
    "--arch", $run.arch,
    "--backend", "openrouter",
    "--rigor", "strict",
    "--seeds", "100",
    "--budget", "100",
    "--arms", $run.arms,
    "--max-validation-attempts", "$maxValidationAttempts",
    "--out", $out
  )

  "START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') label=$($run.label) arch=$($run.arch) arms=$($run.arms) judge=$env:D5_JUDGE_MODEL out=$out trace=$env:D5_TRACE_FILE" |
    Tee-Object -FilePath $status -Append

  python @cmd *>&1 | Tee-Object -FilePath $console
  $code = $LASTEXITCODE

  "END   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') label=$($run.label) exit=$code out=$out" |
    Tee-Object -FilePath $status -Append

  if ($code -ne 0) {
    throw "trust_signal100 retry failed for $($run.label) with exit code $code"
  }
}

"TRUST_SIGNAL100_RETRY_SAME_JUDGE finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" |
  Tee-Object -FilePath $status -Append
