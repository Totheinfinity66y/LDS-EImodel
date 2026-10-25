param(
    [switch]$Test,
    [string]$PythonPath = 'C:\Users\Totheinfinity\.conda\envs\analysis\python.exe',
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'artifacts\v1')
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw "Missing Python: $PythonPath" }
$taskEnv = Split-Path -Parent (Resolve-Path -LiteralPath $PythonPath).Path
$oldPath = $env:PATH
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $env:PATH = "$taskEnv;$taskEnv\Library\bin;$taskEnv\Scripts;$oldPath"
    if ($Test) { & $PythonPath -m unittest discover -s handcrafted_ei/tests -v }
    else { & $PythonPath -m handcrafted_ei.evaluate --output $OutputDirectory }
    $runExit = $LASTEXITCODE
} finally {
    $env:PATH = $oldPath
    Pop-Location
}
exit $runExit
