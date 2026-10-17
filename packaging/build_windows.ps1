# Build and verify PokerPractice.exe on Windows.
#
# Usage (PowerShell, from anywhere):
#     powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1 [-SkipTests]
#
# Requires Python 3.12+ (the "py" launcher). Produces dist\PokerPractice\PokerPractice.exe
# and runs its built-in self-test twice to confirm that history persists.
param([switch]$SkipTests)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path .venv-win)) { py -3.12 -m venv .venv-win }
$python = ".\.venv-win\Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements-dev.txt -r requirements-build.txt

if (-not $SkipTests) {
    & $python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
}

& $python -m PyInstaller --noconfirm --clean packaging\PokerPractice.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

# Verify the packaged executable with an isolated data directory.
$data = Join-Path $env:TEMP ("PokerPracticeSelfTest-" + [guid]::NewGuid())
$env:POKER_PRACTICE_DATA_DIR = $data
foreach ($run in 1, 2) {
    $process = Start-Process dist\PokerPractice\PokerPractice.exe -ArgumentList "--self-test" -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        Get-Content (Join-Path $data "logs\poker_practice.log") -Tail 40
        throw "Self-test run $run failed"
    }
}
Select-String -Path (Join-Path $data "logs\poker_practice.log") -Pattern "Self-test: " | ForEach-Object { $_.Line }
Remove-Item Env:POKER_PRACTICE_DATA_DIR
Write-Host "Built and verified: dist\PokerPractice\PokerPractice.exe"
