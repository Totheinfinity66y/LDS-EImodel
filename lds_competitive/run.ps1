param(
    [switch]$Test,
    [string]$PythonPath = 'C:\Users\Totheinfinity\.conda\envs\analysis\python.exe',
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'artifacts')
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw "Missing interpreter: $PythonPath" }
$pythonRoot = Split-Path -Parent (Resolve-Path -LiteralPath $PythonPath).Path
$previousPath = $env:PATH
$runExit = 1
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $env:PATH = "$pythonRoot;$pythonRoot\Library\bin;$pythonRoot\Scripts;$previousPath"
    if ($Test) { & $PythonPath -m unittest discover -s lds_competitive/tests -v }
    else { & $PythonPath -m lds_competitive --output $OutputDirectory }
    $runExit = $LASTEXITCODE
} finally {
    $env:PATH = $previousPath
    Pop-Location
}
exit $runExit
