param(
    [switch]$Test,
    [string]$PythonPath = 'C:\Users\Totheinfinity\.conda\envs\analysis\python.exe',
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'artifacts'),
    [int]$ProbeAngles = 72
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw "Python interpreter does not exist: $PythonPath"
}
$pythonRoot = Split-Path -Parent (Resolve-Path -LiteralPath $PythonPath).Path
$previousPath = $env:PATH
$runExit = 1
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    # Conda DLL paths are scoped to this invocation, restored in finally.
    $env:PATH = "$pythonRoot;$pythonRoot\Library\bin;$pythonRoot\Scripts;$previousPath"
    if ($Test) {
        & $PythonPath -m unittest discover -s lds_decompressor/tests -v
    } else {
        & $PythonPath -m lds_decompressor --output $OutputDirectory --probe-angles $ProbeAngles
    }
    $runExit = $LASTEXITCODE
} finally {
    $env:PATH = $previousPath
    Pop-Location
}
exit $runExit
