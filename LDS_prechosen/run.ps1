param(
    [string]$PythonPath = 'C:\Users\Totheinfinity\.conda\envs\analysis\python.exe',
    [switch]$Test,
    [string]$OutputDirectory = 'LDS_prechosen/artifacts'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $PythonPath)) { throw "Python not found: $PythonPath" }
$taskEnvRoot = Split-Path -Parent $PythonPath
$taskSavedPath = $env:PATH
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $env:PATH = "$taskEnvRoot;$taskEnvRoot\Library\bin;$taskEnvRoot\Scripts;$taskSavedPath"
    if ($Test) { & $PythonPath -m unittest discover -s LDS_prechosen/tests -v }
    else { & $PythonPath -m LDS_prechosen.evaluate --output $OutputDirectory }
    if ($LASTEXITCODE -ne 0) { throw "Model command failed: $LASTEXITCODE" }
} finally {
    $env:PATH = $taskSavedPath
    Pop-Location
}
