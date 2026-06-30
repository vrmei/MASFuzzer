$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$env:PYTHONUTF8 = "1"

$runs = @(
  @{ label = "low_llama31_8b"; model = "meta-llama/llama-3.1-8b-instruct" },
  @{ label = "mid_llama31_70b"; model = "meta-llama/llama-3.1-70b-instruct" },
  @{ label = "high_deepseek_v3"; model = "deepseek/deepseek-chat" }
)

$topologies = @(
  @{ name = "groupchat"; script = "src\run_groupchat_intervention.py" },
  @{ name = "pipeline"; script = "src\run_pipeline_intervention.py" },
  @{ name = "swarm"; script = "src\run_swarm_intervention.py" }
)

$summary = @()
$started = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$runStamp = Get-Date -Format "yyyyMMdd_HHmmss"
New-Item -ItemType Directory -Force -Path "logs\llm_traces" | Out-Null
"FORMAL25 sweep started $started" | Tee-Object -FilePath "logs\formal25_sweep.status.txt"

foreach ($run in $runs) {
  $env:D5_WORKER_MODEL = $run.model
  foreach ($topology in $topologies) {
    $out = "logs\formal25_$($run.label)_$($topology.name).json"
    $console = "logs\formal25_$($run.label)_$($topology.name).console.log"
    $trace = "logs\llm_traces\formal25_$($runStamp)_$($run.label)_$($topology.name).jsonl"
    $env:D5_TRACE = "1"
    $env:D5_TRACE_FILE = $trace
    $cmd = @(
      $topology.script,
      "--backend", "openrouter",
      "--n-payloads", "25",
      "--sample", "stratified",
      "--sample-seed", "42",
      "--max-workers", "4",
      "--rigor", "strict",
      "--decider-model", "deepseek/deepseek-chat",
      "--out", $out
    )

    $line = "START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') label=$($run.label) topology=$($topology.name) worker=$($run.model) out=$out trace=$trace"
    $line | Tee-Object -FilePath "logs\formal25_sweep.status.txt" -Append
    python @cmd *>&1 | Tee-Object -FilePath $console
    $code = $LASTEXITCODE
    $line = "END   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') label=$($run.label) topology=$($topology.name) exit=$code out=$out"
    $line | Tee-Object -FilePath "logs\formal25_sweep.status.txt" -Append
    $summary += [pscustomobject]@{
      label = $run.label
      worker = $run.model
      topology = $topology.name
      exit_code = $code
      out = $out
      console = $console
      trace = $trace
    }
    if ($code -ne 0) {
      $summary | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 "logs\formal25_sweep.summary.json"
      exit $code
    }
  }
}

$summary | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 "logs\formal25_sweep.summary.json"
"FORMAL25 sweep finished $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Tee-Object -FilePath "logs\formal25_sweep.status.txt" -Append
