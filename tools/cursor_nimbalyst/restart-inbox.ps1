param(
    [Parameter(Mandatory=$true)][string]$ManifestFile,
    [Parameter(Mandatory=$true)][switch]$RestartApproved
)
$ErrorActionPreference = 'Stop'
function Get-TaskSha256([string]$FilePath) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($algorithm.ComputeHash([IO.File]::ReadAllBytes($FilePath)))).Replace('-','').ToLowerInvariant() }
    finally { $algorithm.Dispose() }
}
# Launch only after the user approves stopping active Nimbalyst sessions.
if (-not $RestartApproved) { throw 'Explicit restart approval is required.' }
$taskManifest = Get-Content -LiteralPath $ManifestFile -Raw | ConvertFrom-Json
$appExecutable = Join-Path $env:LOCALAPPDATA 'Programs\Nimbalyst\Nimbalyst.exe'
$expectedArchive = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\Nimbalyst\resources\app.asar'))
if ([IO.Path]::GetFullPath($taskManifest.target) -ne $expectedArchive) { throw 'Unexpected application target.' }
if ((Get-TaskSha256 $expectedArchive) -ne $taskManifest.beforeSha256) { throw 'Application changed after staging.' }
if ((Get-TaskSha256 $taskManifest.stagedArchive) -ne $taskManifest.afterSha256) { throw 'Staged archive changed.' }
$nodeExecutable = 'C:\Program Files\nodejs\node.exe'
$applyScript = Join-Path $PSScriptRoot 'stage-inbox.cjs'
$targets = Get-Process -Name Nimbalyst -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $appExecutable }
if (-not $targets) { throw 'Cannot identify the installed Nimbalyst processes; refusing to stop unrelated processes.' }
$targets | Select-Object Id,StartTime,Path | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskManifest.backupDir 'restart-targets.json')
Start-Sleep -Seconds 3
foreach ($targetProcess in $targets) {
    $currentProcess = Get-Process -Id $targetProcess.Id -ErrorAction SilentlyContinue
    if ($currentProcess -and $currentProcess.Path -eq $appExecutable -and $currentProcess.StartTime -eq $targetProcess.StartTime) { Stop-Process -Id $targetProcess.Id -ErrorAction SilentlyContinue }
}
Start-Sleep -Seconds 3
try {
    & $nodeExecutable $applyScript --apply $ManifestFile *> (Join-Path $taskManifest.backupDir 'apply.log')
    if ($LASTEXITCODE -ne 0) { throw 'Inbox repair failed; inspect apply.log.' }
} finally {
    Start-Process -FilePath $appExecutable -WindowStyle Hidden
}
Get-Date -Format o | Set-Content -LiteralPath (Join-Path $taskManifest.backupDir 'restart-launched.txt')
